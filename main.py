#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# encoding =utf-8

"""
modifyDate: 20120808 ~ 20120810
原作者为：bones7456, http://li2z.cn/
修改者为：decli@qq.com
修改者为:SuperEndermanSM http://www.shenmo.tech:666/
v1.3 全端口支持
v1.2，changeLog：
+: 文件日期/时间/颜色显示、多线程支持、主页跳转
-: 解决不同浏览器下上传文件名乱码问题：仅IE，其它浏览器暂时没处理。
-: 一些路径显示的bug，主要是 cgi.escape() 转义问题
?: notepad++ 下直接编译的server路径问题
"""

"""
  简介：这是一个 python 写的轻量级的文件共享服务器（基于内置的SimpleHTTPServer模块），
  支持文件上传下载，只要你安装了python（建议版本2.6~2.7，不支持3.x），
  然后去到想要共享的目录下，执行：
    python SimpleHTTPServerWithUpload.py 1234    
  其中1234为你指定的端口号，如不写，默认为 8080
  然后访问 http://localhost:1234 即可，localhost 或者 1234 请酌情替换。
"""

"""
Simple HTTP Server With Upload.
  
This module builds on BaseHTTPServer by implementing the standard GET
and HEAD requests in a fairly straightforward manner.
  
"""

import platform
import sys
import urllib2
import urllib
import os
import time
import re
import mimetypes
import shutil
import cgi
import threading
from SocketServer import ThreadingMixIn
import BaseHTTPServer
import posixpath
__version__ = "0.1"
__all__ = ["SimpleHTTPRequestHandler"]
__author__ = "bones7456"
__home_page__ = ""
favicon="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAJhSURBVFhH7dZLiE5hHMfxl3EXmgbJJUTERGoWNhZkIYWxsKHYSCxQikxC2dizVZpBCoXcksvCYgpJFIlCUhYUcsn98v1OPfU473PGvGfedyblV5+aOXPOeZ45z/+5lP6nl1KHoeGHnkxfzEALZqIdPZI+mIa9eIZf2ICax4anYA8e4yds/A3momax4UnYiUcIDQd3MRI1yQRsxwP8QNxwcBjWQ1UzDltwD3kNB5tRtYzBJtzBd8QNfcGnzLV3mIduZxSs5FvINhwauo2P0TXdh50unAasxXV8Q/zy4CWOIEy52DH0Q8Wpxxq4eHxF9sXBc+zCjehabCsqygisxDU4pqmXBg+xGqeia7EPWIAuZRhW4Ao+I/XCmOO9EPuRnfeBHXS2dBo3ieW4iGwF5/HrzMY2dPaVTqI/khmCJTiLbOXm8T89A1c9h+ktUvcFO1CWQViM03CMUg+mOPUOYTTmw+JL3Rf4NRehLFNh4++RejDFz7wPw9EI1/bUfbEnmIiyuHH4Incn1/DLeIW8QvIr7cZgjMUlpO7LOoeB+GushTlwvXZ8XyCs7a+xERaSnW5FtqE8bskVxx57glkHd7BVcBcbAA8XqSU4xSFbim7F45vDZabDla4r64Nckj2YlKWSM6EvCnGjOY+rcIgcEheuvDG+iQPwi/2RoodSC9ZFx5qwuA7iAsKxy85YpOGLnYALW9XiSulOaGM22oQQi3gW1uM4PJItQ1XTjLAVH0XHGT8Rh2Y88v5eOHbAqfkUTtnCKXowdGw9E7jzeRQrnKId8DlnQFvHb72QybDQ/vWUSr8BOTAu01/y3KsAAAAASUVORK5CYII="
folderIcon='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rIiB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiI+CiAgPGRlZnM+CiAgICA8ZmlsdGVyIGlkPSJmb2xkZXItMzItYSIgd2lkdGg9IjEyOC42JSIgaGVpZ2h0PSIxMzMuMyUiIHg9Ii0xNC4zJSIgeT0iLTE2LjclIiBmaWx0ZXJVbml0cz0ib2JqZWN0Qm91bmRpbmdCb3giPgogICAgICA8ZmVPZmZzZXQgZHk9IjEiIGluPSJTb3VyY2VBbHBoYSIgcmVzdWx0PSJzaGFkb3dPZmZzZXRPdXRlcjEiLz4KICAgICAgPGZlR2F1c3NpYW5CbHVyIGluPSJzaGFkb3dPZmZzZXRPdXRlcjEiIHJlc3VsdD0ic2hhZG93Qmx1ck91dGVyMSIgc3RkRGV2aWF0aW9uPSIuNSIvPgogICAgICA8ZmVDb21wb3NpdGUgaW49InNoYWRvd0JsdXJPdXRlcjEiIGluMj0iU291cmNlQWxwaGEiIG9wZXJhdG9yPSJvdXQiIHJlc3VsdD0ic2hhZG93Qmx1ck91dGVyMSIvPgogICAgICA8ZmVDb2xvck1hdHJpeCBpbj0ic2hhZG93Qmx1ck91dGVyMSIgcmVzdWx0PSJzaGFkb3dNYXRyaXhPdXRlcjEiIHZhbHVlcz0iMCAwIDAgMCAwICAgMCAwIDAgMCAwICAgMCAwIDAgMCAwICAwIDAgMCAwLjE1IDAiLz4KICAgICAgPGZlTWVyZ2U+CiAgICAgICAgPGZlTWVyZ2VOb2RlIGluPSJzaGFkb3dNYXRyaXhPdXRlcjEiLz4KICAgICAgICA8ZmVNZXJnZU5vZGUgaW49IlNvdXJjZUdyYXBoaWMiLz4KICAgICAgPC9mZU1lcmdlPgogICAgPC9maWx0ZXI+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImZvbGRlci0zMi1jIiB4MT0iNTAlIiB4Mj0iNTAlIiB5MT0iMCUiIHkyPSIzNy45NjglIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iIzAwQjhGRiIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiMyRTVERkYiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8cGF0aCBpZD0iZm9sZGVyLTMyLWIiIGQ9Ik0xNS41LDEuNSBMMTUuNSwxLjUgQzE1Ljc5ODU5NTEsMi4zOTU3ODU0NCAxNi42MzY4OTgxLDMgMTcuNTgxMTM4OCwzIEwyNC41LDMgQzI2LjQzMjk5NjYsMyAyOCw0LjU2NzAwMzM4IDI4LDYuNSBMMjgsMjAuNSBDMjgsMjIuNDMyOTk2NiAyNi40MzI5OTY2LDI0IDI0LjUsMjQgTDMuNSwyNCBDMS41NjcwMDMzOCwyNCAtNC4yMzk1ODQwM2UtMTQsMjIuNDMyOTk2NiAtNC4yNjMyNTY0MWUtMTQsMjAuNSBMLTQuMjYzMjU2NDFlLTE0LDMuNSBDLTQuMjg2OTI4OGUtMTQsMS41NjcwMDMzOCAxLjU2NzAwMzM4LC0yLjgwNjY2MjM3ZS0xNCAzLjUsLTIuODQyMTcwOTRlLTE0IEwxMy40MTg4NjEyLC0yLjY2NDUzNTI2ZS0xNCBDMTQuMzYzMTAxOSwtMi43NjU3NDYxMWUtMTQgMTUuMjAxNDA0OSwwLjYwNDIxNDU2NCAxNS41LDEuNSBaIi8+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImZvbGRlci0zMi1nIiB4MT0iNTAlIiB4Mj0iNTAlIiB5MT0iMCUiIHkyPSIxMS43OTYlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iI0ZGRiIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiNDRUY1RkYiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8cmVjdCBpZD0iZm9sZGVyLTMyLWYiIHdpZHRoPSIyNiIgaGVpZ2h0PSIxMCIgeD0iMSIgeT0iNCIgcng9IjIuMjUiLz4KICAgIDxmaWx0ZXIgaWQ9ImZvbGRlci0zMi1lIiB3aWR0aD0iMTExLjUlIiBoZWlnaHQ9IjEzMCUiIHg9Ii01LjglIiB5PSItMTUlIiBmaWx0ZXJVbml0cz0ib2JqZWN0Qm91bmRpbmdCb3giPgogICAgICA8ZmVPZmZzZXQgaW49IlNvdXJjZUFscGhhIiByZXN1bHQ9InNoYWRvd09mZnNldE91dGVyMSIvPgogICAgICA8ZmVHYXVzc2lhbkJsdXIgaW49InNoYWRvd09mZnNldE91dGVyMSIgcmVzdWx0PSJzaGFkb3dCbHVyT3V0ZXIxIiBzdGREZXZpYXRpb249Ii41Ii8+CiAgICAgIDxmZUNvbG9yTWF0cml4IGluPSJzaGFkb3dCbHVyT3V0ZXIxIiB2YWx1ZXM9IjAgMCAwIDAgMCAgIDAgMCAwIDAgMCAgIDAgMCAwIDAgMCAgMCAwIDAgMC4yIDAiLz4KICAgIDwvZmlsdGVyPgogICAgPGZpbHRlciBpZD0iZm9sZGVyLTMyLWgiIHdpZHRoPSIxMTEuNSUiIGhlaWdodD0iMTMwJSIgeD0iLTUuOCUiIHk9Ii0xNSUiIGZpbHRlclVuaXRzPSJvYmplY3RCb3VuZGluZ0JveCI+CiAgICAgIDxmZU9mZnNldCBkeT0iMSIgaW49IlNvdXJjZUFscGhhIiByZXN1bHQ9InNoYWRvd09mZnNldElubmVyMSIvPgogICAgICA8ZmVDb21wb3NpdGUgaW49InNoYWRvd09mZnNldElubmVyMSIgaW4yPSJTb3VyY2VBbHBoYSIgazI9Ii0xIiBrMz0iMSIgb3BlcmF0b3I9ImFyaXRobWV0aWMiIHJlc3VsdD0ic2hhZG93SW5uZXJJbm5lcjEiLz4KICAgICAgPGZlQ29sb3JNYXRyaXggaW49InNoYWRvd0lubmVySW5uZXIxIiB2YWx1ZXM9IjAgMCAwIDAgMSAgIDAgMCAwIDAgMSAgIDAgMCAwIDAgMSAgMCAwIDAgMC41IDAiLz4KICAgIDwvZmlsdGVyPgogICAgPHJhZGlhbEdyYWRpZW50IGlkPSJmb2xkZXItMzItaSIgY3g9IjUwJSIgY3k9IjAlIiByPSIxMTcuNjEzJSIgZng9IjUwJSIgZnk9IjAlIiBncmFkaWVudFRyYW5zZm9ybT0ibWF0cml4KC4wNjE3MSAuOTk1MzggLS42Mzk4OSAuMDk2IC40NyAtLjQ5OCkiPgogICAgICA8c3RvcCBvZmZzZXQ9IjAlIiBzdG9wLWNvbG9yPSIjNDhENUZGIi8+CiAgICAgIDxzdG9wIG9mZnNldD0iMTAwJSIgc3RvcC1jb2xvcj0iIzAwODNGNiIvPgogICAgPC9yYWRpYWxHcmFkaWVudD4KICA8L2RlZnM+CiAgPGcgZmlsbD0ibm9uZSIgZmlsbC1ydWxlPSJldmVub2RkIiBmaWx0ZXI9InVybCgjZm9sZGVyLTMyLWEpIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgyIDUpIj4KICAgIDxtYXNrIGlkPSJmb2xkZXItMzItZCIgZmlsbD0iI2ZmZiI+CiAgICAgIDx1c2UgeGxpbms6aHJlZj0iI2ZvbGRlci0zMi1iIi8+CiAgICA8L21hc2s+CiAgICA8dXNlIGZpbGw9InVybCgjZm9sZGVyLTMyLWMpIiB4bGluazpocmVmPSIjZm9sZGVyLTMyLWIiLz4KICAgIDxnIG1hc2s9InVybCgjZm9sZGVyLTMyLWQpIj4KICAgICAgPHVzZSBmaWxsPSIjMDAwIiBmaWx0ZXI9InVybCgjZm9sZGVyLTMyLWUpIiB4bGluazpocmVmPSIjZm9sZGVyLTMyLWYiLz4KICAgICAgPHVzZSBmaWxsPSJ1cmwoI2ZvbGRlci0zMi1nKSIgeGxpbms6aHJlZj0iI2ZvbGRlci0zMi1mIi8+CiAgICAgIDx1c2UgZmlsbD0iIzAwMCIgZmlsdGVyPSJ1cmwoI2ZvbGRlci0zMi1oKSIgeGxpbms6aHJlZj0iI2ZvbGRlci0zMi1mIi8+CiAgICA8L2c+CiAgICA8ZyBmaWxsPSJ1cmwoI2ZvbGRlci0zMi1pKSIgbWFzaz0idXJsKCNmb2xkZXItMzItZCkiPgogICAgICA8cGF0aCBkPSJNMCwwLjI1IEwyOCwwLjI1IEwyOCwxNC43NSBDMjgsMTYuNjgyOTk2NiAyNi40MzI5OTY2LDE4LjI1IDI0LjUsMTguMjUgTDMuNSwxOC4yNSBDMS41NjcwMDMzOCwxOC4yNSAyLjM2NzIzODEzZS0xNiwxNi42ODI5OTY2IDAsMTQuNzUgTDAsMC4yNSBaIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgwIDUuNzUpIi8+CiAgICA8L2c+CiAgPC9nPgo8L3N2Zz4K'
fileIcon='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rIiB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiI+CiAgPGRlZnM+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9InRleHQtcGxhaW4tYyIgeDE9IjUwJSIgeDI9IjUwJSIgeTE9IjAlIiB5Mj0iOTguOTQ3JSI+CiAgICAgIDxzdG9wIG9mZnNldD0iMCUiIHN0b3AtY29sb3I9IiNGN0Y3RjciLz4KICAgICAgPHN0b3Agb2Zmc2V0PSIxMDAlIiBzdG9wLWNvbG9yPSIjRjZGNkY2Ii8+CiAgICA8L2xpbmVhckdyYWRpZW50PgogICAgPHBhdGggaWQ9InRleHQtcGxhaW4tYiIgZD0iTTE1LDAgTDIyLDcgTDIyLDIyIEMyMiwyNC4yMDkxMzkgMjAuMjA5MTM5LDI2IDE4LDI2IEw0LDI2IEMxLjc5MDg2MSwyNiAyLjcwNTQxNWUtMTYsMjQuMjA5MTM5IDAsMjIgTDAsNCBDLTIuNzA1NDE1ZS0xNiwxLjc5MDg2MSAxLjc5MDg2MSw0LjA1ODEyMjUxZS0xNiA0LDAgTDE1LDAgWiIvPgogICAgPGZpbHRlciBpZD0idGV4dC1wbGFpbi1hIiB3aWR0aD0iMTM2LjQlIiBoZWlnaHQ9IjEzMC44JSIgeD0iLTE4LjIlIiB5PSItMTEuNSUiIGZpbHRlclVuaXRzPSJvYmplY3RCb3VuZGluZ0JveCI+CiAgICAgIDxmZU1vcnBob2xvZ3kgaW49IlNvdXJjZUFscGhhIiBvcGVyYXRvcj0iZGlsYXRlIiByYWRpdXM9Ii41IiByZXN1bHQ9InNoYWRvd1NwcmVhZE91dGVyMSIvPgogICAgICA8ZmVPZmZzZXQgZHk9IjEiIGluPSJzaGFkb3dTcHJlYWRPdXRlcjEiIHJlc3VsdD0ic2hhZG93T2Zmc2V0T3V0ZXIxIi8+CiAgICAgIDxmZUdhdXNzaWFuQmx1ciBpbj0ic2hhZG93T2Zmc2V0T3V0ZXIxIiByZXN1bHQ9InNoYWRvd0JsdXJPdXRlcjEiIHN0ZERldmlhdGlvbj0iMSIvPgogICAgICA8ZmVDb21wb3NpdGUgaW49InNoYWRvd0JsdXJPdXRlcjEiIGluMj0iU291cmNlQWxwaGEiIG9wZXJhdG9yPSJvdXQiIHJlc3VsdD0ic2hhZG93Qmx1ck91dGVyMSIvPgogICAgICA8ZmVDb2xvck1hdHJpeCBpbj0ic2hhZG93Qmx1ck91dGVyMSIgdmFsdWVzPSIwIDAgMCAwIDAgICAwIDAgMCAwIDAgICAwIDAgMCAwIDAgIDAgMCAwIDAuMSAwIi8+CiAgICA8L2ZpbHRlcj4KICAgIDxsaW5lYXJHcmFkaWVudCBpZD0idGV4dC1wbGFpbi1mIiB4MT0iNTAlIiB4Mj0iMTAuNDg5JSIgeTE9IjUwJSIgeTI9IjkxLjE5NCUiPgogICAgICA8c3RvcCBvZmZzZXQ9IjAlIiBzdG9wLWNvbG9yPSIjRkZGIiBzdG9wLW9wYWNpdHk9Ii4xIi8+CiAgICAgIDxzdG9wIG9mZnNldD0iMTAwJSIgc3RvcC1jb2xvcj0iI0ZGRiIgc3RvcC1vcGFjaXR5PSIuMyIvPgogICAgPC9saW5lYXJHcmFkaWVudD4KICAgIDxwYXRoIGlkPSJ0ZXh0LXBsYWluLWUiIGQ9Ik0xNSwwIEwyMiw3IEwxNy4yNSw3IEMxNi4wMDczNTkzLDcgMTUsNS45OTI2NDA2OSAxNSw0Ljc1IEwxNSwwIFoiLz4KICAgIDxmaWx0ZXIgaWQ9InRleHQtcGxhaW4tZCIgd2lkdGg9IjE1Ny4xJSIgaGVpZ2h0PSIxNTcuMSUiIHg9Ii0yOC42JSIgeT0iLTE0LjMlIiBmaWx0ZXJVbml0cz0ib2JqZWN0Qm91bmRpbmdCb3giPgogICAgICA8ZmVPZmZzZXQgZHk9IjEiIGluPSJTb3VyY2VBbHBoYSIgcmVzdWx0PSJzaGFkb3dPZmZzZXRPdXRlcjEiLz4KICAgICAgPGZlR2F1c3NpYW5CbHVyIGluPSJzaGFkb3dPZmZzZXRPdXRlcjEiIHJlc3VsdD0ic2hhZG93Qmx1ck91dGVyMSIgc3RkRGV2aWF0aW9uPSIuNSIvPgogICAgICA8ZmVDb21wb3NpdGUgaW49InNoYWRvd0JsdXJPdXRlcjEiIGluMj0iU291cmNlQWxwaGEiIG9wZXJhdG9yPSJvdXQiIHJlc3VsdD0ic2hhZG93Qmx1ck91dGVyMSIvPgogICAgICA8ZmVDb2xvck1hdHJpeCBpbj0ic2hhZG93Qmx1ck91dGVyMSIgdmFsdWVzPSIwIDAgMCAwIDAgICAwIDAgMCAwIDAgICAwIDAgMCAwIDAgIDAgMCAwIDAuMDUgMCIvPgogICAgPC9maWx0ZXI+CiAgPC9kZWZzPgogIDxnIGZpbGw9Im5vbmUiIGZpbGwtcnVsZT0iZXZlbm9kZCI+CiAgICA8ZyB0cmFuc2Zvcm09InRyYW5zbGF0ZSg1IDMpIj4KICAgICAgPHVzZSBmaWxsPSIjMDAwIiBmaWx0ZXI9InVybCgjdGV4dC1wbGFpbi1hKSIgeGxpbms6aHJlZj0iI3RleHQtcGxhaW4tYiIvPgogICAgICA8cGF0aCBmaWxsPSJ1cmwoI3RleHQtcGxhaW4tYykiIHN0cm9rZT0iIzAwMCIgc3Ryb2tlLW9wYWNpdHk9Ii4xIiBzdHJva2Utd2lkdGg9Ii41IiBkPSJNMTUuMTc2Nzc2NywtMC4xNzY3NzY2OTUgTDIyLjE3Njc3NjcsNi44MjMyMjMzIEwyMi4yNSw3IEwyMi4yNSwyMiBDMjIuMjUsMjQuMzQ3MjEwMiAyMC4zNDcyMTAyLDI2LjI1IDE4LDI2LjI1IEw0LDI2LjI1IEMxLjY1Mjc4OTgxLDI2LjI1IC0wLjI1LDI0LjM0NzIxMDIgLTAuMjUsMjIgTC0wLjI1LDQgQy0wLjI1LDEuNjUyNzg5ODEgMS42NTI3ODk4MSwtMC4yNSA0LC0wLjI1IEwxNSwtMC4yNSBMMTUuMTc2Nzc2NywtMC4xNzY3NzY2OTUgWiIvPgogICAgICA8dXNlIGZpbGw9IiMwMDAiIGZpbHRlcj0idXJsKCN0ZXh0LXBsYWluLWQpIiB4bGluazpocmVmPSIjdGV4dC1wbGFpbi1lIi8+CiAgICAgIDx1c2UgZmlsbD0idXJsKCN0ZXh0LXBsYWluLWYpIiB4bGluazpocmVmPSIjdGV4dC1wbGFpbi1lIi8+CiAgICA8L2c+CiAgICA8cGF0aCBmaWxsPSIjQUNBM0MyIiBkPSJNMjQsMTIgTDI0LDEzIEw4LDEzIEw4LDEyIEwyNCwxMiBaIE0yNCwxNSBMMjQsMTYgTDgsMTYgTDgsMTUgTDI0LDE1IFogTTI0LDE4IEwyNCwxOSBMOCwxOSBMOCwxOCBMMjQsMTggWiBNMjQsMjEgTDI0LDIyIEw4LDIyIEw4LDIxIEwyNCwyMSBaIE0yNCwyNCBMMjQsMjUgTDgsMjUgTDgsMjQgTDI0LDI0IFoiLz4KICA8L2c+Cjwvc3ZnPgo='
fileLink='data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rIiB3aWR0aD0iMzJwdCIgaGVpZ2h0PSIzMnB0IiB2aWV3Qm94PSIwIDAgMzIgMzIiIHZlcnNpb249IjEuMSI+CjxnIGlkPSJzdXJmYWNlMSI+CjxwYXRoIHN0eWxlPSIgc3Ryb2tlOm5vbmU7ZmlsbC1ydWxlOm5vbnplcm87ZmlsbDpyZ2IoOTYuNDcwNTg4JSw5Ni40NzA1ODglLDk2LjQ3MDU4OCUpO2ZpbGwtb3BhY2l0eToxOyIgZD0iTSAxOC42Njc5NjkgMi42Njc5NjkgTCA4IDIuNjY3OTY5IEMgNi41MTk1MzEgMi42Njc5NjkgNS4zMzIwMzEgMy44NTE1NjIgNS4zMzIwMzEgNS4zMzIwMzEgTCA1LjMzMjAzMSAyNi42Njc5NjkgQyA1LjMzMjAzMSAyOC4xNDg0MzggNi41MTk1MzEgMjkuMzMyMDMxIDggMjkuMzMyMDMxIEwgMjQgMjkuMzMyMDMxIEMgMjUuNDgwNDY5IDI5LjMzMjAzMSAyNi42Njc5NjkgMjguMTQ4NDM4IDI2LjY2Nzk2OSAyNi42Njc5NjkgTCAyNi42Njc5NjkgMTAuNjY3OTY5IEwgMTguNjY3OTY5IDIuNjY3OTY5IE0gMTQuNjY3OTY5IDI2LjY2Nzk2OSBMIDEzLjMzMjAzMSAyNi42Njc5NjkgQyAxMS4xODc1IDI2LjY2Nzk2OSA4IDI1LjI1MzkwNiA4IDIxLjMzMjAzMSBDIDggMTcuNDI1NzgxIDExLjE4NzUgMTYgMTMuMzMyMDMxIDE2IEwgMTQuNjY3OTY5IDE2IEwgMTQuNjY3OTY5IDE4LjY2Nzk2OSBMIDEzLjMzMjAzMSAxOC42Njc5NjkgQyAxMi43MTg3NSAxOC42Njc5NjkgMTAuNjY3OTY5IDE4Ljg5NDUzMSAxMC42Njc5NjkgMjEuMzMyMDMxIEMgMTAuNjY3OTY5IDIzLjg2NzE4OCAxMi44OTQ1MzEgMjQgMTMuMzMyMDMxIDI0IEwgMTQuNjY3OTY5IDI0IEwgMTQuNjY3OTY5IDI2LjY2Nzk2OSBNIDIwIDIwIEwgMjAgMjIuNjY3OTY5IEwgMTIgMjIuNjY3OTY5IEwgMTIgMjAgTCAyMCAyMCBNIDE4LjY2Nzk2OSAyNi42Njc5NjkgTCAxNy4zMzIwMzEgMjYuNjY3OTY5IEwgMTcuMzMyMDMxIDI0IEwgMTguNjY3OTY5IDI0IEMgMTkuMjgxMjUgMjQgMjEuMzMyMDMxIDIzLjc3MzQzOCAyMS4zMzIwMzEgMjEuMzMyMDMxIEMgMjEuMzMyMDMxIDE4LjgwMDc4MSAxOS4xMDU0NjkgMTguNjY3OTY5IDE4LjY2Nzk2OSAxOC42Njc5NjkgTCAxNy4zMzIwMzEgMTguNjY3OTY5IEwgMTcuMzMyMDMxIDE2IEwgMTguNjY3OTY5IDE2IEMgMjAuODEyNSAxNiAyNCAxNy40MjU3ODEgMjQgMjEuMzMyMDMxIEMgMjQgMjUuMjUzOTA2IDIwLjgxMjUgMjYuNjY3OTY5IDE4LjY2Nzk2OSAyNi42Njc5NjkgTSAxNy4zMzIwMzEgMTIgTCAxNy4zMzIwMzEgNC42Njc5NjkgTCAyNC42Njc5NjkgMTIgWiBNIDE3LjMzMjAzMSAxMiAiLz4KPC9nPgo8L3N2Zz4K'
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


