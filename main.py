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
from http.server import SimpleHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from io import BytesIO

__version__ = "0.1"

class GetWanIp:
    def getip(self):
        return "127.0.0.1"

def showTips():
    print("")
    print('----------------------------------------------------------------------->> ')
    try:
        port = int(sys.argv[1])
    except Exception:
        print('-------->> Warning: Port is not given, will use default port: 8080 ')
        print('-------->> if you want to use another port, please execute: ')
        print('-------->> python SimpleHTTPServerWithUpload.py port ')
        port = 8080

    if not 0 < port < 65535:
        port = 8080

    print(f'-------->> Now, listening at port {port}...')
    osType = platform.system()
    if osType == "Linux":
        print(f'-------->> You can visit the URL: http://{GetWanIp().getip()}:{port}')
    else:
        print(f'-------->> You can visit the URL: http://127.0.0.1:{port}')
    print('----------------------------------------------------------------------->> ')
    print("")
    return ('', port)


serveraddr = showTips()
shareDir = os.getcwd()

try:
    shareDir = sys.argv[2]
    print('share dir is ' + shareDir)
except Exception:
    print('did not set share dir, use current dir ' + shareDir)


def sizeof_fmt(num):
    for x in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


def modification_date(filename):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(filename)))


class SimpleHTTPRequestHandlerWithUpload(SimpleHTTPRequestHandler):

    server_version = "SimpleHTTPWithUpload/" + __version__

    def do_POST(self):
        """Serve a POST request."""
        r, info = self.deal_post_data()
        print(r, info, "by: ", self.client_address)
        f = BytesIO()
        f.write(b'<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write(b"<html>\n<title>Upload Result Page</title>\n")
        f.write(b"<body>\n<h2>Upload Result Page</h2>\n")
        f.write(b"<hr>\n")
        if r:
            f.write(b"<strong>Success:</strong>")
        else:
            f.write(b"<strong>Failed:</strong>")
        f.write(info.encode())
        f.write(b"<br><a href='%s'>back</a>" % self.headers['referer'].encode())
        f.write(b"<hr><small>Powered By: bones7456, check new version at ")
        f.write(b"<a href='http://li2z.cn/?s=SimpleHTTPServerWithUpload'>")
        f.write(b"here</a>.</small></body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        self.wfile.write(f.getvalue())

    def deal_post_data(self):
        boundary = self.headers.get_boundary()
        remainbytes = int(self.headers['content-length'])
        line = self.rfile.readline()
        remainbytes -= len(line)
        if not boundary.encode() in line:
            return (False, "Content NOT begin with boundary")
        line = self.rfile.readline()
        remainbytes -= len(line)
        fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line.decode('utf-8'))
        if not fn:
            return (False, "Can't find out file name...")
        path = shareDir + self.path
        fn = os.path.join(path, fn[0])

        while os.path.exists(fn):
            fn += "_"

        line = self.rfile.readline()
        remainbytes -= len(line)
        line = self.rfile.readline()
        remainbytes -= len(line)

        try:
            out = open(fn, 'wb')
        except IOError:
            return (False, "Can't create file to write, do you have permission to write?")

        preline = self.rfile.readline()
        remainbytes -= len(preline)
        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            if boundary.encode() in line:
                preline = preline[0:-1]
                if preline.endswith(b'\r'):
                    preline = preline[0:-1]
                out.write(preline)
                out.close()
                return (True, f"File '{fn}' upload success!")
            else:
                out.write(preline)
                preline = line
        return (False, "Unexpected end of data.")

    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html)."""
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

        f.write(b'<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write(b"<html><head><meta charset='utf-8'><title>%s</title></head>" % displaypath.encode('utf-8'))
        f.write("<body><h2>文件列表 Directory listing for %s</h2>".encode('utf-8') % displaypath.encode('utf-8'))
        f.write(b"<hr><form ENCTYPE='multipart/form-data' method='post'>")
        f.write(b"<input name='file' type='file'/><input type='submit' value='")
        f.write('上传Upload'.encode('utf-8'))  # Encode non-ASCII characters
        f.write(b"'/></form>")
        f.write(b"<hr><ul>")

        # Write the parent directory link if available
        if parent_dir_link:
            f.write(parent_dir_link.encode('utf-8'))

        for name in listx:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            if os.path.isdir(fullname):
                linkname = name + "/"
                displayname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
            f.write(b'<li><a href="%s">%s</a></li>' % (urllib.parse.quote(linkname).encode('utf-8'), html.escape(displayname).encode('utf-8')))
        
        f.write(b"</ul><hr></body></html>")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f


class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
    pass


if __name__ == '__main__':
    server = ThreadingSimpleServer(serveraddr, SimpleHTTPRequestHandlerWithUpload)
    print("Starting server, use <Ctrl-C> to stop")
    server.serve_forever()
