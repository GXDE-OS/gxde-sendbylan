#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GXDE SendByLan - 局域网文件传输工具
一个简单的 HTTP 服务器，支持文件上传、下载和目录浏览。

Usage:
    python main.py [port] [-d directory]

Example:
    python main.py 8080 -d /home/user/share
"""

import argparse
import fcntl
import html
import mimetypes
import os
import platform
import re
import socket
import struct
import sys
import threading
import urllib.parse
from http.server import SimpleHTTPRequestHandler, HTTPServer
from io import BytesIO
from socketserver import ThreadingMixIn
from typing import Optional, List, Tuple

__version__ = "0.3"

# 全局配置
PROGRAM_PATH = os.path.dirname(os.path.realpath(__file__))
SHARE_DIR = os.getcwd()


# =============================================================================
# HTML 模板
# =============================================================================

HTML_TEMPLATE_BASE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --primary: #2196F3;
            --primary-dark: #1976D2;
            --success: #4CAF50;
            --bg: #f5f7fa;
            --card-bg: #ffffff;
            --text: #333333;
            --text-secondary: #666666;
            --border: #e0e0e0;
            --hover: #e3f2fd;
            --shadow: 0 2px 8px rgba(0,0,0,0.1);
            --radius: 12px;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }}
        .card {{
            background: var(--card-bg);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            padding: 24px;
            margin-bottom: 20px;
        }}
        h1, h2 {{
            color: var(--text);
            margin-bottom: 16px;
            font-weight: 600;
        }}
        h1 {{ font-size: 1.5rem; }}
        h2 {{ font-size: 1.25rem; color: var(--primary); }}
        .upload-area {{
            border: 2px dashed var(--border);
            border-radius: var(--radius);
            padding: 24px;
            text-align: center;
            margin-bottom: 16px;
            transition: all 0.3s ease;
        }}
        .upload-area:hover {{
            border-color: var(--primary);
            background: var(--hover);
        }}
        .file-input-wrapper {{
            position: relative;
            display: inline-block;
            margin: 8px;
        }}
        .file-input-wrapper input[type="file"] {{
            position: absolute;
            left: 0;
            top: 0;
            opacity: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
        }}
        .btn {{
            display: inline-block;
            padding: 10px 20px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
            text-decoration: none;
        }}
        .btn:hover {{ background: var(--primary-dark); }}
        .btn-secondary {{
            background: #f0f0f0;
            color: var(--text);
        }}
        .btn-secondary:hover {{ background: #e0e0e0; }}
        .btn-success {{ background: var(--success); }}
        .btn-success:hover {{ background: #45a049; }}
        .file-list {{
            list-style: none;
        }}
        .file-list-header {{
            display: grid;
            grid-template-columns: 1fr 120px 100px;
            gap: 16px;
            padding: 12px 16px;
            background: var(--bg);
            border-radius: 8px;
            font-weight: 600;
            color: var(--text-secondary);
            font-size: 0.875rem;
            margin-bottom: 8px;
        }}
        .file-item {{
            display: grid;
            grid-template-columns: 1fr 120px 100px;
            gap: 16px;
            padding: 12px 16px;
            border-radius: 8px;
            transition: background 0.2s;
            align-items: center;
        }}
        .file-item:hover {{ background: var(--hover); }}
        .file-item:nth-child(even) {{ background: #fafafa; }}
        .file-item:nth-child(even):hover {{ background: var(--hover); }}
        .file-name {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .file-name a {{
            color: var(--primary);
            text-decoration: none;
            font-weight: 500;
        }}
        .file-name a:hover {{ text-decoration: underline; }}
        .file-icon {{
            width: 20px;
            height: 20px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }}
        .file-size {{
            color: var(--text-secondary);
            font-size: 0.875rem;
            text-align: right;
        }}
        .file-actions {{
            text-align: right;
        }}
        .breadcrumb {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }}
        .breadcrumb a {{
            color: var(--primary);
            text-decoration: none;
        }}
        .breadcrumb a:hover {{ text-decoration: underline; }}
        .breadcrumb-separator {{ color: var(--text-secondary); }}
        .progress-container {{
            display: none;
            margin-top: 16px;
        }}
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: var(--bg);
            border-radius: 4px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            background: var(--primary);
            width: 0%;
            transition: width 0.3s ease;
        }}
        .progress-text {{
            text-align: center;
            margin-top: 8px;
            color: var(--text-secondary);
            font-size: 0.875rem;
        }}
        .empty-state {{
            text-align: center;
            padding: 48px;
            color: var(--text-secondary);
        }}
        .footer {{
            text-align: center;
            padding: 24px;
            color: var(--text-secondary);
            font-size: 0.875rem;
        }}
        .footer a {{ color: var(--primary); text-decoration: none; }}
        .footer a:hover {{ text-decoration: underline; }}
        .success-icon {{
            font-size: 64px;
            color: var(--success);
            margin-bottom: 16px;
        }}
        .uploaded-files {{
            background: var(--bg);
            border-radius: 8px;
            padding: 16px;
            margin: 16px 0;
            max-height: 300px;
            overflow-y: auto;
        }}
        .uploaded-files li {{
            padding: 4px 0;
            color: var(--text-secondary);
        }}
        @media (max-width: 640px) {{
            .container {{ padding: 12px; }}
            .card {{ padding: 16px; }}
            .file-list-header,
            .file-item {{ grid-template-columns: 1fr 80px; }}
            .file-actions {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
    <footer class="footer">
        <p>GXDE SendByLan v{version} | <a href="https://gitee.com/shenmo7192/gxde-sendbylan">开源项目</a></p>
    </footer>
    {scripts}
</body>
</html>"""

