#ifndef CONFIG_H
#define CONFIG_H

/* 安装目录，可在构建时用 -DSBL_INSTALL_DIR=... 覆盖（CMake 会跟随 BINDIR） */
#ifndef SBL_INSTALL_DIR
#define SBL_INSTALL_DIR "/opt/gxde-sendbylan"
#endif

#define PATH_ICON SBL_INSTALL_DIR "/sendbylan.svg"
/* 共享服务由 momo-and-mox-tool-scripts 的 server.py 提供（支持 HTTP / WebDAV / SMB） */
#define SERVER_SCRIPT SBL_INSTALL_DIR "/server.py"
#define ERROR_PAGES_DIR SBL_INSTALL_DIR "/error"
/* 与 python 服务端约定的启动脚本（同时作为“是否已有分享在运行”的锁文件） */
#define SBL_LAUNCHER_SCRIPT "/tmp/http.sh"

#define MAIN_TITLE "共享文件夹"
#define VERSION "1.6"
#define APP_VERSION "4.1.1"

#endif // CONFIG_H
