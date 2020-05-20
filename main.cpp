#include "mainwindow.h"
#include <DApplication>
#include <DWidgetUtil>  //Dtk::Widget::moveToCenter(&w); 要调用它，就得引用DWidgetUtil
#include <QDebug>
#include <widget.h>
#include <fstream>
#include <DMessageBox>
#include <QNetworkInterface>
#include <QList>
DWIDGET_USE_NAMESPACE
int main(int argc, char *argv[])
{

    //初始化
    DApplication::loadDXcbPlugin();  //让bar处在标题栏中
    DApplication a(argc, argv);
    a.setAttribute(Qt::AA_UseHighDpiPixmaps);
    a.loadTranslator();
    a.setOrganizationName("free");
    a.setApplicationVersion(DApplication::buildVersion(VERSON));
    a.setApplicationAcknowledgementPage("QQ:2684053139");
    a.setProductIcon(QIcon(PATH_ICON));  //设置Logo
    a.setProductName(MAIN_TITLE);
    a.setApplicationName(MAIN_TITLE); //只有在这儿修改窗口标题才有效
    //模拟文件锁
    std::fstream lock;
    lock.open("/tmp/http.sh",std::ios::in);
    if(lock){
        if(DMessageBox::critical(NULL, "无法打开", "我们无法同时分享多个文件夹！\n如果您确信现在并没有运行其他分享，您可以点击NO忽略该警告", DMessageBox::Yes|DMessageBox::No, DMessageBox::Yes)==DMessageBox::No){
            system("rm /tmp/http.sh");
        }else {
            return 0;
        }
    }

    //检查网络状态
    QString ip_address;
    QStringList temp;
    bool isonlion=false;
    QList<QHostAddress> network;
    network = QNetworkInterface().allAddresses();
    for (int i=0;i<network.size();i++) {
        ip_address="http://"+QNetworkInterface().allAddresses().at(i).toString()+":8080";
        temp=ip_address.split(".");
        if(temp[0]=="http://192"){
            isonlion=true;
            break;
        }
    }
    if(!isonlion){
        system("notify-send \"您可能没有接入局域网，请检查网络情况。\" --icon=3");
        return 0;
    }

    //写入运行脚本
    std::fstream outhttp;
    outhttp.open("/tmp/http.sh",std::fstream::out);
    outhttp<<"cd /opt/SendByLAN\n";
    qDebug()<<sizeof (&argv)/sizeof (argv[1]);
    outhttp<<"/opt/SendByLAN/main.py 8080 ";
    outhttp<<argv[1];
    outhttp.close();
    //让打开时界面显示在正中
    MainWindow w;
    w.show();

    Dtk::Widget::moveToCenter(&w);


    return a.exec();
}