HTML_TEMPLATE_DIRECTORY = """
<div class="card">
    <div class="breadcrumb">
        <a href="/">🏠 根目录</a>
        {breadcrumb}
    </div>
    <h2>📁 {path}</h2>
    
    <div class="upload-area">
        <div class="file-input-wrapper">
            <button class="btn">📄 选择文件</button>
            <input type="file" id="fileInput" multiple />
        </div>
        <div class="file-input-wrapper">
            <button class="btn btn-secondary">📁 选择文件夹</button>
            <input type="file" id="folderInput" webkitdirectory directory multiple />
        </div>
        <p style="margin-top: 12px; color: var(--text-secondary); font-size: 0.875rem;">
            支持多文件上传，文件夹上传仅支持部分浏览器
        </p>
    </div>
    
    <button class="btn btn-success" id="uploadBtn" style="width: 100%; display: none;">
        🚀 开始上传
    </button>
    
    <div class="progress-container" id="progressContainer">
        <div class="progress-bar">
            <div class="progress-fill" id="progressFill"></div>
        </div>
        <div class="progress-text" id="progressText">0%</div>
    </div>
</div>

<div class="card">
    {file_list}
</div>
"""

HTML_TEMPLATE_SUCCESS = """
<div class="card" style="text-align: center;">
    <div class="success-icon">✓</div>
    <h1>上传成功！</h1>
    <p style="color: var(--text-secondary); margin-bottom: 24px;">
        成功上传 {count} 个文件
    </p>
    {file_list}
    <a href="{back_link}" class="btn" style="margin-top: 24px;">
        ← 返回文件列表
    </a>
</div>
"""

