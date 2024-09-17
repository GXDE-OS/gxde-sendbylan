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
import argparse

__version__ = "0.1"

class GetWanIp:
    def getip(self):
        return "127.0.0.1"

def showTips(port):
    print("")
    print('----------------------------------------------------------------------->> ')
    print(f'-------->> Now, listening at port {port}...')
    osType = platform.system()
    if osType == "Linux":
        print(f'-------->> You can visit the URL: http://{GetWanIp().getip()}:{port}')
    else:
        print(f'-------->> You can visit the URL: http://127.0.0.1:{port}')
    print('----------------------------------------------------------------------->> ')
    print("")

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

    def translate_path(self, path):
        """Override to serve from the custom directory."""
        # Use the shareDir (custom directory) instead of the current working directory
        path = urllib.parse.unquote(path)
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        trailing_slash = path.rstrip().endswith('/')
        path = os.path.normpath(path)

        # Map the requested path to the shared directory
        full_path = os.path.join(shareDir, path.lstrip('/'))
        if os.path.isdir(full_path) and trailing_slash:
            return full_path + '/'
        return full_path

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
    parser = argparse.ArgumentParser(description='Simple HTTP Server with Upload.')
    parser.add_argument('port', type=int, nargs='?', default=8080, help='Port to listen on (default: 8080)')
    parser.add_argument('-d', '--directory', default=os.getcwd(), help='Directory to share (default: current directory)')
    args = parser.parse_args()

    shareDir = args.directory
    serveraddr = ('', args.port)

    showTips(args.port)
    server = ThreadingSimpleServer(serveraddr, SimpleHTTPRequestHandlerWithUpload)
    print(f"Serving files from directory: {shareDir}")
    print("Starting server, use <Ctrl-C> to stop")
    server.serve_forever()
