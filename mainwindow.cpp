#include "mainwindow.h"
#include <DMainWindow>
#include <DMenu>
#include <DMenuBar>
#include <DTitlebar>
#include <QDebug>
DWIDGET_USE_NAMESPACE

MainWindow::MainWindow(QWidget *parent)
    : DMainWindow(parent),
      m_menu(new DMenu)
{
    w = new Widget;
    setCentralWidget(w);

    setMinimumSize(400,350);
    setMaximumSize(400,350);
    setWindowFlags(Qt::WindowStaysOnTopHint);
//    QMenu *fileMenu;
//    QString file="文件";
//    fileMenu = menuBar()->addAction(file);
    QAction *setting(new QAction(tr("设置"), this));
    m_menu->addAction(setting);
    titlebar()->setMenu(m_menu);
    connect(setting,&QAction::triggered,this,[=](){
       qDebug()<<"设置";
       system("/opt/SendByLAN/setting");
    });
}
MainWindow::~MainWindow()
{

}