def get_ip_address(ifname):
    import socket
    import fcntl
    import struct
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


class GetWanIp:
    def getip(self):
        return "127.0.0.1"

    def visit(self, url):
        #req = urllib2.Request(url)
        # values = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537',
        #      'Referer': 'http://ip.taobao.com/ipSearch.php',
        #      'ip': 'myip'
        #     }
        #data = urllib.urlencode(values)
        opener = urllib2.urlopen(url, None, 3)
        if url == opener.geturl():
            str = opener.read()
        return re.search('(\d+\.){3}\d+', str).group(0)


def showTips():
    print ""
    print '----------------------------------------------------------------------->> '
    try:
        port = int(sys.argv[1])
    except Exception, e:
        print '-------->> Warning: Port is not given, will use deafult port: 8080 '
        print '-------->> if you want to use other port, please execute: '
        print '-------->> python SimpleHTTPServerWithUpload.py port '
        print "-------->> port is a integer and it's range: 0 < port < 65535 "
        port = 8080

    if not 0 < port < 65535:
        port = 8080
    # serveraddr = ('', port)
    print '-------->> Now, listening at port ' + str(port) + ' ...'
    osType = platform.system()
    if osType == "Linux":
        print '-------->> You can visit the URL:   http://' + GetWanIp().getip() + \
            ':' + str(port)
    else:
        print '-------->> You can visit the URL:   http://127.0.0.1:' + \
            str(port)
    print '----------------------------------------------------------------------->> '
    print ""
    return ('', port)


