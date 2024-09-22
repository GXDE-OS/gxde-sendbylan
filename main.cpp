#include "mainwindow.h"
#include <DApplication>
#include <DWidgetUtil>  // Dtk::Widget::moveToCenter(&w); 要调用它，就得引用DWidgetUtil
#include <QDebug>
#include <widget.h>
#include <fstream>
#include <QMessageBox>
#include <QNetworkInterface>
#include <QList>
#include <dmainwindow.h>

DWIDGET_USE_NAMESPACE

int main(int argc, char *argv[])
{
    // 初始化
    DApplication::loadDXcbPlugin();  // 让bar处在标题栏中
    DApplication a(argc, argv);
    a.setAttribute(Qt::AA_UseHighDpiPixmaps);
    a.loadTranslator();
    a.setOrganizationName("GXDE OS");
    a.setApplicationVersion(DApplication::buildVersion(VERSON));
    a.setApplicationAcknowledgementPage("https://gitee.com/shenmo7192");
    a.setProductIcon(QIcon(PATH_ICON));  // 设置Logo
    a.setProductName(MAIN_TITLE);
    a.setApplicationName(MAIN_TITLE);  // 只有在这儿修改窗口标题才有效

    DMainWindow tempWindow;

    // 检查是否提供了参数
    if (argc < 2) {
        QMessageBox::critical(nullptr, "用法错误", "用法: 程序名 <文件夹路径>\n请提供一个有效的文件夹路径作为参数。");
        return 0;
    }

    std::string config_path = getenv("HOME");  // 读入配置目录
    config_path += "/.config/SBL/";

    // 模拟文件锁
    std::fstream lock;
    lock.open("/tmp/http.sh", std::ios::in);
    if (lock) {
        if (QMessageBox::critical(nullptr, "无法打开", "我们无法同时分享多个文件夹！\n如果您确信现在并没有运行其他分享，您可以点击NO忽略该警告", QMessageBox::Ok | QMessageBox::Close, QMessageBox::Ok) == QMessageBox::No) {
            system("rm /tmp/http.sh");
        } else {
            return 0;
        }
    }

    // 读入端口号
    std::fstream readconfig_port;
    std::string port;
    readconfig_port.open(config_path + "port", std::ios::in);
    if (readconfig_port) {
        getline(readconfig_port, port);
    } else {
        port = "8080";
    }

    // 检查网络状态
    QString ip_address;
    QStringList temp;
    bool isonlion = false;
    QList<QHostAddress> network = QNetworkInterface().allAddresses();
    for (int i = 0; i < network.size(); i++) {
        ip_address = "http://" + QNetworkInterface().allAddresses().at(i).toString() + ":" + port.c_str();
        temp = ip_address.split(".");
        // if (temp[0] == "http://192") {
            isonlion = true;
            // break;
        // }
    }
    if (!isonlion) {
        system("notify-send \"您可能没有接入局域网，请检查网络情况。\" --icon=3");
        return 0;
    }

    // 写入运行脚本
    std::fstream outhttp;
    outhttp.open("/tmp/http.sh", std::fstream::out);
    outhttp << "/opt/gxde-sendbylan/main.py ";
    outhttp << port;
    outhttp << " -d ";
    outhttp << argv[1];  // 只有在有参数时访问argv[1]
    outhttp.close();

    // 让打开时界面显示在正中
    MainWindow w;
    w.show();
    Dtk::Widget::moveToCenter(&w);

    return a.exec();
}
