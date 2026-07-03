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
    a.setProductIcon(QIcon("/opt/gxde-sendbylan/sendbylan.svg"));
    a.setProductName(MAIN_TITLE);
    a.setApplicationDescription("GXDE Sendbylan is a super cool and convenient tool for sharing your files by on click \nSpecial thank to Maicss");
    a.setApplicationName(MAIN_TITLE);

    DMainWindow tempWindow;

    if (argc < 2) {
        QMessageBox::critical(nullptr, "用法错误", "用法: 程序名 <文件夹路径>\n请提供一个有效的文件夹路径作为参数。");
        return 0;
    }

    std::string config_path = getenv("HOME");
    config_path += "/.config/SBL/";
    {
        QDir cfgdir(QString::fromStdString(config_path));
        if (!cfgdir.exists())
            cfgdir.mkpath(".");
    }

    std::fstream lock;
    lock.open("/tmp/http.sh", std::ios::in);
    if (lock) {
        if (QMessageBox::critical(nullptr, "无法打开", "我们无法同时分享多个文件夹！\n如果您确信现在并没有运行其他分享，您可以点击忽略来忽略该警告", QMessageBox::Close | QMessageBox::Ignore, QMessageBox::Close) == QMessageBox::Ignore) {
            QFile::remove("/tmp/http.sh");
        } else {
            return 0;
        }
    }

    std::fstream readconfig_port;
    std::string port;
    readconfig_port.open(config_path + "port", std::ios::in);
    if (readconfig_port) {
        getline(readconfig_port, port);
    } else {
        port = "8080";
    }

    QString ip_address;
    QStringList temp;
    bool isonlion = false;
    QList<QHostAddress> network = QNetworkInterface().allAddresses();
    for (int i = 0; i < network.size(); i++) {
        ip_address = "http://" + QNetworkInterface().allAddresses().at(i).toString() + ":" + port.c_str();
        temp = ip_address.split(".");
        isonlion = true;
    }
    if (!isonlion) {
        system("notify-send \"您可能没有接入局域网，请检查网络情况。\" --icon=3");
        return 0;
    }

    std::fstream outhttp;
    outhttp.open("/tmp/http.sh", std::fstream::out);
    outhttp << "/opt/gxde-sendbylan/main.py ";
    outhttp << port;
    outhttp << " -d ";
    outhttp << argv[1];
    outhttp.close();

    MainWindow w(QString::fromLocal8Bit(argv[1]));
    w.show();
    Dtk::Widget::moveToCenter(&w);

    return a.exec();
}