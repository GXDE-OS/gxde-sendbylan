#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

import platform
import sys
import urllib.request
import urllib.parse
import os
import time
import re
import mimetypes
import html
import threading
import socket
from email.parser import BytesParser
from email.policy import default
from http.server import SimpleHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from io import BytesIO
import argparse
import re

__version__ = "1.7.8"
import fcntl
import struct

programPath = os.path.split(os.path.realpath(__file__))[0]  # 返回 string

def get_interface_ip(ifname, family):
    """Retrieve the IP address associated with a network interface."""
    s = socket.socket(family, socket.SOCK_DGRAM)
    try:
        if family == socket.AF_INET:  # IPv4
            return socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR for IPv4
                struct.pack('256s', bytes(ifname[:15], 'utf-8'))
            )[20:24])
        elif family == socket.AF_INET6:  # IPv6
            return socket.inet_ntop(
                socket.AF_INET6,
                fcntl.ioctl(
                    s.fileno(),
                    0x8915,  # SIOCGIFADDR for IPv6 might need to be different
                    struct.pack('256s', bytes(ifname[:15], 'utf-8'))
                )[20:36]
            )
    except IOError:
        return None

def list_all_ips():
    """List all IP addresses for all network interfaces (IPv4 and IPv6)."""
    addresses = []
    interfaces = socket.if_nameindex()

    for interface in interfaces:
        # Get IPv4 address for the interface
        ipv4 = get_interface_ip(interface[1], socket.AF_INET)
        if ipv4 and ipv4 != '127.0.0.1':
            addresses.append((interface[1], ipv4, 'IPv4'))

        # Get IPv6 address for the interface
        ipv6 = get_interface_ip(interface[1], socket.AF_INET6)
        if ipv6 and not ipv6.startswith('fe80'):  # Filter out link-local addresses
            addresses.append((interface[1], ipv6, 'IPv6'))

    return addresses
def showTips(port):
    print("")
    print('----------------------------------------------------------------------->> ')
    print(f'-------->> Now, listening at port {port}...')
    osType = platform.system()

    # List all IP addresses
    print('-------->> Available IP addresses:')
    for interface, ip, version in list_all_ips():
        print(f"-------->> {interface} ({version}): http://{ip}:{port}")
    
    print('----------------------------------------------------------------------->> ')
    print("")

def sizeof_fmt(num):
    for x in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


def parse_uploaded_files(content_type, body):
    message = BytesParser(policy=default).parsebytes(
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8") + body
    )
    if not message.is_multipart():
        return []

    files = []
    for part in message.iter_parts():
        if part.get_content_disposition() != "form-data":
            continue
        if part.get_param("name", header="Content-Disposition") != "file":
            continue
        filename = part.get_filename()
        if not filename:
            continue
        files.append((filename, part.get_payload(decode=True) or b""))
    return files


def sanitize_upload_name(filename):
    normalized = os.path.normpath(filename.replace("\\", "/")).lstrip("/")
    if normalized in ("", "."):
        return None
    if normalized == ".." or normalized.startswith("../"):
        return None
    return normalized



