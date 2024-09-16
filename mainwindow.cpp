#include "mainwindow.h"
#include <DMainWindow>
#include <QMenu>
#include <QMenuBar>
#include <DTitlebar>
#include <QDebug>
DWIDGET_USE_NAMESPACE

MainWindow::MainWindow(QWidget *parent)
    : DMainWindow(parent),
      m_menu(new QMenu)
{
    w = new Widget;
    setCentralWidget(w);

    setMinimumSize(450,350);
    setMaximumSize(450,350);
    setWindowFlags(Qt::WindowStaysOnTopHint);
//    QMenu *fileMenu;
//    QString file="文件";
//    fileMenu = menuBar()->addAction(file);
    QAction *setting(new QAction(tr("设置"), this));
    m_menu->addAction(setting);
    titlebar()->setMenu(m_menu);
    connect(setting,&QAction::triggered,this,[=](){
       qDebug()<<"设置";
       system("/opt/gxde-sendbylan/setting");
    });
}
MainWindow::~MainWindow()
{

}