JS_TEMPLATE = """
<script>
(function() {
    const fileInput = document.getElementById('fileInput');
    const folderInput = document.getElementById('folderInput');
    const uploadBtn = document.getElementById('uploadBtn');
    const progressContainer = document.getElementById('progressContainer');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    let selectedFiles = [];
    
    function updateUploadButton() {
        const totalFiles = (fileInput.files ? fileInput.files.length : 0) + 
                          (folderInput.files ? folderInput.files.length : 0);
        if (totalFiles > 0) {
            uploadBtn.style.display = 'block';
            uploadBtn.textContent = '🚀 开始上传 (' + totalFiles + ' 个文件)';
        } else {
            uploadBtn.style.display = 'none';
        }
    }
    
    fileInput.addEventListener('change', updateUploadButton);
    folderInput.addEventListener('change', updateUploadButton);
    
    uploadBtn.addEventListener('click', function() {
        const formData = new FormData();
        
        if (fileInput.files) {
            for (let file of fileInput.files) {
                formData.append('file', file);
            }
        }
        if (folderInput.files) {
            for (let file of folderInput.files) {
                formData.append('file', file, file.webkitRelativePath || file.name);
            }
        }
        
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                progressFill.style.width = percent + '%';
                progressText.textContent = percent + '%';
            }
        });
        
        xhr.addEventListener('loadstart', function() {
            progressContainer.style.display = 'block';
            uploadBtn.disabled = true;
            uploadBtn.textContent = '上传中...';
        });
        
        xhr.addEventListener('load', function() {
            if (xhr.status === 200) {
                document.open();
                document.write(xhr.responseText);
                document.close();
            } else {
                alert('上传失败: ' + xhr.statusText);
                uploadBtn.disabled = false;
                updateUploadButton();
            }
        });
        
        xhr.addEventListener('error', function() {
            alert('上传过程中发生错误');
            uploadBtn.disabled = false;
            updateUploadButton();
        });
        
        xhr.open('POST', window.location.href);
        xhr.send(formData);
    });
})();
</script>
"""


# =============================================================================
# 工具函数
# =============================================================================

