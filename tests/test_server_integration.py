"""验证 sendbylan 与 server.py 之间的约定。

C++ 前端会把共享目录、端口、协议等拼成 server.py 的命令行，
这些测试直接以同样的参数启动 server.py，确认网页浏览、网页上传、
WebDAV 挂载与自定义错误页都能正常工作。
"""
import http.client
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = REPO_ROOT / "server.py"
ERROR_PAGES = REPO_ROOT / "error"


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def encode_multipart(parts, boundary="----GXDESendByLanBoundary"):
    body = bytearray()
    for field_name, filename, content in parts:
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode("utf-8")
        )
        body.extend(b"Content-Type: application/octet-stream\r\n\r\n")
        body.extend(content)
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    return boundary, bytes(body)


class ServerProcess:
    """按 C++ 前端生成的方式启动 server.py。"""

    def __init__(self, share_dir, extra_args=(), protocol="webdav", upload=True):
        self.port = free_port()
        self.share_dir = str(share_dir)
        command = [
            sys.executable,
            str(SERVER_PATH),
            str(self.port),
            "-d", self.share_dir,
            "-p", protocol,
            "--brand", "GXDE Sendbylan",
            "--error-pages", str(ERROR_PAGES),
        ]
        if upload and protocol != "smb":
            command.append("--upload")
        command.extend(extra_args)
        self.command = command
        self.process = None

    def __enter__(self):
        self.process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        deadline = time.time() + 15
        while time.time() < deadline:
            if self.process.poll() is not None:
                raise AssertionError(f"server.py 提前退出: {self.process.stdout.read()}")
            try:
                with socket.create_connection(("127.0.0.1", self.port), timeout=0.5):
                    return self
            except OSError:
                time.sleep(0.1)
        raise AssertionError("等待 server.py 监听超时")

    def __exit__(self, *exc_info):
        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=15)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, response.read()
        finally:
            connection.close()


def test_upload_saves_single_file(tmp_path):
    with ServerProcess(tmp_path) as running:
        boundary, body = encode_multipart([("files", "hello.txt", b"hello from upload")])
        status, _ = running.request(
            "POST",
            "/",
            body=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(body)),
            },
        )

    assert status == 303
    assert (tmp_path / "hello.txt").read_bytes() == b"hello from upload"


def test_upload_preserves_subdirectories(tmp_path):
    with ServerProcess(tmp_path) as running:
        boundary, body = encode_multipart([("files", "nested/demo.txt", b"nested upload")])
        status, _ = running.request(
            "POST",
            "/",
            body=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(body)),
            },
        )

    assert status == 303
    assert (tmp_path / "nested" / "demo.txt").read_bytes() == b"nested upload"


def test_directory_listing_shows_brand_and_upload_form(tmp_path):
    (tmp_path / "note.txt").write_text("hello", encoding="utf-8")

    with ServerProcess(tmp_path) as running:
        status, body = running.request("GET", "/")

    assert status == 200
    page = body.decode("utf-8")
    assert "GXDE Sendbylan" in page
    assert "note.txt" in page
    assert "upload-form" in page
    # 先选择、点“开始上传”才真正上传
    assert "upload-start-btn" in page
    assert 'onchange="updateSelectionHint()"' in page


def test_upload_can_be_disabled(tmp_path):
    with ServerProcess(tmp_path, upload=False) as running:
        status, body = running.request("GET", "/")
        page = body.decode("utf-8")
        assert status == 200
        assert "upload-form" not in page


def test_custom_404_page_is_used(tmp_path):
    with ServerProcess(tmp_path) as running:
        status, body = running.request("GET", "/not-here.txt")

    assert status == 404
    assert body == (ERROR_PAGES / "404.html").read_bytes()


def test_webdav_is_available_in_default_protocol(tmp_path):
    (tmp_path / "webdav.txt").write_bytes(b"webdav payload")

    with ServerProcess(tmp_path) as running:
        status, body = running.request("PROPFIND", "/", headers={"Depth": "1"})
        assert status == 207
        assert b"webdav.txt" in body

        status, body = running.request("PUT", "/uploaded.txt", body=b"put payload")
        assert status == 201
        assert (tmp_path / "uploaded.txt").read_bytes() == b"put payload"

        status, _ = running.request("MKCOL", "/davdir")
        assert status == 201
        assert (tmp_path / "davdir").is_dir()


def test_http_protocol_has_no_webdav_methods(tmp_path):
    with ServerProcess(tmp_path, protocol="http") as running:
        status, _ = running.request("PROPFIND", "/", headers={"Depth": "1"})

    assert status == 501


@pytest.mark.skipif(shutil.which("smbclient") is None, reason="需要 smbclient 才能验证 SMB 共享")
def test_smb_share_from_command_line(tmp_path):
    pytest.importorskip("impacket")

    (tmp_path / "hello.txt").write_text("hello smb", encoding="utf-8")
    port = free_port()

    process = subprocess.Popen(
        [
            sys.executable, str(SERVER_PATH), str(port),
            "-d", str(tmp_path), "-p", "smb",
            "--smb-share", "sendbylan", "--auth", "user:pass",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        result = None
        for _ in range(50):
            if process.poll() is not None:
                raise AssertionError(f"server.py 提前退出: {process.stdout.read()}")
            result = subprocess.run(
                [
                    "smbclient", "//127.0.0.1/sendbylan", "-p", str(port),
                    "-U", "user%pass", "-c", "ls",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                break
            time.sleep(0.2)

        assert result is not None and result.returncode == 0, result.stderr if result else "no result"
        assert "hello.txt" in result.stdout
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def test_server_py_is_shipped_with_sendbylan():
    assert SERVER_PATH.is_file()
    assert os.access(SERVER_PATH, os.X_OK), "server.py 需要可执行权限（CMake 以 PROGRAMS 安装）"
