#include "mainwindow.h"
#include <DApplication>
#include <DWidgetUtil>  //Dtk::Widget::moveToCenter(&w); 要调用它，就得引用DWidgetUtil
#include <QDebug>
#include <widget.h>
#include <fstream>
#include <DMessageBox>
DWIDGET_USE_NAMESPACE
int main(int argc, char *argv[])
{
    DApplication::loadDXcbPlugin();  //让bar处在标题栏中
    DApplication a(argc, argv);
    a.setAttribute(Qt::AA_UseHighDpiPixmaps);
    a.loadTranslator();
    a.setOrganizationName("free");
    a.setApplicationVersion(DApplication::buildVersion("2.0"));
    a.setApplicationAcknowledgementPage("QQ:2684053139");
    a.setProductIcon(QIcon("/opt/SendByLAN/folder.svg"));  //设置Logo
    a.setProductName("文件夹共享设置");
    a.setApplicationName("文件夹共享设置"); //只有在这儿修改窗口标题才有效
    MainWindow w;

    w.show();
    //让打开时界面显示在正中
    Dtk::Widget::moveToCenter(&w);
    return a.exec();
}