def format_file_size(num: float) -> str:
    """将字节数格式化为人类可读的字符串。"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"


def get_interface_ip(ifname: str, family: int) -> Optional[str]:
    """获取指定网络接口的 IP 地址。"""
    sock = socket.socket(family, socket.SOCK_DGRAM)
    try:
        if family == socket.AF_INET:
            result = fcntl.ioctl(
                sock.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', bytes(ifname[:15], 'utf-8'))
            )
            return socket.inet_ntoa(result[20:24])
        elif family == socket.AF_INET6:
            result = fcntl.ioctl(
                sock.fileno(),
                0x8915,
                struct.pack('256s', bytes(ifname[:15], 'utf-8'))
            )
            return socket.inet_ntop(socket.AF_INET6, result[20:36])
    except IOError:
        return None
    finally:
        sock.close()


def list_all_ips() -> List[Tuple[str, str, str]]:
    """列出所有网络接口的 IP 地址（IPv4 和 IPv6）。"""
    addresses = []
    for idx, ifname in socket.if_nameindex():
        ipv4 = get_interface_ip(ifname, socket.AF_INET)
        if ipv4 and ipv4 != '127.0.0.1':
            addresses.append((ifname, ipv4, 'IPv4'))
        
        ipv6 = get_interface_ip(ifname, socket.AF_INET6)
        if ipv6 and not ipv6.startswith('fe80'):
            addresses.append((ifname, ipv6, 'IPv6'))
    return addresses


def print_server_info(port: int, share_dir: str) -> None:
    """打印服务器启动信息。"""
    print("\n" + "=" * 60)
    print(f"  🚀 GXDE SendByLan v{__version__}")
    print("=" * 60)
    print(f"\n  📂 共享目录: {share_dir}")
    print(f"  🌐 监听端口: {port}\n")
    print("  📡 可用地址:")
    for interface, ip, version in list_all_ips():
        print(f"     • {interface} ({version}): http://{ip}:{port}")
    print("\n" + "=" * 60)
    print("  按 Ctrl+C 停止服务器")
    print("=" * 60 + "\n")


def get_file_icon(name: str, is_dir: bool, is_link: bool) -> str:
    """根据文件类型返回对应的图标。"""
    if is_dir:
        return "📁"
    if is_link:
        return "🔗"
    ext = os.path.splitext(name)[1].lower()
    icons = {
        '.txt': '📄', '.md': '📝', '.py': '🐍', '.js': '📜',
        '.html': '🌐', '.css': '🎨', '.json': '📋', '.xml': '📋',
        '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
        '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬',
        '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵',
        '.zip': '📦', '.tar': '📦', '.gz': '📦', '.7z': '📦',
        '.pdf': '📕', '.doc': '📘', '.docx': '📘',
        '.xls': '📗', '.xlsx': '📗', '.ppt': '📙', '.pptx': '📙',
    }
    return icons.get(ext, '📄')


def generate_breadcrumb(path: str) -> str:
    """生成面包屑导航 HTML。"""
    if not path or path == '/':
        return ''
    
    parts = path.strip('/').split('/')
    breadcrumb = []
    current_path = ''
    
    for part in parts:
        current_path += '/' + part
        breadcrumb.append(
            f'<span class="breadcrumb-separator">/</span>'
            f'<a href="{urllib.parse.quote(current_path)}">{html.escape(part)}</a>'
        )
    
    return ''.join(breadcrumb)


# =============================================================================
# HTTP 请求处理器
# =============================================================================

class FileServerHandler(SimpleHTTPRequestHandler):
    """支持文件上传、断点续传的 HTTP 文件服务器处理器。"""
    
    server_version = f"GXDE-SendByLan/{__version__}"
    
    def translate_path(self, path: str) -> str:
        """将 URL 路径转换为文件系统路径。"""
        path = urllib.parse.unquote(path)
        path = path.split('?', 1)[0].split('#', 1)[0]
        trailing_slash = path.rstrip().endswith('/')
        path = os.path.normpath(path)
        
        full_path = os.path.join(SHARE_DIR, path.lstrip('/'))
        if os.path.isdir(full_path) and trailing_slash:
            return full_path + '/'
        return full_path
    
    def send_head(self):
        """处理 HEAD 和 GET 请求，支持 Range 请求。"""
        path = self.translate_path(self.path)
        
        if os.path.isdir(path):
            return self.list_directory(path)
        
        try:
            file = open(path, 'rb')
        except OSError:
            return self.send_error_page(404, "文件不存在")
        
        file_size = os.path.getsize(path)
        range_header = self.headers.get('Range')
        
        if range_header:
            range_match = re.match(r"bytes=(\d+)-(\d*)", range_header)
            if range_match:
                start = int(range_match.group(1))
                end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
                
                if start >= file_size:
                    self.send_error(416, "Range Not Satisfiable")
                    return None
                
                self.send_response(206)
                self.send_header("Content-Type", self.guess_type(path))
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(end - start + 1))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                
                file.seek(start)
                self.wfile.write(file.read(end - start + 1))
                file.close()
                return None
        
        self.send_response(200)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        return file
    
    def send_error_page(self, code: int, message: str):
        """发送错误页面。"""
        error_file = os.path.join(PROGRAM_PATH, "error", f"{code}.html")
        
        if os.path.exists(error_file):
            with open(error_file, 'rb') as f:
                content = f.read()
        else:
            content = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Error {code}</title></head>
<body style="font-family: sans-serif; text-align: center; padding: 50px;">
<h1>Error {code}</h1><p>{message}</p>
</body></html>""".encode('utf-8')
        
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)
    
    def list_directory(self, path: str):
        """生成目录列表页面。"""
        try:
            entries = os.listdir(path)
        except OSError:
            return self.send_error_page(403, "无权限访问此目录")
        
        entries.sort(key=str.lower)
        display_path = html.escape(urllib.parse.unquote(self.path)) or '/'
        
        # 生成文件列表
        file_items = []
        parent_link = ''
        
        if os.path.abspath(path) != os.path.abspath(SHARE_DIR):
            parent_link = '''
            <div class="file-item">
                <div class="file-name">
                    <span class="file-icon">⬆️</span>
                    <a href="../">返回上级目录</a>
                </div>
                <div class="file-size">-</div>
                <div class="file-actions"></div>
            </div>'''
        
        for name in entries:
            fullname = os.path.join(path, name)
            is_dir = os.path.isdir(fullname)
            is_link = os.path.islink(fullname)
            
            display_name = name
            link_name = name
            if is_dir:
                display_name += '/'
                link_name += '/'
            if is_link:
                display_name += '@'
            
            size = format_file_size(os.path.getsize(fullname)) if os.path.isfile(fullname) else '-'
            icon = get_file_icon(name, is_dir, is_link)
            
            file_items.append(f'''
            <div class="file-item">
                <div class="file-name">
                    <span class="file-icon">{icon}</span>
                    <a href="{urllib.parse.quote(link_name)}">{html.escape(display_name)}</a>
                </div>
                <div class="file-size">{size}</div>
                <div class="file-actions">
                    {f'<a href="{urllib.parse.quote(link_name)}" download class="btn btn-secondary" style="padding: 4px 12px; font-size: 12px;">下载</a>' if not is_dir else ''}
                </div>
            </div>''')
        
        file_list_html = f'''
        <div class="file-list-header">
            <span>名称</span>
            <span style="text-align: right;">大小</span>
            <span></span>
        </div>
        <div class="file-list">
            {parent_link}
            {''.join(file_items) if file_items else '<div class="empty-state">📂 空文件夹</div>'}
        </div>'''
        
        content = HTML_TEMPLATE_DIRECTORY.format(
            path=display_path,
            breadcrumb=generate_breadcrumb(self.path),
            file_list=file_list_html
        )
        
        html_output = HTML_TEMPLATE_BASE.format(
            title=f"GXDE SendByLan - {display_path}",
            version=__version__,
            content=content,
            scripts=JS_TEMPLATE
        )
        
        encoded = html_output.encode('utf-8')
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        
        from io import BytesIO
        f = BytesIO(encoded)
        return f
    
    def do_POST(self):
        """处理文件上传请求。"""
        import cgi
        
        content_type = self.headers.get('Content-Type', '')
        if 'multipart/form-data' not in content_type:
            self.send_error(501, "不支持的请求类型")
            return
        
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'},
            keep_blank_values=True
        )
        
        files = form.get('file')
        if not files:
            self.send_error(400, "没有找到文件")
            return
        
        if not isinstance(files, list):
            files = [files]
        
        upload_path = self.translate_path(self.path)
        saved_files = []
        
        for item in files:
            if not item.filename:
                continue
            
            filename = os.path.normpath(item.filename)
            filename = filename.lstrip(os.sep)
            
            dest = os.path.join(upload_path, filename)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            
            try:
                with open(dest, 'wb') as out:
                    out.write(item.file.read())
                saved_files.append(filename)
            except IOError as e:
                print(f"保存文件失败 {filename}: {e}")
        
        # 生成成功页面
        file_list_html = ''
        if saved_files:
            file_list_html = '<ul class="uploaded-files">' + ''.join(
                f'<li>📄 {html.escape(f)}</li>' for f in saved_files
            ) + '</ul>'
        
        content = HTML_TEMPLATE_SUCCESS.format(
            count=len(saved_files),
            file_list=file_list_html,
            back_link=html.escape(self.path)
        )
        
        html_output = HTML_TEMPLATE_BASE.format(
            title="上传成功 - GXDE SendByLan",
            version=__version__,
            content=content,
            scripts=''
        )
        
        encoded = html_output.encode('utf-8')
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """支持多线程和 IPv6 的 HTTP 服务器。"""
    address_family = socket.AF_INET6
    daemon_threads = True


