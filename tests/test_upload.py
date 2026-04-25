import http.client
import importlib.util
import threading
from pathlib import Path
from uuid import uuid4


REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = REPO_ROOT / "main.py"


def load_main_module():
    spec = importlib.util.spec_from_file_location(f"gxde_sendbylan_main_{uuid4().hex}", MAIN_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


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


def run_server(module, share_dir):
    module.shareDir = str(share_dir)
    server = module.HTTPServer(("127.0.0.1", 0), module.SimpleHTTPRequestHandlerWithUpload)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def post_files(server, files):
    boundary, body = encode_multipart(files)
    conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
    conn.request(
        "POST",
        "/",
        body=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
        },
    )
    return conn.getresponse()


def test_upload_saves_single_file(tmp_path):
    module = load_main_module()
    server, thread = run_server(module, tmp_path)

    try:
        response = post_files(server, [("file", "hello.txt", b"hello from upload")])
        body = response.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert response.status == 200
    assert (tmp_path / "hello.txt").read_bytes() == b"hello from upload"
    assert "Upload Success" in body


def test_upload_preserves_subdirectories(tmp_path):
    module = load_main_module()
    server, thread = run_server(module, tmp_path)

    try:
        response = post_files(server, [("file", "nested/demo.txt", b"nested upload")])
        response.read()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert response.status == 200
    assert (tmp_path / "nested" / "demo.txt").read_bytes() == b"nested upload"