class SimpleHTTPRequestHandlerWithUpload(SimpleHTTPRequestHandler):
    server_version = "SimpleHTTPWithUpload/" + __version__
    def send_head(self):
        """Override the default method to handle Range requests."""
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return self.list_directory(path)
        
        try:
            file = open(path, 'rb')
        except OSError:
            return self.error_page(404, "File not found.")

        file_size = os.path.getsize(path)
        range_header = self.headers.get('Range')

        if range_header:
            # Parsing the Range header, e.g., bytes=500-999
            range_match = re.match(r"bytes=(\d+)-(\d*)", range_header)
            if range_match:
                start = int(range_match.group(1))
                end = range_match.group(2)
                end = int(end) if end else file_size - 1

                if start >= file_size:
                    self.send_error(416, "Requested Range Not Satisfiable")
                    self.send_header("Content-Range", f"bytes */{file_size}")
                    self.end_headers()
                    return None

                self.send_response(206)
                self.send_header("Content-Type", self.guess_type(path))
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(end - start + 1))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()

                # Serve the requested file range
                file.seek(start)
                self.wfile.write(file.read(end - start + 1))
                file.close()
                return None

        # Default response when no Range request is made (serve the full file)
        self.send_response(200)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()

        return file

    def translate_path(self, path):
        """Override to serve from the custom directory."""
        path = urllib.parse.unquote(path)
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        trailing_slash = path.rstrip().endswith('/')
        path = os.path.normpath(path)

        full_path = os.path.join(shareDir, path.lstrip('/'))
        if os.path.isdir(full_path) and trailing_slash:
            return full_path + '/'
        return full_path

    def error_page(self, code: int, defaultText: str):
        if (not os.path.exists(f"{programPath}/error/{str(code)}.html")):
            self.send_error(code, defaultText)
            return None
        f = BytesIO()
        with open(f"{programPath}/error/{str(code)}.html", "r") as file:
            f.write(file.read().encode("utf-8"))
        length = f.tell()
        f.seek(0)
        self.send_response(code)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    def list_directory(self, path):
        try:
            listx = os.listdir(path)
        except os.error:
            self.error_page(403, "No permission to list directory")
            return None

        listx.sort(key=lambda a: a.lower())
        f = BytesIO()
        displaypath = html.escape(urllib.parse.unquote(self.path))

        # Check if we can navigate to the parent directory
        parent_dir_link = ''
        if os.path.abspath(path) != os.path.abspath(shareDir):
            parent_dir_link = '<li><a href="../">../</a></li>'

        f.write(b'\t<!DOCTYPE html>\n')
        f.write(b"\t<html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title> %s</title>\n" % displaypath.encode('utf-8'))
        f.write(b"\t<style>\n")
        f.write(b"\t:root { color-scheme: light; font-family: Arial, sans-serif; }\n")
        f.write(b"\tbody { margin: 0; background: linear-gradient(180deg, #eef4ff 0%%, #f7f9fc 100%%); color: #1f2937; }\n")
        f.write(b"\t.container { max-width: 980px; margin: 0 auto; padding: 24px 16px 40px; }\n")
        f.write(b"\t.hero, .panel { background: rgba(255,255,255,0.94); border-radius: 18px; box-shadow: 0 14px 40px rgba(15,23,42,0.08); border: 1px solid rgba(148,163,184,0.18); }\n")
        f.write(b"\t.hero { padding: 24px; margin-bottom: 18px; }\n")
        f.write(b"\th1 { margin: 0 0 8px; font-size: 28px; }\n")
        f.write(b"\t.subtitle { margin: 0; color: #64748b; word-break: break-all; }\n")
        f.write(b"\t.panel { padding: 20px; margin-bottom: 18px; }\n")
        f.write(b"\t.upload-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-bottom: 14px; }\n")
        f.write(b"\tlabel.field { display: block; padding: 14px; border: 1px dashed #93c5fd; border-radius: 14px; background: #f8fbff; font-weight: bold; }\n")
        f.write(b"\tlabel.field span { display: block; margin-top: 6px; font-size: 13px; font-weight: normal; color: #64748b; }\n")
        f.write(b"\tinput[type='file'] { display: block; margin-top: 10px; width: 100%%; }\n")
        f.write(b"\tbutton, input[type='submit'] { border: none; border-radius: 999px; background: linear-gradient(135deg, #2563eb, #3b82f6); color: white; padding: 12px 22px; font-size: 15px; cursor: pointer; }\n")
        f.write(b"\tbutton:hover, input[type='submit']:hover { opacity: 0.94; }\n")
        f.write(b"\t#progressContainer { margin-top: 14px; display: none; }\n")
        f.write(b"\t#progressMeta { display: flex; justify-content: space-between; font-size: 14px; color: #475569; margin-bottom: 6px; }\n")
        f.write(b"\tprogress { width: 100%%; height: 14px; }\n")
        f.write(b"\t.file-header, li { display: grid; grid-template-columns: minmax(0,1fr) 110px; gap: 16px; align-items: center; }\n")
        f.write(b"\t.file-header { padding-bottom: 10px; margin-bottom: 8px; border-bottom: 1px solid #e2e8f0; color: #2563eb; font-weight: bold; }\n")
        f.write(b"\tul { list-style-type: none; padding-left: 0; margin: 0; }\n")
        f.write(b"\tli { padding: 12px 14px; border-radius: 12px; margin: 8px 0; background: #f8fafc; }\n")
        f.write(b"\tli:hover { background: #eff6ff; }\n")
        f.write(b"\tli a { text-decoration: none; color: #0f172a; overflow-wrap: anywhere; }\n")
        f.write(b"\tli a:hover { color: #2563eb; }\n")
        f.write(b"\t.file-size { color: #64748b; text-align: right; }\n")
        f.write(b"\tfooter { text-align: center; color: #64748b; font-size: 14px; }\n")
        f.write(b"\tfooter a { color: #2563eb; text-decoration: none; }\n")
        f.write(b"\t.empty-state { padding: 20px 0; color: #64748b; text-align: center; }\n")
        f.write(b"\t@media (max-width: 640px) { .container { padding: 16px 12px 32px; } h1 { font-size: 24px; } .file-header, li { grid-template-columns: minmax(0,1fr) 88px; gap: 10px; } }\n")
        f.write(b"\t</style></head>\n")
        f.write(b"\t<body><div class='container'>\n")
        f.write("\t<section class='hero'><h1>局域网文件共享</h1><p class='subtitle'>当前目录 / Current directory: %s</p></section>\n".encode('utf-8') % displaypath.encode('utf-8'))
        f.write(b"\t<section class='panel'>\n")
        f.write(b"\t<form ENCTYPE='multipart/form-data' method='post' id='uploadForm'>\n")
        f.write(b"\t<div class='upload-grid'>\n")
        f.write("\t<label class='field'>上传文件 / Files<input name='file' type='file' multiple/><span>支持多选</span></label>\n".encode('utf-8'))
        f.write("\t<label class='field'>上传文件夹 / Folder<input name='file' type='file' webkitdirectory directory multiple/><span>保留目录结构，部分浏览器支持</span></label>\n".encode('utf-8'))
        f.write(b"\t</div>\n")
        f.write("\t<input type='submit' value='开始上传 / Upload'/>\n".encode('utf-8'))
        f.write(b"\t</form>\n")
        f.write(b"\t<div id='progressContainer'>\n")
        f.write("\t<div id='progressMeta'><span id='progressText'>准备上传</span><span id='progressPercent'>0%</span></div>\n".encode('utf-8'))
        f.write(b"\t<progress id='progressBar' value='0' max='100'></progress>\n")
        f.write(b"\t</div>\n")
        f.write(b"\t</section>\n")
        f.write(b"\t<section class='panel'>\n")
        f.write(b"\t<div class='file-header'>\n")
        f.write("\t<span>名称 / Name</span><span>大小 / Size</span>\n".encode('utf-8'))
        f.write(b"\t</div>\n")
        f.write(b"\t<ul>\n")

        # Write the parent directory link if available
        if parent_dir_link:
            f.write(b"\t%s\n" % parent_dir_link.encode('utf-8'))

        entry_count = 1 if parent_dir_link else 0
        for name in listx:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            file_size = ''
            if os.path.isdir(fullname):
                linkname = name + "/"
                displayname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
            else:
                file_size = sizeof_fmt(os.path.getsize(fullname)) if os.path.isfile(fullname) else ''

            f.write(b"\t<li><a href='%s'>%s</a><span class='file-size'>%s</span></li>\n" % (
                urllib.parse.quote(linkname).encode('utf-8'),
                html.escape(displayname).encode('utf-8'),
                file_size.encode('utf-8')
            ))
            entry_count += 1

        if entry_count == 0:
            f.write("\t<li class='empty-state'>当前目录为空，可直接上传文件到这里。</li>\n".encode('utf-8'))

        f.write(b"\t</ul>\n")
        f.write(b"\t</section>\n")

        f.write(b"\t<footer>\n")
        f.write("\t<p>项目链接 / Project link: <a href=https://gitee.com/shenmo7192/momo-and-mox-tool-scripts/blob/master/updowner.py>Momo and Mox Tool Scripts</a></p>\n".encode('utf-8'))
        f.write(b"\t</footer>\n")

        f.write(b"</div></body></html>\n")

        # JavaScript for progress bar
        f.write(b"\t<script>\n")
        f.write("""
            const form = document.getElementById('uploadForm');
            const progressBar = document.getElementById('progressBar');
            const progressPercent = document.getElementById('progressPercent');
            const progressContainer = document.getElementById('progressContainer');
            const progressText = document.getElementById('progressText');

            form.addEventListener('submit', function(event) {
                event.preventDefault();
                const formData = new FormData(form);
                
                // Check for folder paths in regular file inputs
                const fileInputs = document.querySelectorAll('input[name="file"]');
                for (let input of fileInputs) {
                    if (!input.hasAttribute('webkitdirectory')) {
                        for (let file of input.files) {
                            if (file.name.includes('/') || file.name.includes('\\\\')) {
                                alert('检测到文件夹路径，请使用文件夹选择控件上传文件夹。');
                                return;
                            }
                        }
                    }
                }
                
                const xhr = new XMLHttpRequest();

                xhr.open('POST', window.location.href, true);

                // Track upload progress
                xhr.upload.onprogress = function(event) {
                    if (event.lengthComputable) {
                        const percentComplete = Math.round((event.loaded / event.total) * 100);
                        progressBar.value = percentComplete;
                        progressPercent.textContent = percentComplete + '%';
                        progressText.textContent = '正在上传 / Uploading';
                    }
                };

                // Show progress bar when upload starts
                xhr.onloadstart = function() {
                    progressContainer.style.display = 'block';
                    progressText.textContent = '正在准备上传 / Preparing';
                };

                // Handle the server response when upload completes
                xhr.onloadend = function() {
                    if (xhr.status === 200) {
                        progressBar.value = 100;
                        progressPercent.textContent = '100%';

                        // Replace the entire page content with the server's response
                        document.open();
                        document.write(xhr.responseText);  // Replace the current page with the success page
                        document.close();
                    } else {
                        progressText.textContent = '上传失败 / Upload failed';
                        alert('Upload failed: ' + xhr.status + ' - ' + xhr.responseText);
                    }
                };

                // Send form data
                xhr.send(formData);
            });
        """.encode('utf-8'))
        f.write(b"\t</script>\n")

        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    
    def do_POST(self):
        """Serve a POST request to handle file upload (supports multiple files and directories)."""
        content_type = self.headers.get('Content-Type')
        if not content_type or 'multipart/form-data' not in content_type:
            self.send_error(501, "Unsupported method (POST)")
            return

        content_length = self.headers.get('Content-Length')
        if not content_length:
            self.send_error(411, "Content-Length header is required")
            return

        body = self.rfile.read(int(content_length))
        files = parse_uploaded_files(content_type, body)
        if not files:
            self.send_error(400, "No file fields found in POST")
            return

        path = self.translate_path(self.path)
        saved = []
        skipped = []
        for original_name, file_bytes in files:
            filename = sanitize_upload_name(original_name)
            if not filename:
                skipped.append(original_name)
                continue

            dest = os.path.join(path, filename)
            dest_dir = os.path.dirname(dest)
            os.makedirs(dest_dir, exist_ok=True)
            try:
                with open(dest, 'wb') as out:
                    out.write(file_bytes)
                saved.append(dest[len(path)+1:])
            except IOError:
                skipped.append(original_name)

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        response = BytesIO()
        response.write(b"<!DOCTYPE html>")
        response.write(b"<html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>")
        response.write(b"<title>Upload Success</title>")
        response.write(b"<style>")
        response.write(b"body { margin: 0; font-family: Arial, sans-serif; background: linear-gradient(180deg, #eefbf3 0%, #f8fafc 100%); color: #1f2937; }")
        response.write(b".container { max-width: 720px; margin: 0 auto; padding: 28px 16px; }")
        response.write(b".card { background: white; padding: 24px; border-radius: 18px; box-shadow: 0 14px 40px rgba(15,23,42,0.08); }")
        response.write(b"h1 { color: #16a34a; margin-top: 0; }")
        response.write(b"p { line-height: 1.6; }")
        response.write(b".summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin: 18px 0; }")
        response.write(b".metric { padding: 14px; border-radius: 14px; background: #f8fafc; border: 1px solid #e2e8f0; }")
        response.write(b".metric strong { display: block; font-size: 24px; color: #0f172a; }")
        response.write(b"ul { margin: 0; padding-left: 18px; }")
        response.write(b"li { margin: 8px 0; overflow-wrap: anywhere; }")
        response.write(b"a { text-decoration: none; color: #2563eb; }")
        response.write(b"a:hover { text-decoration: underline; }")
        response.write(b".muted { color: #64748b; }")
        response.write(b"</style></head>")
        response.write(b"<body><div class='container'><div class='card'>")
        response.write("<h1>Upload Success! 上传成功！</h1>".encode('utf-8'))
        response.write(b"<p>Your files have been processed and saved to the current shared directory.</p>")
        response.write("<p>文件已经处理完成，并保存到当前共享目录。</p>".encode('utf-8'))
        response.write(b"<div class='summary'>")
        response.write(f"<div class='metric'><span class='muted'>Uploaded</span><strong>{len(saved)}</strong></div>".encode('utf-8'))
        response.write(f"<div class='metric'><span class='muted'>Skipped</span><strong>{len(skipped)}</strong></div>".encode('utf-8'))
        response.write(b"</div>")
        if saved:
            response.write("<p><strong>已上传文件 / Uploaded files</strong></p>".encode('utf-8'))
            response.write(b"<ul>")
            for fname in saved:
                response.write(f"<li>{html.escape(fname)}</li>".encode('utf-8'))
            response.write(b"</ul>")
        if skipped:
            response.write("<p><strong>已跳过项目 / Skipped items</strong></p>".encode('utf-8'))
            response.write(b"<ul>")
            for fname in skipped:
                response.write(f"<li>{html.escape(fname)}</li>".encode('utf-8'))
            response.write(b"</ul>")
        response.write(b"<hr>")

        back_link = html.escape(self.path)
        response.write("<p><a href='%s'>Back to the file list / 返回文件列表</a></p>".encode('utf-8') % back_link.encode('utf-8'))
        response.write(b"</div></div></body></html>")

        length = response.tell()
        response.seek(0)
        self.wfile.write(response.read())


class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
    address_family = socket.AF_INET6  # Support IPv6

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple HTTP Server with Upload.')
    parser.add_argument('port', type=int, nargs='?', default=8080, help='Port to listen on (default: 8080)')
    parser.add_argument('-d', '--directory', default=os.getcwd(), help='Directory to share (default: current directory)')
    args = parser.parse_args()

    shareDir = args.directory
    serveraddr = ('::', args.port)  # Listen on all IPv6 interfaces

    showTips(args.port)
    server = ThreadingSimpleServer(serveraddr, SimpleHTTPRequestHandlerWithUpload)
    print(f"Serving files from directory: {shareDir}")
    print("Starting server, use <Ctrl-C> to stop")
    server.serve_forever()