# =============================================================================
# 主程序
# =============================================================================

def main():
    """程序入口。"""
    global SHARE_DIR
    
    parser = argparse.ArgumentParser(
        description='GXDE SendByLan - 局域网文件传输工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  %(prog)s                    # 使用默认端口 8080，共享当前目录
  %(prog)s 9000               # 使用端口 9000
  %(prog)s -d /home/share     # 共享指定目录
  %(prog)s 8080 -d /tmp       # 组合使用
        '''
    )
    parser.add_argument(
        'port',
        nargs='?',
        type=int,
        default=8080,
        help='监听端口 (默认: 8080)'
    )
    parser.add_argument(
        '-d', '--directory',
        default=os.getcwd(),
        help='要共享的目录 (默认: 当前目录)'
    )
    
    args = parser.parse_args()
    
    # 验证目录
    if not os.path.isdir(args.directory):
        print(f"错误: 目录不存在: {args.directory}")
        sys.exit(1)
    
    SHARE_DIR = os.path.abspath(args.directory)
    
    # 打印服务器信息
    print_server_info(args.port, SHARE_DIR)
    
    # 启动服务器
    server_address = ('::', args.port)
    httpd = ThreadedHTTPServer(server_address, FileServerHandler)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n正在关闭服务器...")
        httpd.shutdown()
        print("服务器已停止")


if __name__ == '__main__':
    main()
