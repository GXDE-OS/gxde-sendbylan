#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
#    NGINX Config 
#    proxy_read_timeout 3600s;
#    client_max_body_size 0;
#    proxy_request_buffering off;


from xml.etree import ElementTree as ET
import argparse
import socket
import socketserver
import http.server
import os
import sys
from urllib.parse import urlparse, unquote
import shutil
import uuid
import re
import platform
import mimetypes
from xml.sax.saxutils import escape
from html import escape as html_escape
import struct
import fcntl
import base64
from functools import wraps
import time
from urllib.parse import quote


FILE_BUFFER_SIZE = 64 * 1024
SERVER_BRAND = "Erotica WebServer"
SERVER_VERSION = "v3.2.1"
SERVER_HEADER_NAME = "Erotica-WebServer"
SMB_DEFAULT_PORT = 445
SMB_SHARE_FALLBACK = "share"



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


def format_size(size):
    """Convert file size to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def guess_file_icon(name, is_dir, is_link):
    if is_dir:
        return '📁'
    if is_link:
        return '🔗'

    ext = os.path.splitext(name.lower())[1]
    if ext in {'.txt', '.md', '.rst', '.log', '.ini', '.cfg', '.conf'}:
        return '📄'
    if ext in {'.doc', '.docx', '.odt'}:
        return '📝'
    if ext in {'.xls', '.xlsx', '.csv', '.ods'}:
        return '📊'
    if ext in {'.ppt', '.pptx', '.odp'}:
        return '📽'
    if ext in {'.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac'}:
        return '🎵'
    if ext in {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv'}:
        return '🎬'
    if ext in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'}:
        return '🖼'
    if ext in {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'}:
        return '🗜'
    if ext in {'.py', '.sh', '.js', '.ts', '.lua', '.rb', '.pl', '.php', '.c', '.cpp', '.h', '.hpp', '.java'}:
        return '⚙'
    return '❔'


def sanitize_share_name(name, fallback=SMB_SHARE_FALLBACK):
    """把任意字符串整理成安全的 SMB 共享名。"""
    cleaned = re.sub(r'[^0-9A-Za-z._$-]', '-', (name or '').strip()).strip('-')
    return cleaned or fallback


def resolve_share_name(share_name, directory):
    """未显式指定共享名时，使用共享目录的目录名。"""
    candidate = share_name if share_name else os.path.basename(os.path.abspath(directory))
    return sanitize_share_name(candidate)


def normalize_request_path(path):
    return unquote(path or '/')


def extract_url_path(path):
    parsed = urlparse(path or '/')
    target = parsed.path if parsed.scheme or parsed.netloc else (path or '/')
    return target or '/'


def normalize_destination_path(destination):
    parsed = urlparse(destination)
    target = parsed.path if parsed.scheme else destination
    normalized = unquote(target or '/')
    return normalized if normalized.startswith('/') else '/' + normalized


def encode_href_path(path):
    return quote(path or '/', safe='/%')


def parse_range_header(range_header, file_size):
    range_header = range_header or ''
    open_ended_match = re.match(r'bytes=(\d+)-(\d*)$', range_header)
    suffix_match = re.match(r'bytes=-(\d+)$', range_header)

    if suffix_match:
        suffix_length = int(suffix_match.group(1))
        if suffix_length <= 0:
            raise ValueError('Invalid suffix range')
        start = max(file_size - suffix_length, 0)
        return start, file_size - 1

    if not open_ended_match:
        return 0, file_size - 1

    start = int(open_ended_match.group(1))
    end = int(open_ended_match.group(2)) if open_ended_match.group(2) else file_size - 1
    if start > end:
        raise ValueError('Invalid byte range')
    return start, min(end, file_size - 1)


def collect_directory_entries(path):
    entries = []
    with os.scandir(path) as iterator:
        for entry in iterator:
            is_dir = entry.is_dir()
            is_link = entry.is_symlink()
            stat_result = entry.stat(follow_symlinks=False)
            display_name = entry.name
            link_name = entry.name

            if is_dir:
                display_name += '/'
                link_name += '/'
            elif is_link:
                display_name += '@'

            entries.append({
                'name': entry.name,
                'display_name': display_name,
                'link_name': link_name,
                'is_dir': is_dir,
                'is_link': is_link,
                'size': 0 if is_dir else stat_result.st_size,
                'stat': stat_result,
                'path': entry.path,
            })

    entries.sort(key=lambda item: item['name'].lower())
    return entries


def iter_file_chunks(file_obj, start=0, end=None, buffer_size=FILE_BUFFER_SIZE):
    file_obj.seek(start)
    remaining = None if end is None else end - start + 1

    while True:
        if remaining is not None and remaining <= 0:
            return

        read_size = buffer_size if remaining is None else min(buffer_size, remaining)
        chunk = file_obj.read(read_size)
        if not chunk:
            return

        yield chunk
        if remaining is not None:
            remaining -= len(chunk)


def build_propfind_entry(url, path, is_dir, stat_result=None, display_name=None):
    stat_result = stat_result or os.stat(path)
    display_name = display_name or os.path.basename(path.rstrip('/'))
    raw_href = url.rstrip('/') + '/' if is_dir else url
    href = escape(encode_href_path(raw_href))
    last_modified = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(stat_result.st_mtime))
    creation_date = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(stat_result.st_ctime))
    etag = f'"{hex(stat_result.st_ino)[2:]}-{int(stat_result.st_mtime)}-{stat_result.st_size}"' if not is_dir else '""'
    content_length = '' if is_dir else f'<d:getcontentlength>{stat_result.st_size}</d:getcontentlength>'
    content_type = mimetypes.guess_type(display_name.rstrip('@/'))[0] or ('httpd/unix-directory' if is_dir else 'application/octet-stream')

    return ''.join([
        '<d:response>',
        f'<d:href>{href}</d:href>',
        '<d:propstat>',
        '<d:prop>',
        '<d:resourcetype>{}</d:resourcetype>'.format('<d:collection/>' if is_dir else ''),
        content_length,
        f'<d:getlastmodified>{last_modified}</d:getlastmodified>',
        f'<d:creationdate>{creation_date}</d:creationdate>',
        f'<d:displayname>{escape(display_name)}</d:displayname>',
        f'<d:getcontenttype>{content_type}</d:getcontenttype>',
        f'<d:getetag>{etag}</d:getetag>',
        '''<d:supportedlock>
            <d:lockentry>
                <d:lockscope><d:exclusive/></d:lockscope>
                <d:locktype><d:write/></d:locktype>
            </d:lockentry>
            <d:lockentry>
                <d:lockscope><d:shared/></d:lockscope>
                <d:locktype><d:write/></d:locktype>
            </d:lockentry>
        </d:supportedlock>''',
        '</d:prop>',
        '<d:status>HTTP/1.1 200 OK</d:status>',
        '</d:propstat>',
        '</d:response>',
    ])


def iter_propfind_items(request_url, path, depth='1'):
    current_url = request_url if request_url.endswith('/') or not os.path.isdir(path) else request_url + '/'
    yield {'url': current_url, 'path': path, 'entry': None}

    if os.path.isdir(path) and depth != '0':
        for entry in collect_directory_entries(path):
            item_url = current_url.rstrip('/') + '/' + entry['name']
            if entry['is_dir']:
                item_url += '/'
            yield {'url': item_url.replace('\\', '/'), 'path': entry['path'], 'entry': entry}


def render_directory_listing_html(path, request_path, upload_enabled=False):
    entries = collect_directory_entries(path)
    full_directory = os.path.relpath(os.path.abspath(path), start=os.getcwd())
    rows = []

    if request_path != '/':
        rows.append('''
        <a class="table-row table-row-parent" href="../">
            <span class="row-name">../ 返回上一级 / Go Back</span>
            <span class="row-modified">-</span>
            <span class="row-size">-</span>
        </a>
        ''')

    for entry in entries:
        stat_result = entry['stat']
        modified = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(stat_result.st_mtime))
        size = '-' if entry['is_dir'] else format_size(entry['size'])
        icon = guess_file_icon(entry['name'], entry['is_dir'], entry['is_link'])
        rows.append(f'''
        <a class="table-row" href="{html_escape(encode_href_path(entry['link_name']), quote=True)}">
            <span class="row-name"><span class="row-icon">{html_escape(icon, quote=True)}</span><span class="row-label">{html_escape(entry['display_name'], quote=True)}</span></span>
            <span class="row-modified">{html_escape(modified, quote=True)}</span>
            <span class="row-size">{html_escape(size, quote=True)}</span>
        </a>
        ''')

    upload_form = ''
    if upload_enabled:
        upload_form = f'''
    <div class="upload-section">
        <form id="upload-form" enctype="multipart/form-data" method="post" action="{html_escape(encode_href_path(request_path), quote=True)}" onsubmit="return false;">
            <span class="upload-label">上传文件 / Upload:</span>
            <label class="upload-btn" title="选择文件上传">
                📄 选择文件
                <input type="file" name="files" multiple="" style="display:none" onchange="updateSelectionHint()">
            </label>
            <label class="upload-btn" title="选择整个目录上传（保持目录结构）">
                📁 选择目录
                <input type="file" name="files" webkitdirectory="" directory="" multiple="" style="display:none" onchange="updateSelectionHint()">
            </label>
            <button id="upload-start-btn" class="upload-start-btn" type="button" onclick="handleUpload()">开始上传 / Upload</button>
            <span id="upload-selection" class="upload-selection">未选择文件 / No file selected</span>
        </form>
    </div>
    <div id="upload-progress" class="upload-progress" style="display:none;">
        <div class="upload-progress-info">
            <span id="upload-progress-text">上传中 / Uploading...</span>
            <span id="upload-progress-percent">0%</span>
        </div>
        <div class="upload-progress-bar">
            <div id="upload-progress-fill" class="upload-progress-fill" style="width:0%;"></div>
        </div>
        <button id="upload-cancel-btn" class="upload-cancel-btn" type="button">取消 / Cancel</button>
    </div>
    <div id="upload-toast" class="upload-toast" style="display:none;">
        <div class="upload-toast-content">
            <span id="upload-toast-icon">✅</span>
            <span id="upload-toast-message">上传成功 / Upload successful</span>
        </div>
    </div>
    <div id="upload-modal" class="upload-modal" style="display:none;">
        <div class="upload-modal-content">
            <span class="upload-modal-icon">✅</span>
            <p id="upload-modal-message">上传成功 / Upload successful</p>
            <button id="upload-modal-ok" class="upload-modal-btn" type="button">确定 / OK</button>
        </div>
    </div>'''

    upload_script = ''
    if upload_enabled:
        upload_script = '''<script>
function collectSelectedFiles() {
    // 选择文件与选择目录两个控件里的内容会被一起上传（与老版本行为一致）
    var inputs = document.querySelectorAll('#upload-form input[type="file"]');
    var selected = [];
    for (var i = 0; i < inputs.length; i++) {
        var files = inputs[i].files;
        if (!files) continue;
        for (var j = 0; j < files.length; j++) {
            selected.push(files[j]);
        }
    }
    return selected;
}

function formatSize(bytes) {
    var units = ['B', 'KB', 'MB', 'GB', 'TB'];
    var value = bytes;
    var unit = 0;
    while (value >= 1024 && unit < units.length - 1) {
        value /= 1024;
        unit++;
    }
    return (unit === 0 ? value : value.toFixed(2)) + ' ' + units[unit];
}

function updateSelectionHint() {
    var hint = document.getElementById('upload-selection');
    if (!hint) return;
    var files = collectSelectedFiles();
    if (files.length === 0) {
        hint.textContent = '未选择文件 / No file selected';
        return;
    }
    var total = 0;
    for (var i = 0; i < files.length; i++) {
        total += files[i].size;
    }
    hint.textContent = '已选择 ' + files.length + ' 个文件（' + formatSize(total) + '），点击“开始上传”上传';
}

function handleUpload() {
    var files = collectSelectedFiles();
    var progressWrap = document.getElementById('upload-progress');
    var fill = document.getElementById('upload-progress-fill');
    var percentText = document.getElementById('upload-progress-percent');
    var toast = document.getElementById('upload-toast');
    var toastMsg = document.getElementById('upload-toast-message');
    var toastIcon = document.getElementById('upload-toast-icon');
    var modal = document.getElementById('upload-modal');
    var modalMsg = document.getElementById('upload-modal-message');
    var modalOk = document.getElementById('upload-modal-ok');
    var cancelBtn = document.getElementById('upload-cancel-btn');
    var form = document.getElementById('upload-form');
    var action = form.getAttribute('action') || window.location.pathname;
    var cancelled = false;

    if (files.length === 0) {
        toast.classList.add('upload-toast-error');
        toastIcon.textContent = '⚠️';
        toastMsg.textContent = '请先选择文件 / Please select files first';
        toast.style.display = 'block';
        setTimeout(function() { toast.style.display = 'none'; }, 3000);
        return;
    }

    progressWrap.style.display = 'block';
    toast.style.display = 'none';
    toast.classList.remove('upload-toast-error');

    var xhr = new XMLHttpRequest();
    var fd = new FormData();
    for (var i = 0; i < files.length; i++) {
        // 目录上传时浏览器会给出 webkitRelativePath，用它才能保留目录结构
        fd.append('files', files[i], files[i].webkitRelativePath || files[i].name);
    }

    cancelBtn.onclick = function() {
        cancelled = true;
        xhr.abort();
        progressWrap.style.display = 'none';
        fill.style.width = '0%';
        percentText.textContent = '0%';
        toast.classList.add('upload-toast-error');
        toastIcon.textContent = '⚠️';
        toastMsg.textContent = '上传已取消 / Upload cancelled';
        toast.style.display = 'block';
        setTimeout(function() { toast.style.display = 'none'; }, 3000);
    };

    xhr.upload.addEventListener('progress', function(e) {
        if (e.lengthComputable) {
            var percent = Math.round(e.loaded / e.total * 100);
            fill.style.width = percent + '%';
            percentText.textContent = percent + '%';
        }
    });

    xhr.addEventListener('load', function() {
        progressWrap.style.display = 'none';
        fill.style.width = '0%';
        percentText.textContent = '0%';
        if (xhr.status >= 200 && xhr.status < 300) {
            modalMsg.textContent = '上传成功 / Upload successful';
            modal.style.display = 'flex';
            modalOk.onclick = function() {
                modal.style.display = 'none';
                window.location.reload();
            };
        } else {
            toast.classList.add('upload-toast-error');
            toastIcon.textContent = '❌';
            toastMsg.textContent = '上传失败 / Upload failed (' + xhr.status + ')';
            toast.style.display = 'block';
            setTimeout(function() { toast.style.display = 'none'; }, 5000);
        }
    });

    xhr.addEventListener('error', function() {
        if (cancelled) return;
        progressWrap.style.display = 'none';
        toast.classList.add('upload-toast-error');
        toastIcon.textContent = '❌';
        toastMsg.textContent = '上传失败 / Upload failed';
        toast.style.display = 'block';
        setTimeout(function() { toast.style.display = 'none'; }, 5000);
    });

    xhr.addEventListener('abort', function() {
        progressWrap.style.display = 'none';
        fill.style.width = '0%';
        percentText.textContent = '0%';
    });

    xhr.open('POST', action);
    xhr.send(fd);
}
</script>'''

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(full_directory)} - 文件列表 / File List</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: Arial, sans-serif; background: #f5f7fa; color: #2a2f36; line-height: 1.5; padding: 16px; }}
.page {{ max-width: 1080px; margin: 0 auto; }}
.page-header {{ margin-bottom: 12px; padding: 10px 14px 12px; background: linear-gradient(180deg, #f4fbff 0%, #ffffff 100%); border-top: 4px solid #66CCFF; border-radius: 8px 8px 6px 6px; }}
.page-title {{ font-size: 1.05rem; font-weight: 600; word-break: break-word; }}
.page-subtitle {{ margin-top: 4px; color: #5c6a79; font-size: 0.88rem; }}
.directory-table {{ background: #fff; border: 1px solid #d9e0e7; border-radius: 6px; overflow: hidden; }}
.table-header, .table-row {{ display: grid; grid-template-columns: minmax(0, 1fr) 180px 110px; gap: 12px; align-items: center; }}
.table-header {{ padding: 8px 14px; background: #f7fbff; border-bottom: 1px solid #d7ebf7; color: #536170; font-size: 0.88rem; font-weight: 600; }}
.table-row {{ padding: 8px 14px; color: #2f5f8f; text-decoration: none; border-bottom: 1px solid #edf1f5; min-height: 42px; }}
.table-row:last-child {{ border-bottom: none; }}
.table-row:hover {{ background: #f4fbff; }}
.table-row-parent {{ font-weight: 600; }}
.row-name {{ min-width: 0; color: #222; overflow-wrap: anywhere; display: flex; align-items: center; gap: 8px; }}
.row-icon {{ width: 1.2rem; text-align: center; flex: 0 0 auto; }}
.row-label {{ min-width: 0; overflow-wrap: anywhere; }}
.row-modified, .row-size {{ color: #6c7886; font-size: 0.9rem; white-space: nowrap; }}
.row-size {{ text-align: right; }}
.footer {{ margin-top: 12px; text-align: center; font-size: 0.9rem; color: #6c7886; }}
.upload-section {{ margin-bottom: 12px; padding: 10px 14px; background: #fff; border: 1px solid #d9e0e7; border-radius: 6px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
.upload-label {{ font-size: 0.92rem; font-weight: 600; color: #2a2f36; }}
.upload-btn {{ display: inline-flex; align-items: center; gap: 4px; padding: 6px 14px; background: #e8f4fd; border: 1px solid #b8d8f0; border-radius: 5px; cursor: pointer; font-size: 0.9rem; color: #2f5f8f; transition: background 0.15s; }}
.upload-btn:hover {{ background: #d4ebfa; }}
.upload-start-btn {{ display: inline-flex; align-items: center; padding: 6px 18px; background: #66CCFF; border: 1px solid #4fb8ec; border-radius: 5px; cursor: pointer; font-size: 0.9rem; color: #fff; transition: background 0.15s; }}
.upload-start-btn:hover {{ background: #3399FF; }}
.upload-selection {{ font-size: 0.85rem; color: #6c7886; }}
@media (max-width: 700px) {{
    body {{ padding: 12px; }}
    .table-header {{ display: none; }}
    .table-row {{ grid-template-columns: minmax(0, 1fr) auto; grid-template-areas: "name size" "modified modified"; gap: 4px 10px; padding: 10px 12px; }}
    .row-name {{ grid-area: name; }}
    .row-size {{ grid-area: size; }}
    .row-modified {{ grid-area: modified; font-size: 0.82rem; }}
}}
.upload-progress {{ margin-bottom: 12px; padding: 10px 14px; background: #fff; border: 1px solid #d9e0e7; border-radius: 6px; }}
.upload-progress-info {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 0.9rem; color: #2a2f36; }}
.upload-progress-bar {{ width: 100%; height: 10px; background: #e9ecef; border-radius: 5px; overflow: hidden; }}
.upload-progress-fill {{ height: 100%; background: linear-gradient(90deg, #66CCFF, #3399FF); transition: width 0.2s ease; }}
.upload-toast {{ position: fixed; top: 20px; right: 20px; z-index: 1000; }}
.upload-toast-content {{ display: flex; align-items: center; gap: 8px; padding: 12px 18px; background: #fff; border: 1px solid #b8d8f0; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.12); font-size: 0.95rem; color: #2a2f36; }}
.upload-toast-error .upload-toast-content {{ border-color: #f5c6cb; background: #f8d7da; color: #721c24; }}
.upload-cancel-btn {{ margin-top: 8px; padding: 6px 18px; background: #fde8e8; border: 1px solid #f5b8b8; border-radius: 5px; cursor: pointer; font-size: 0.9rem; color: #c0392b; transition: background 0.15s; }}
.upload-cancel-btn:hover {{ background: #f8d0d0; }}
.upload-modal {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.4); z-index: 2000; display: flex; align-items: center; justify-content: center; }}
.upload-modal-content {{ background: #fff; border-radius: 8px; padding: 28px 36px; text-align: center; box-shadow: 0 8px 24px rgba(0,0,0,0.2); max-width: 90vw; min-width: 280px; }}
.upload-modal-icon {{ font-size: 2.4rem; display: block; margin-bottom: 10px; }}
.upload-modal-content p {{ font-size: 1.05rem; color: #2a2f36; margin-bottom: 18px; }}
.upload-modal-btn {{ padding: 8px 28px; background: #66CCFF; border: none; border-radius: 5px; cursor: pointer; font-size: 0.95rem; color: #fff; transition: background 0.15s; }}
.upload-modal-btn:hover {{ background: #3399FF; }}
</style>
</head>
<body>
<div class="page">
    <div class="page-header">
        <h2 class="page-title">{escape(full_directory)} - 文件列表 / File List</h2>
        <div class="page-subtitle">{escape(SERVER_BRAND)} {escape(SERVER_VERSION)}</div>
    </div>
    {upload_form}
    <div class="directory-table">
        <div class="table-header">
            <span>名称</span>
            <span>修改时间</span>
            <span>大小</span>
        </div>
        {''.join(rows)}
    </div>
    <div class="footer">
        <p>项目链接 / Project link: <a href="https://gitee.com/shenmo7192/momo-and-mox-tool-scripts/blob/master/server.py">Momo and Mox Tool Scripts</a></p>
    </div>
</div>
{upload_script}
</body>
</html>'''


def prepare_destination_path(handler, destination):
    return handler.translate_path(extract_url_path(destination))


def remove_existing_path(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)

def parse_multipart_body(data, boundary):
    """解析 multipart/form-data 请求体，逐个产出 (field_name, filename, file_data)。"""
    boundary_bytes = ('--' + boundary).encode()
    end_boundary = ('--' + boundary + '--').encode()

    # 按 boundary 切分，跳过开头引导部分和结尾标记
    parts = data.split(boundary_bytes)
    for part in parts[1:]:
        if part.startswith(b'--'):
            continue  # 到达 --boundary-- 结尾标记

        # 定位 headers 与 body 的分隔位置
        split_idx = part.find(b'\r\n\r\n')
        if split_idx == -1:
            continue

        headers_raw = part[:split_idx]
        body = part[split_idx + 4:]

        # 去除尾部的 \r\n
        if body.endswith(b'\r\n'):
            body = body[:-2]

        # 解析 Content-Disposition 中的 name / filename
        headers_text = headers_raw.decode('utf-8', errors='replace')
        name = ''
        filename = ''

        for line in headers_text.split('\r\n'):
            line_lower = line.lower()
            if line_lower.startswith('content-disposition:'):
                for param in line.split(';')[1:]:
                    param = param.strip()
                    if '=' not in param:
                        continue
                    key, value = param.split('=', 1)
                    key = key.strip().lower()
                    value = value.strip().strip('"')
                    if key == 'name':
                        name = value
                    elif key == 'filename':
                        filename = value

        if name:
            yield (name, filename, body)


class ForkingHTTPServer(socketserver.ForkingTCPServer):
    allow_reuse_address = 1
    address_family = socket.AF_INET6

    def server_bind(self):
        socketserver.TCPServer.server_bind(self)
        host, port = self.socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    server_version = f"{SERVER_HEADER_NAME}/{SERVER_VERSION}"
    sys_version = f"Python/{platform.python_version()}"

    _auth_enabled = False
    _credentials = ('', '')  # 存储(user, password)
    _auto_index = True  # 是否自动提供目录下的 index.html
    _upload_enabled = False  # 是否启用网页上传功能
    _error_pages_dir = None  # 自定义错误页目录（可选，读取 <code>.html）

    def _is_authorized_request(self):
        if not self._auth_enabled:
            return True

        auth_header = self.headers.get('Authorization', '')
        if not auth_header.startswith('Basic '):
            return False

        try:
            auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
            user, passwd = auth_decoded.split(':', 1)
        except Exception:
            return False

        return (user, passwd) == self._credentials



    def require_auth(f):
        """身份验证装饰器"""
        @wraps(f)
        def wrapper(self, *args, **kwargs):
            if self._is_authorized_request():
                return f(self, *args, **kwargs)

            self._send_auth_challenge()
        return wrapper

    def _send_auth_challenge(self):
        """发送401认证质询"""
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="HTTP Server", charset="UTF-8"')
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(b'<h1>Authentication Required</h1>')

    def send_error(self, code, message=None, explain=None):
        """错误响应优先使用 --error-pages 目录下的 <code>.html 自定义页面。"""
        if self._error_pages_dir:
            page_path = os.path.join(self._error_pages_dir, f'{int(code)}.html')
            try:
                with open(page_path, 'rb') as page_file:
                    body = page_file.read()
            except OSError:
                body = None

            if body is not None:
                self.log_error("code %d, message %s", code, message)
                self.send_response(code, message)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Connection', 'close')
                self.end_headers()
                if self.command != 'HEAD' and body:
                    self.wfile.write(body)
                return

        super().send_error(code, message, explain)

    def do_GET(self):
        """处理目录和文件请求：目录请求生成索引，文件请求下载"""
        filepath = self.translate_path(extract_url_path(self.path))

        # 如果请求的是一个目录，优先检查 index.html
        if os.path.isdir(filepath):
            index = os.path.join(filepath, 'index.html')
            if self._auto_index and os.path.exists(index):
                filepath = index  # 存在 index.html 则提供该文件
            else:
                return self.list_directory(filepath)  # 否则列出目录内容
        
        # 处理文件请求
        if not os.path.exists(filepath):
            self.send_error(404, "File not found")
            return

        try:
            file_size = os.path.getsize(filepath)
            mime_type, _ = mimetypes.guess_type(filepath)
            if not mime_type:
                mime_type = "application/octet-stream"

            # 文本类文件默认使用 UTF-8 编码
            TEXT_MIMES = {
                'text/plain', 'text/html', 'text/css', 'text/xml', 'text/javascript',
                'text/csv', 'text/markdown', 'text/x-python', 'text/x-c', 'text/x-shellscript',
                'application/javascript', 'application/json', 'application/xml',
                'application/xhtml+xml', 'image/svg+xml',
            }
            if mime_type in TEXT_MIMES or mime_type.startswith('text/'):
                if 'charset' not in mime_type.lower():
                    mime_type += '; charset=utf-8'

            range_header = self.headers.get("Range")
            if range_header:
                try:
                    start, end = parse_range_header(range_header, file_size)
                except ValueError:
                    self.send_error(416, "Requested Range Not Satisfiable")
                    return

                if start >= file_size:
                    self.send_error(416, "Requested Range Not Satisfiable")
                    return

                self.send_response(206)
                self.send_header("Content-Type", mime_type)
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(end - start + 1))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()

                with open(filepath, "rb") as f:
                    for chunk in iter_file_chunks(f, start=start, end=end):
                        self.wfile.write(chunk)
            else:
                self.send_response(200)
                self.send_header("Content-Type", mime_type)
                self.send_header("Content-Length", str(file_size))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()

                with open(filepath, "rb") as file:
                    for chunk in iter_file_chunks(file):
                        self.wfile.write(chunk)
        except Exception as e:
            self.send_error(500, f"Internal Server Error: {str(e)}")


    def do_POST(self):
        """处理文件/目录上传（仅当 --upload 启用时生效）。"""
        if not self._upload_enabled:
            self.send_error(405, "Method Not Allowed")
            return

        content_type = self.headers.get('Content-Type', '')
        if 'multipart/form-data' not in content_type:
            self.send_error(400, "Expected multipart/form-data")
            return

        # 提取 boundary
        boundary = None
        for part in content_type.split(';'):
            part = part.strip()
            if part.startswith('boundary='):
                boundary = part.split('=', 1)[1].strip('"')
                break

        if not boundary:
            self.send_error(400, "Missing boundary")
            return

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        # 确定上传目标目录
        request_path = extract_url_path(self.path)
        target_path = self.translate_path(request_path)
        if not os.path.isdir(target_path):
            target_path = os.path.dirname(target_path)

        uploaded_count = 0
        for _name, filename, data in parse_multipart_body(body, boundary):
            if not filename:
                continue

            # 规范化文件名，防止路径穿越
            safe_name = filename.replace('\\', '/')
            dest_path = os.path.normpath(os.path.join(target_path, safe_name))
            # 安全检查：确保最终路径在目标目录下
            if not dest_path.startswith(os.path.normpath(target_path) + os.sep) and dest_path != os.path.normpath(target_path):
                continue

            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, 'wb') as f:
                f.write(data)
            uploaded_count += 1

        # 上传完成后重定向回当前目录
        self.send_response(303)
        self.send_header('Location', encode_href_path(request_path))
        self.end_headers()

    def send_head(self):
        """Override the default method to handle Range requests."""
        path = self.translate_path(extract_url_path(self.path))
        
        if os.path.isdir(path):
            index = os.path.join(path, 'index.html')
            if self._auto_index and os.path.exists(index):
                path = index  # Serve index.html if it exists
            else:
                return self.list_directory(path)  # List directory if no index.html
    
        try:
            file = open(path, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return None

        file_size = os.path.getsize(path)
        range_header = self.headers.get('Range')
    
        if range_header:
            try:
                start, end = parse_range_header(range_header, file_size)
            except ValueError:
                self.send_response(416, "Requested Range Not Satisfiable")
                self.send_header("Content-Range", f"bytes */{file_size}")
                self.end_headers()
                return None

            if start >= file_size:
                self.send_response(416, "Requested Range Not Satisfiable")
                self.send_header("Content-Range", f"bytes */{file_size}")
                self.end_headers()
                return None

            self.send_response(206)
            self.send_header("Content-Type", self.guess_type(path))
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Content-Length", str(end - start + 1))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            file.close()
            return None
    
        # Default response when no Range request is made (serve the full file)
        self.send_response(200)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
    
        return file
    


    def list_directory(self, path):
        if not self._is_authorized_request():
            self._send_auth_challenge()
            return None

        try:
            html = render_directory_listing_html(path, self.path, upload_enabled=self._upload_enabled)
        except OSError:
            self.send_error(404, "No permission to list directory")
            return None

        # Encode the HTML content
        encoded = html.encode('utf-8', 'surrogateescape')
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()

        # Write the encoded HTML directly to wfile
        self.wfile.write(encoded)

    def format_size(self, size):
        return format_size(size)
for method in ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'OPTIONS']:
    if hasattr(CustomHTTPRequestHandler, 'do_' + method):
        original_method = getattr(CustomHTTPRequestHandler, 'do_' + method)
        setattr(CustomHTTPRequestHandler, 'do_' + method, 
                CustomHTTPRequestHandler.require_auth(original_method))

class WebDAVRequestHandler(CustomHTTPRequestHandler):
    _auth_enabled = False
    _credentials = ('', '')  # 存储(user, password)
    


    def require_auth(f):
        """身份验证装饰器"""
        @wraps(f)
        def wrapper(self, *args, **kwargs):
            if not self._auth_enabled:
                return f(self, *args, **kwargs)
                
            auth_header = self.headers.get('Authorization', '')
            if not auth_header.startswith('Basic '):
                self._send_auth_challenge()
                return

            try:
                # 解析Base64凭证
                auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
                user, passwd = auth_decoded.split(':', 1)
                if (user, passwd) == self._credentials:
                    return f(self, *args, **kwargs)
            except Exception:
                pass
            
            self._send_auth_challenge()
        return wrapper

    def _send_auth_challenge(self):
        """发送401认证质询"""
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Erotica WebDAV Server", charset="UTF-8"')
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(b'<h1>Authentication Required</h1>')


    def do_OPTIONS(self):
        """确保OPTIONS响应包含PROPPATCH支持"""
        self.send_response(200)
        self.send_header('Allow', ', '.join([
            'OPTIONS', 'GET', 'HEAD', 'POST', 
            'PUT', 'DELETE', 'MKCOL', 'PROPFIND',
            'PROPPATCH', 'LOCK', 'UNLOCK',       # 新增PROPPATCH支持
            'MOVE', 'COPY'
        ]))
        self.send_header('DAV', '1, 2')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_PROPPATCH(self):
        """处理PROPPATCH请求以实现WebDAV属性修改"""
        path = self.translate_path(extract_url_path(self.path))
        if not os.path.exists(path):
            self.send_error(404, "File not found")
            return

        # 读取请求XML内容
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            raw_xml = self.rfile.read(content_length)
            root = ET.fromstring(raw_xml)
        except (ValueError, ET.ParseError) as e:
            self.send_error(400, f"Invalid XML: {str(e)}")
            return
        
        # 验证XML根元素
        if root.tag != '{DAV:}propertyupdate':
            self.send_error(400, "Root element must be propertyupdate")
            return

        # 构造多状态响应XML
        multistatus = ET.Element('{DAV:}multistatus')
        response = ET.SubElement(multistatus, '{DAV:}response')
        href = ET.SubElement(response, '{DAV:}href')
        href.text = self.path

        # 处理属性更新请求
        propstat = ET.SubElement(response, '{DAV:}propstat')
        prop = ET.SubElement(propstat, '{DAV:}prop')
        status = ET.SubElement(propstat, '{DAV:}status')
        
        result = {'code': 200, 'message': 'OK'}
        
        # 遍历所有属性操作
        for operation in root:
            if operation.tag == '{DAV:}set':
                target_prop = operation.find('.//{DAV:}prop')
                for elem in list(target_prop):
                    status_code = self._process_property(path, elem)
                    result['code'] = max(result['code'], status_code)
            elif operation.tag == '{DAV:}remove':
                # 属性移除暂不支持（示例代码）
                result['code'] = 403
                ET.SubElement(prop, elem.tag)  # 记录失败属性

        # 设置最终响应状态
        status.text = f'HTTP/1.1 {result["code"]} {result["message"]}'
        
        # 生成XML响应
        response_xml = ET.tostring(multistatus, encoding='utf-8', method='xml')
        self.send_response(207)
        self.send_header('Content-Type', 'text/xml; charset="utf-8"')
        self.send_header('Content-Length', len(response_xml))
        self.end_headers()
        self.wfile.write(response_xml)

    def _process_property(self, path, elem):
        """处理单个属性（返回HTTP状态码）"""
        if elem.tag == '{DAV:}displayname':
            # 在此不做文件系统的重命名，仅表示 displayname 已接收
            return 200  # 只表示 displayname 更新成功
        elif elem.tag == '{DAV:}getlastmodified':
            # 返回成功
            return 200
        # 对于其他未实现的属性返回501
        return 501



    
    def do_PROPFIND(self):
        path = self.translate_path(extract_url_path(self.path))
        if not os.path.exists(path):
            self.send_error(404, "File not found")
            return

        depth = self.headers.get('Depth', '1')
        
        # 生成XML内容
        xml_content = []
        xml_content.append('<?xml version="1.0" encoding="utf-8"?>')
        xml_content.append('<d:multistatus xmlns:d="DAV:">')

        for item in iter_propfind_items(extract_url_path(self.path), path, depth=depth):
            entry = item.get('entry')
            if entry is None:
                xml_content.append(build_propfind_entry(item['url'], item['path'], os.path.isdir(item['path'])))
            else:
                xml_content.append(build_propfind_entry(
                    item['url'],
                    item['path'],
                    entry['is_dir'],
                    stat_result=entry['stat'],
                    display_name=entry['name'],
                ))

        xml_content.append('</d:multistatus>')
        full_xml = '\n'.join(xml_content).encode('utf-8')
        
        # 发送响应
        self.send_response(207)
        self.send_header('Content-Type', 'text/xml; charset="utf-8"')
        self.send_header('Content-Length', len(full_xml))
        self.end_headers()
        self.wfile.write(full_xml)

    def _add_propfind_response(self, xml_content, url, path):
        """生成完整的PROPFIND响应XML（含所有标准属性）"""
        xml_content.append(build_propfind_entry(url, path, os.path.isdir(path)))



    # WebDAV MKCOL method to create a collection (directory)
    def do_MKCOL(self):
        path = self.translate_path(extract_url_path(self.path))
        if os.path.exists(path):
            self.send_error(405, "Method Not Allowed")
            return

        os.makedirs(path)
        self.send_response(201)
        self.end_headers()

    # WebDAV DELETE method to delete a file or directory
    def do_DELETE(self):
        path = self.translate_path(extract_url_path(self.path))
        if not os.path.exists(path):
            self.send_error(404, "File not found")
            return

        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

        self.send_response(204)
        self.end_headers()

    def do_PUT(self):
        """
        处理 WebDAV 上传（PUT方法），支持:
          1) 非分块 (Content-Length)
          2) 分块 (Transfer-Encoding: chunked)
        """
        path = self.translate_path(extract_url_path(self.path))
        # 确保上传目录存在
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # 判断是否是 chunked 方式
        transfer_encoding = self.headers.get('Transfer-Encoding', '').lower()
        content_length = self.headers.get('Content-Length')

        try:
            if 'chunked' in transfer_encoding:
                # --- Chunked 方式 ---
                self._handle_chunked_put(path)
            elif content_length is not None:
                # --- 普通方式（Content-Length） ---
                self._handle_content_length_put(path, int(content_length))
            else:
                # 两种都没有，就会报错
                self.send_error(400, "Missing Content-Length or Transfer-Encoding: chunked")
                return

            self.send_response(201, "Created")
            self.end_headers()
        except Exception as e:
            self.send_error(500, f"Internal Server Error: {str(e)}")

    def _handle_content_length_put(self, filepath, content_length):
        """基于 Content-Length 的上传"""
        with open(filepath, "wb") as f:
            remaining = content_length
            while remaining > 0:
                chunk_size = min(FILE_BUFFER_SIZE, remaining)
                data = self.rfile.read(chunk_size)
                if not data:
                    break
                f.write(data)
                remaining -= len(data)

    def _handle_chunked_put(self, filepath):
        """基于 Transfer-Encoding: chunked 的上传"""
        with open(filepath, "wb") as f:
            while True:
                # 读取一行，获取 chunk size（十六进制）
                chunk_size_line = self.rfile.readline().strip()
                if not chunk_size_line:
                    # 空行或者异常
                    break

                # 转成10进制
                try:
                    chunk_size = int(chunk_size_line, 16)
                except ValueError:
                    # 如果无法解析为16进制，客户端传输格式不对
                    raise ValueError("Invalid chunk size header")

                if chunk_size == 0:
                    # chunk_size = 0 表示结束，还要读掉可能的 trailer 部分
                    # 读取并丢弃剩下的header（直到遇到空行）
                    _ = self.rfile.readline()
                    break

                # 读取 chunk_size 字节的数据
                chunk_data = self.rfile.read(chunk_size)
                if not chunk_data:
                    break
                f.write(chunk_data)

                # chunk 后面还有一个空行(CRLF)需要读掉
                _ = self.rfile.readline()


        
    
    locks = {}  # Dictionary to store lock information

    # WebDAV LOCK method
    def do_LOCK(self):
        path = self.translate_path(extract_url_path(self.path))
        
        # If the resource is already locked, return an error
        if path in self.locks:
            self.send_response(423)  # 423 Locked
            self.end_headers()
            return

        # Generate a lock token and store it
        lock_token = str(uuid.uuid4())
        self.locks[path] = {
            'token': lock_token,
            'owner': self.headers.get('Owner'),  # Optional owner info from client
            'timeout': 3600  # Example timeout in seconds
        }

        # Send lock response
        self.send_response(200)
        self.send_header('Content-Type', 'application/xml; charset="utf-8"')
        self.send_header('Lock-Token', f'<urn:uuid:{lock_token}>')
        self.end_headers()

        lock_response = f'''<?xml version="1.0" encoding="utf-8"?>
        <d:prop xmlns:d="DAV:">
            <d:lockdiscovery>
                <d:activelock>
                    <d:locktoken>
                        <d:href>urn:uuid:{lock_token}</d:href>
                    </d:locktoken>
                </d:activelock>
            </d:lockdiscovery>
        </d:prop>'''
        self.wfile.write(lock_response.encode('utf-8'))

    # WebDAV UNLOCK method
    def do_UNLOCK(self):
        path = self.translate_path(extract_url_path(self.path))
        lock_token = self.headers.get('Lock-Token')

        # Verify that the token matches
        if path in self.locks and self.locks[path]['token'] == lock_token.strip('<>'):
            del self.locks[path]  # Remove the lock
            self.send_response(204)  # No Content
        else:
            self.send_response(400)  # Bad Request
        self.end_headers()
    # WebDAV MOVE method
    def do_MOVE(self):
        path = self.translate_path(extract_url_path(self.path))
        if not os.path.exists(path):
            self.send_error(404, "File not found")
            return

    # 解析 Destination 头中的路径部分
        destination = self.headers.get('Destination')
        if not destination:
            self.send_error(400, "Bad Request: Missing Destination header")
            return

        # 提取目标路径并解码
        full_dest_path = prepare_destination_path(self, destination)
    # 检查目标路径是否已存在及是否覆盖
        overwrite = self.headers.get('Overwrite', 'T').upper()
        original_dest_exists = os.path.exists(full_dest_path)

        if original_dest_exists:
            if overwrite == 'F':
                self.send_error(412, "Precondition Failed: Destination exists and Overwrite is False")
                return
            else:
                # 如果目标路径已存在且需要覆盖，删除目标路径
                try:
                    remove_existing_path(full_dest_path)
                except Exception as e:
                    self.send_error(500, f"Failed to remove existing destination: {str(e)}")
                    return      



        try:
            shutil.move(path, full_dest_path)  # normal file move
            
        # Response code depending on whether the destination was overwritten or not
            response_code = 204 if original_dest_exists else 201
            self.send_response(response_code)
            self.end_headers()
        except Exception as e:
            self.send_error(500, f"Move failed: {str(e)}")  


    
# WebDAV COPY method
    def do_COPY(self):
        path = self.translate_path(extract_url_path(self.path))
        if not os.path.exists(path):
            self.send_error(404, "File not found")
            return
        destination = self.headers.get('Destination')
        overwrite = self.headers.get('Overwrite', 'T').upper()
    
        if not destination:
            self.send_error(400, "Bad Request: Missing Destination header")
            return
    
        dest_path = prepare_destination_path(self, destination)
        original_dest_exists = os.path.exists(dest_path)
    
        if original_dest_exists:
            if overwrite == 'F':
                self.send_error(412, "Precondition Failed: Destination exists and Overwrite is False")
                return
            else:
            # Overwrite existing destination
                remove_existing_path(dest_path)

        try:
            if os.path.isdir(path):
                shutil.copytree(path, dest_path)
            else:
                shutil.copy2(path, dest_path)
        except FileNotFoundError:
            self.send_error(409, "Conflict: Destination parent does not exist")
            return
        except Exception as e:
            self.send_error(500, f"Copy failed: {str(e)}")
            return

        self.send_response(204 if original_dest_exists else 201)
        self.end_headers()

auth_required_methods = [
    'GET', 'OPTIONS' ,'PROPFIND', 'PROPPATCH', 'MKCOL', 
    'DELETE', 'MOVE', 'COPY',
    'LOCK', 'UNLOCK', 'PUT', 'POST'
]

for method in auth_required_methods:
    if hasattr(WebDAVRequestHandler, 'do_' + method):
        setattr(WebDAVRequestHandler, 'do_' + method, 
                WebDAVRequestHandler.require_auth(getattr(WebDAVRequestHandler, 'do_' + method))
        )
    
def apply_brand(brand):
    """把命令行指定的品牌名应用到目录页面和 HTTP Server 头。"""
    global SERVER_BRAND, SERVER_HEADER_NAME

    if not brand:
        return

    SERVER_BRAND = brand
    SERVER_HEADER_NAME = re.sub(r'[^0-9A-Za-z]+', '-', brand).strip('-') or 'WebServer'
    for handler_class in (CustomHTTPRequestHandler, WebDAVRequestHandler):
        handler_class.server_version = f'{SERVER_HEADER_NAME}/{SERVER_VERSION}'


def create_smb_server(port, address, directory, share_name, credentials=None, read_only=False):
    """创建（但不启动）impacket 的 SMB 服务器实例。

    impacket 是可选依赖：未安装时抛出 RuntimeError，由调用方给出安装提示。
    注意：SMB 默认端口 445 属于特权端口，需要 root 权限才能监听。
    """
    try:
        from impacket import smbserver, ntlm
    except ImportError as exc:
        raise RuntimeError(
            'SMB 模式需要 impacket（Debian/GXDE: sudo apt install python3-impacket，'
            '其他系统: pip install impacket）'
        ) from exc

    shared_path = os.path.abspath(directory)
    if not os.path.isdir(shared_path):
        raise RuntimeError(f'共享目录不存在: {shared_path}')

    listen_address = address or '0.0.0.0'
    server = smbserver.SimpleSMBServer(
        listenAddress=listen_address,
        listenPort=port,
        ipv6=':' in listen_address,
    )
    server.setSMB2Support(True)

    if credentials:
        user, password = credentials
        server.addCredential(user, 0, ntlm.compute_lmhash(password), ntlm.compute_nthash(password))

    server.addShare(
        resolve_share_name(share_name, shared_path),
        shared_path,
        f'{SERVER_BRAND} {SERVER_VERSION}',
        readOnly='yes' if read_only else 'no',
    )
    return server


def print_smb_tips(port, address, directory, share_name, read_only=False):
    print("="*50)
    print(f"Starting server on:")
    print(f"  Address : {address or '0.0.0.0'}")
    print(f"  Port    : {port}")
    print(f"  Root    : {os.path.abspath(directory)}")
    print(f"  Share   : {share_name}{' (read only)' if read_only else ''}")
    print(f"  Protocol: SMB2/3 (impacket)")
    print("="*50)
    print('-------->> Available IP addresses:')
    for interface, ip, version in list_all_ips():
        if ':' in ip:
            # IPv6 的 SMB 地址需要方括号，这里只提示 IPv4，避免误导
            continue
        host = ip if port == SMB_DEFAULT_PORT else f'{ip}:{port}'
        print(f"-------->> {interface} ({version}): smb://{host}/{share_name}")
    print("="*50)


def start_smb_server(port, address, directory, share_name, credentials=None, read_only=False):
    """启动 SMB 服务，返回进程退出码。"""
    resolved_share = resolve_share_name(share_name, directory)

    try:
        server = create_smb_server(
            port,
            address,
            directory,
            share_name,
            credentials=credentials,
            read_only=read_only,
        )
    except RuntimeError as exc:
        print(f"错误：{exc}")
        return 1
    except PermissionError:
        print(f"错误：无法监听端口 {port}（SMB 默认端口 {SMB_DEFAULT_PORT} 需要 root 权限）")
        print("      可以用 sudo 运行，或改用 -p http / -p webdav，")
        print("      也可以换一个高位端口，再用 smb://主机:端口/共享名 访问。")
        return 1
    except OSError as exc:
        print(f"错误：无法启动 SMB 服务：{exc}")
        return 1

    print_smb_tips(port, address, directory, resolved_share, read_only=read_only)

    try:
        server.start()
    except KeyboardInterrupt:
        print("")
        print("Stopping SMB server, bye.")
    return 0


def start_http_server(port, address, handler_class, server_class, directory):
    if address == '':
        address = '::'
    server_address = (address, port)

    httpd = server_class(server_address, handler_class)

    # 打印启动信息，显示正确的 handler 类名
    print("="*50)
    print(f"Starting server on:")
    print(f"  Address : {address}")
    print(f"  Port    : {port}")
    print(f"  Root    : {directory}")
    print(f"  Handler : {handler_class.__name__}")
    print(f'-------->> Now, listening at port {port}...')

    # List all IP addresses
    print('-------->> Available IP addresses:')
    for interface, ip, version in list_all_ips():
        print(f"-------->> {interface} ({version}): http://{ip}:{port}")
    print("="*50)

    httpd.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run a simple HTTP, WebDAV or SMB server.')
    parser.add_argument('port', type=int, nargs='?', default=8000, help=f'Port to listen on (default: 8000, SMB usually uses {SMB_DEFAULT_PORT})')
    parser.add_argument('-b', '--bind', default='', help='Address to bind to (default: 0.0.0.0)')
    parser.add_argument('-d', '--directory', default='.', help='Directory to serve (default: current directory)')
    parser.add_argument('-p', '--protocol', choices=['http', 'webdav', 'smb'], default='http', help='Protocol version (default: http)')
    parser.add_argument('--cgi', action='store_true', help='Enable CGI')
    parser.add_argument('--auth', help='Authentication credentials (user:pass)')
    parser.add_argument('--no-auto-index', action='store_true', help='Disable automatic serving of index.html for directories')
    parser.add_argument('--upload', action='store_true', help='Enable file/directory upload in the web interface')
    parser.add_argument('--brand', default=SERVER_BRAND, help=f'Brand name shown in the directory page and the Server header (default: {SERVER_BRAND})')
    parser.add_argument('--error-pages', help='Directory with custom <code>.html error pages (for example 403.html / 404.html)')
    parser.add_argument('--smb-share', help='SMB share name (default: name of the shared directory)')
    parser.add_argument('--smb-readonly', action='store_true', help='Expose the SMB share as read only')

    args = parser.parse_args()

    apply_brand(args.brand)

    if args.error_pages:
        CustomHTTPRequestHandler._error_pages_dir = os.path.abspath(args.error_pages)

    # 处理认证参数
    if args.auth:
        if ':' not in args.auth:
            print("错误：认证参数格式应为 user:password")
            exit(1)
        if args.protocol == 'http':
            CustomHTTPRequestHandler._credentials = tuple(args.auth.split(':', 1))
            CustomHTTPRequestHandler._auth_enabled = True
        elif args.protocol == 'webdav':
            WebDAVRequestHandler._credentials = tuple(args.auth.split(':', 1))
            WebDAVRequestHandler._auth_enabled = True

    if args.protocol == 'http':
        # Change working directory to the one specified by the -d option
        os.chdir(args.directory)

        if args.cgi:
            handler_class = http.server.CGIHTTPRequestHandler
            handler_class.cgi_directories = {"/cgi-bin": "/cgi-bin"}  # Adjust as needed
        else:
            handler_class = CustomHTTPRequestHandler

        CustomHTTPRequestHandler._auto_index = not args.no_auto_index
        CustomHTTPRequestHandler._upload_enabled = args.upload

        start_http_server(args.port, address=args.bind, handler_class=handler_class, server_class=ForkingHTTPServer, directory=args.directory)

    elif args.protocol == 'webdav':
        os.chdir(args.directory)
        WebDAVRequestHandler._auto_index = not args.no_auto_index
        WebDAVRequestHandler._upload_enabled = args.upload
        start_http_server(args.port, address=args.bind, handler_class=WebDAVRequestHandler, server_class=ForkingHTTPServer, directory=args.directory)

    elif args.protocol == 'smb':
        sys.exit(start_smb_server(
            args.port,
            args.bind,
            args.directory,
            args.smb_share,
            credentials=tuple(args.auth.split(':', 1)) if args.auth else None,
            read_only=args.smb_readonly,
        ))