serveraddr = showTips()
shareDir = os.getcwd()
try:
  shareDir = sys.argv[2]
  print 'share dir is ' + shareDir
except Exception, e:
  print 'did not set share dir, use current dir '+shareDir

def sizeof_fmt(num):
    for x in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


def modification_date(filename):
    # t = os.path.getmtime(filename)
    # return datetime.datetime.fromtimestamp(t)
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(filename)))


class SimpleHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    """Simple HTTP request handler with GET/HEAD/POST commands.

    This serves files from the current directory and any of its
    subdirectories. The MIME type for files is determined by
    calling the .guess_type() method. And can reveive file uploaded
    by client.

    The GET/HEAD/POST requests are identical except that the HEAD
    request omits the actual contents of the file.

    """

    server_version = "SimpleHTTPWithUpload/" + __version__

    def do_GET(self):
        """Serve a GET request."""
        # print "....................", threading.currentThread().getName()
        f = self.send_head()
        if f:
            self.copyfile(f, self.wfile)
            f.close()

    def do_HEAD(self):
        """Serve a HEAD request."""
        f = self.send_head()
        if f:
            f.close()

    def do_POST(self):
        """Serve a POST request."""
        r, info = self.deal_post_data()
        print r, info, "by: ", self.client_address
        f = StringIO()
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title>Upload Result Page</title>\n")
        f.write("<body>\n<h2>Upload Result Page</h2>\n")
        f.write("<hr>\n")
        if r:
            f.write("<strong>Success:</strong>")
        else:
            f.write("<strong>Failed:</strong>")
        f.write(info)
        f.write("<br><a href='%s'>back</a>" % self.headers['referer'])
        f.write("<hr><small>Powered By: bones7456, check new version at ")
        f.write("<a href='http://li2z.cn/?s=SimpleHTTPServerWithUpload'>")
        f.write("here</a>.</small></body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        if f:
            self.copyfile(f, self.wfile)
            f.close()

    def deal_post_data(self):
        boundary = self.headers.plisttext.split("=")[1]
        remainbytes = int(self.headers['content-length'])
        line = self.rfile.readline()
        remainbytes -= len(line)
        if not boundary in line:
            return (False, "Content NOT begin with boundary")
        line = self.rfile.readline()
        remainbytes -= len(line)
        fn = re.findall(
            r'Content-Disposition.*name="file"; filename="(.*)"', line)
        if not fn:
            return (False, "Can't find out file name...")
        path = shareDir+self.path
        osType = platform.system()
        try:
            if osType == "Linux":
                fn = os.path.join(path, fn[0].decode('gbk').encode('utf-8'))
            else:
                fn = os.path.join(path, fn[0])
        except Exception, e:
            return (False, "文件名请不要用中文，或者使用IE上传中文名的文件。")
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
            if boundary in line:
                preline = preline[0:-1]
                if preline.endswith('\r'):
                    preline = preline[0:-1]
                out.write(preline)
                out.close()
                return (True, "File '%s' upload success!" % fn)
            else:
                out.write(preline)
                preline = line
        return (False, "Unexpect Ends of data.")

    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        path = shareDir+urllib.unquote(self.path)
        f = None
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error). In either case, the headers are sent, making the
        interface the same as for send_head().

        """
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        f = StringIO()
        displaypath = cgi.escape(urllib.unquote(self.path))
        parimaryColor = "rgb(9, 2, 75)"
        secondColor="rgb(58, 48, 151)"
        infoColor="rgba(192, 191, 191, 1)"
        reversParimaryColor="rgb(247, 247, 248)"
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write('<html><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><title>Directory listing for %s</title>' %displaypath)
        f.write('<meta charset="utf-8">')
        f.write('<meta http-equiv="X-UA-Compatible" content="IE=edge">')
        f.write('<meta name="viewport" content="width=device-width,initial-scale=1.0">')
        f.write("<link rel='icon' href='"+favicon+"'>")
        f.write("<head>")
        f.write("<style>")
        f.write("body,html{padding:0px;margin:0px;}")
        f.write("input[type='submit'],button,input[type=button]{background-color: #fff;border:none;box-shadow: 0px 0px 3px %s;cursor:pointer;padding:3px 5px;}" %infoColor)
        f.write(".main-container{position:relative;padding:3px 5px;}")
        f.write("@media screen and (min-width:768px){")
        f.write(".main-container{margin-left:15%%;margin-right:15%%;box-shadow:0px 0px 10px %s;}"%infoColor)
        f.write("}")
        f.write("@media screen and (min-width:1200px){.main-container {margin-left:20%%;margin-right:20%%;box-shadow:0px 0px 10px %s ;}}"%infoColor)
        f.write("@media screen and (min-width:1920px) {.main-container {margin-left:30%%;margin-right:30%%;box-shadow:0px 0px 10px %s ;}}"%infoColor)
        f.write(".navigator{background-color:%s;line-height: 3rem;height:3rem;padding:3px 5px;color:%s;}"%(parimaryColor,reversParimaryColor))
        f.write(".text-info{font-size:12px;color:%s;}"%infoColor)
        f.write("table tr:hover{background-color:rgba(192,191,191,0.5);}")
        f.write("table{width:100%;border-collapse:collapse}")
        f.write("table tr td{padding:3px 5px;}")
        f.write("table tr td div img{width:100%;height:100%;}")
        f.write("table tr td:first-child div{float:left;}")
        f.write("table tr td:first-child a{padding:3px 5px;text-decoration:none;color:%s;float:left;}"%secondColor)
        f.write("table tr td:first-child a:hover {color: %s;}"%parimaryColor)
        f.write(".file-icon{display:inline-block;width:2rem;height:2rem;border-radius:4px;font-size:9px;text-align:center;}")
        f.write("a{color:%s;text-decoration:none;}a:hover{color:%s;}"%(parimaryColor,infoColor))
        f.write("<style>")
        f.write("<style>")
        f.write("</style>")
        f.write("</head>")
        f.write("<body>")
        f.write("<div class='navigator'>文件共享</div>")
        f.write("<div class='main-container'>")
        def isEmpty(i):
          return i!=''
        pathArr = filter(isEmpty,displaypath.split('/'))
        f.write("<h4>/")
        recordPath = ''
        for item in pathArr:
          recordPath +='/'+item
          f.write("<a href='"+recordPath+"/'>%s</a>/"%item)
        f.write("</h4>")
        f.write("<div>")
        f.write("<form ENCTYPE='multipart/form-data' method='post'>")
        f.write("<input name='file' type='file' id='selectedFile'/>")
        f.write("<input type='submit' value='上传' onClick='uploadCheck(event)'/>")
        f.write("<script>")
        f.write("function uploadCheck(event){")
        f.write("var length = document.getElementById('selectedFile').files.length;")
        f.write("if(length===0){event.preventDefault();alert('请选择文件');}")
        f.write("}")
        f.write("</script>")
        f.write("<input type='button' value='根目录' onClick='location=\"/\"'>")
        f.write("</form>")
        f.write("</div>")
        f.write("<div style='min-height:calc(100vh - 165px);'>")
        f.write("<table>")
        if len(list)==0:
          f.write("<tr><td width='100%' style='text-align:center;' class='text-info'>无数据</td></tr>")
        for name in list:
            fullname = os.path.join(path, name)
            colorName = displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                linkname = name + "/"
                colorName = '<div class="file-icon"><img src="'+folderIcon+'"></div><a href="'+urllib.quote(linkname)+'" title="'+name+'">' + name + '/</a>'
                displayname = name
            elif os.path.islink(fullname):
                colorName = '<div class="file-icon"><img src="'+fileLink+'"></div><a href="'+urllib.quote(linkname)+'" title="'+name+'">' + name + '</a>'
                displayname = name
                # Note: a link to a directory displays with @ and links with /
            else:
                colorName = '<div class="file-icon"><img src="'+fileIcon+'"></div><a href="'+urllib.quote(linkname)+'" download="'+name+'" title="'+name+'">' + name + '</a>'
            filename = path + displayname
            f.write('<tr><td>%s</td><td class="text-info">%s</td><td class="text-info">%s</td></tr>'
                    % (colorName,sizeof_fmt(os.path.getsize(filename)), modification_date(filename)))
        f.write("</table>")
        f.write("</div>")
        f.write("</div>")
        f.write("</body>")
        f.write("</html>")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored. (XXX They should
        probably be diagnosed.)

        """
        # abandon query parameters
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = os.getcwd()
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir):
                continue
            path = os.path.join(path, word)
        return path

    def copyfile(self, source, outputfile):
        """Copy all data between two file objects.

        The SOURCE argument is a file object open for reading
        (or anything with a read() method) and the DESTINATION
        argument is a file object open for writing (or
        anything with a write() method).

        The only reason for overriding this would be to change
        the block size or perhaps to replace newlines by CRLF
        -- note however that this the default server uses this
        to copy binary data as well.

        """
        shutil.copyfileobj(source, outputfile)

    def guess_type(self, path):
        """Guess the type of a file.

        Argument is a PATH (a filename).

        Return value is a string of the form type/subtype,
        usable for a MIME Content-type header.

        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        as a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.

        """

        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

    if not mimetypes.inited:
        mimetypes.init()  # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream',  # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
    })


class ThreadingServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass


def test(HandlerClass=SimpleHTTPRequestHandler,
         ServerClass=BaseHTTPServer.HTTPServer):
    BaseHTTPServer.test(HandlerClass, ServerClass)


if __name__ == '__main__':
    # test()

    # 单线程
    # srvr = BaseHTTPServer.HTTPServer(serveraddr, SimpleHTTPRequestHandler)

    # 多线程
    srvr = ThreadingServer(serveraddr, SimpleHTTPRequestHandler)

    srvr.serve_forever()
