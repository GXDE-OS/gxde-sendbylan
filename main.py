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
from http.server import SimpleHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from io import BytesIO
import argparse
import re

__version__ = "0.2"
import fcntl
import struct


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
            self.send_error(404, "File not found")
            return None

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

    def list_directory(self, path):
        try:
            listx = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None

        listx.sort(key=lambda a: a.lower())
        f = BytesIO()
        displaypath = html.escape(urllib.parse.unquote(self.path))

        # Check if we can navigate to the parent directory
        parent_dir_link = ''
        if os.path.abspath(path) != os.path.abspath(shareDir):
            parent_dir_link = '<li><a href="../">../</a></li>'

        # Beautified HTML layout with header
        f.write(b'\t<!DOCTYPE html>\n')
        f.write(b"\t<html><head><meta charset='utf-8'><title> %s</title>\n" % displaypath.encode('utf-8'))
        f.write(b"\t<style>\n")
        f.write(b"\tbody { font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 20px; }\n")
        f.write(b"\t.container { max-width: 900px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }\n")
        f.write(b"\th2 { color: #333; }\n")
        f.write(b"\tul { list-style-type: none; padding-left: 0; margin: 0; }\n")
        f.write(b"\tli { margin: 8px 0; display: flex; justify-content: space-between; padding: 8px 0; }\n")
        f.write(b"\tli:nth-child(odd) { background-color: #f9f9f9; }\n")  # Add alternating row colors
        f.write(b"\tli a { text-decoration: none; color: #2196F3; }\n")  # Link color for file/folder names
        f.write(b"\tli a:hover { text-decoration: underline; }\n")  # Hover effect for file/folder names
        f.write(b"\tli:hover { background-color: #e0f7fa; }\n")  # Hover effect for the entire list item
        f.write(b"\t.file-size { color: #666; }\n")
        f.write(b"\t.file-header { display: flex; justify-content: space-between; font-weight: bold; padding: 8px 0; border-bottom: 2px solid #ddd; color: #2196F3; }\n")
        f.write(b"\t#progressContainer { margin-top: 20px; display: none; }\n")  # Hide progress bar by default
        f.write(b"\tfooter { margin-top: 20px; text-align: center; color: #666; }\n")  # Footer styling
        f.write(b"\tfooter a { color: #2196F3; text-decoration: none; }\n")  # Footer link color
        f.write(b"\tfooter a:hover { text-decoration: underline; }\n")  # Footer link hover effect
        f.write(b"\t</style></head>\n")
        f.write(b"\t<body><div class='container'>\n")
        f.write("\t<h2>文件列表 / Directory listing for %s</h2>\n".encode('utf-8') % displaypath.encode('utf-8'))
        f.write(b"\t<form ENCTYPE='multipart/form-data' method='post' id='uploadForm'>\n")
        f.write("\t<input name='file' type='file'/><input type='submit' value='上传 Upload'/>\n".encode('utf-8'))
        f.write(b"\t</form>\n")

        # Progress bar container
        f.write(b"\t<div id='progressContainer'>\n")
        f.write(b"\t<p>Upload Progress: <span id='progressPercent'>0%</span></p>\n")
        f.write(b"\t<progress id='progressBar' value='0' max='100'></progress>\n")
        f.write(b"\t</div>\n")
        f.write(b"\t<hr>\n")

        # Add file list header for Name and Size
        f.write(b"\t<div class='file-header'>\n")
        f.write("\t<span>名称 / Name</span><span>大小 / Size</span>\n".encode('utf-8'))
        f.write(b"\t</div>\n")

        f.write(b"\t<ul>\n")

        # Write the parent directory link if available
        if parent_dir_link:
            f.write(b"\t%s\n" % parent_dir_link.encode('utf-8'))

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

        f.write(b"\t</ul><hr>\n")

        # Footer with project link
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

            form.addEventListener('submit', function(event) {
                event.preventDefault();
                const formData = new FormData(form);
                const xhr = new XMLHttpRequest();

                xhr.open('POST', window.location.href, true);

                // Track upload progress
                xhr.upload.onprogress = function(event) {
                    if (event.lengthComputable) {
                        const percentComplete = Math.round((event.loaded / event.total) * 100);
                        progressBar.value = percentComplete;
                        progressPercent.textContent = percentComplete + '%';
                    }
                };

                // Show progress bar when upload starts
                xhr.onloadstart = function() {
                    progressContainer.style.display = 'block';
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
                        alert('Upload failed, please try again.');
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
           """Serve a POST request to handle file upload without progress tracking."""
           content_type = self.headers.get('Content-Type')
           if not content_type or 'multipart/form-data' not in content_type:
               self.send_error(501, "Unsupported method (POST)")
               return
    
           boundary = content_type.split("=")[1].encode('utf-8')
           remainbytes = int(self.headers['Content-length'])
           line = self.rfile.readline()
           remainbytes -= len(line)
           if boundary not in line:
               self.send_error(400, "Content does not start with boundary")
               return
    
           line = self.rfile.readline()
           remainbytes -= len(line)
           fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line.decode('utf-8'))
           if not fn:
               self.send_error(400, "Can't find out file name")
               return
           path = self.translate_path(self.path)
           fn = os.path.join(path, fn[0])
           line = self.rfile.readline()
           remainbytes -= len(line)
           line = self.rfile.readline()
           remainbytes -= len(line)
    
           try:
               with open(fn, 'wb') as out:
                   preline = self.rfile.readline()
                   remainbytes -= len(preline)
                   while remainbytes > 0:
                       line = self.rfile.readline()
                       remainbytes -= len(line)
                       
                       if boundary in line:
                           preline = preline[0:-1]
                           if preline.endswith(b'\r'):
                               preline = preline[0:-1]
                           out.write(preline)
                           break
                       else:
                           out.write(preline)
                           preline = line
        
                # Return the beautified success page with correct back link
               self.send_response(200)
               self.send_header("Content-type", "text/html; charset=utf-8")
               self.end_headers()
        
               response = BytesIO()
               response.write(b"<!DOCTYPE html>")
               response.write(b"<html><head><meta charset='utf-8'>")
               response.write(b"<title>Upload Success</title>")
               response.write(b"<style>")
               response.write(b"body { font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 20px; }")
               response.write(b".container { max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }")
               response.write(b"h1 { color: #4CAF50; }")
               response.write(b"p { font-size: 1.2em; }")
               response.write(b"a { text-decoration: none; color: #2196F3; }")
               response.write(b"a:hover { text-decoration: underline; }")
               response.write(b"</style></head>")
               response.write(b"<body><div class='container'>")
               response.write("<h1>Upload Success! 上传成功！</h1>".encode('utf-8'))
               response.write(b"<p>Your file has been successfully uploaded.</p>")
               response.write("<p>您的文件已成功上传。</p>".encode('utf-8'))
               response.write(b"<hr>")
        
                # Set the back link to the current directory instead of root
               back_link = html.escape(self.path)
               response.write("<p><a href='%s'>Back to the file list / 返回文件列表</a></p>".encode('utf-8') % back_link.encode('utf-8'))
               response.write(b"</div></body></html>")
       
               length = response.tell()
               response.seek(0)
               self.wfile.write(response.read())
       
           except IOError:
               self.send_error(500, "Failed to write file")

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
