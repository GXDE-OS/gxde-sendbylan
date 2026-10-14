#include "mainwindow.h"
#include <DApplication>
#include <DWidgetUtil>
#include <QDebug>
#include <widget.h>
#include <fstream>
#include <QMessageBox>
#include <QNetworkInterface>
#include <QList>
#include <DMainWindow>
#include <QFile>
#include <QDir>

#include "config.h"
#include "sblconfig.h"

DWIDGET_USE_NAMESPACE

int main(int argc, char *argv[])
{
    DApplication::loadDXcbPlugin();
    DApplication a(argc, argv);
    a.loadTranslator();
    a.setOrganizationName("GXDE OS");
    a.setApplicationVersion(DApplication::buildVersion(APP_VERSION));
    a.setApplicationAcknowledgementPage("https://gitee.com/GXDE-OS/gxde-sendbylan");
    // 修复关于图标不显示的问题
    a.setProductIcon(QIcon(PATH_ICON));
    a.setProductName(MAIN_TITLE);
    a.setApplicationDescription("GXDE Sendbylan is a super cool and convenient tool for sharing your files by on click \nSpecial thank to Maicss");
    a.setApplicationName(MAIN_TITLE);

    DMainWindow tempWindow;

    if (argc < 2) {
        QMessageBox::critical(nullptr, "用法错误", "用法: 程序名 <文件夹路径>\n请提供一个有效的文件夹路径作为参数。");
        return 0;
    }

    SBL::configDir();

    std::fstream lock;
    lock.open(SBL_LAUNCHER_SCRIPT, std::ios::in);
    if (lock) {
        if (QMessageBox::critical(nullptr, "无法打开", "我们无法同时分享多个文件夹！\n如果您确信现在并没有运行其他分享，您可以点击忽略来忽略该警告", QMessageBox::Close | QMessageBox::Ignore, QMessageBox::Close) == QMessageBox::Ignore) {
            QFile::remove(SBL_LAUNCHER_SCRIPT);
        } else {
            return 0;
        }
    }

    const QString folderPath = QString::fromLocal8Bit(argv[1]);

    if (SBL::preferredAddress().isEmpty()) {
        system("notify-send \"您可能没有接入局域网，请检查网络情况。\" --icon=3");
        return 0;
    }

    // 启动脚本由主窗口负责执行（见 widget.cpp），这里先按当前设置写好
    SBL::writeLauncherScript(folderPath);

    MainWindow w(folderPath);
    w.show();
    Dtk::Widget::moveToCenter(&w);

    return a.exec();
}
