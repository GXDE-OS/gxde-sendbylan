# 局域网文件共享

     支持GXDE OS 15.14 /deepin 20/23 / UOS

    这是基于DTK开发的插件,可以实现在局域网内向任何设备共享文件.

---
# 安装说明:
    在源代码内容不变的情况下,安装目录必须位于/opt/gxde-sendbylan
    安装目录中的可执行文件是 SBL(主程序 gxde-sendbylan) 与 server.py(共享服务),设置项在主程序窗口的菜单里

---
## 功能说明
    右键文件夹选择“分享到局域网”后，会自动在局域网内启动共享服务并显示二维码/地址：

    * 网页方式：手机/电脑打开 http://本机IP:端口/ 即可浏览、下载，也可以直接上传文件或整个文件夹
    * WebDAV：同一个地址可以直接挂载为网络位置（文件管理器、ES 文件浏览器等）
    * SMB：可在设置里切换为 SMB 共享，Windows 资源管理器可直接访问（445 端口需要 root 权限）

    高级设置里可以修改端口、共享方式（网页+WebDAV / 仅网页 / SMB）、是否允许接收端上传、SMB 共享名以及开机自启动。

---
## 开发平台和依赖说明
    开发平台：GXDE 15.13

    依赖：dde-file-manager,gxde-file-manager,python3

    可选依赖：python3-impacket（SMB 共享方式需要，Debian/GXDE 下 sudo apt install python3-impacket）

    共享服务由 momo-and-mox-tool-scripts 仓库的 server.py 提供，本仓库中的 server.py 与其保持一致，
    升级方式就是把该文件原样复制过来。
