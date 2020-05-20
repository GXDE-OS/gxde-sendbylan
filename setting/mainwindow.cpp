#include "mainwindow.h"
#include <DMainWindow>

DWIDGET_USE_NAMESPACE

MainWindow::MainWindow(QWidget *parent)
    : DMainWindow(parent)
{
    w = new Widget;
    setCentralWidget(w);

    setMinimumSize(400,450);
    setMaximumSize(400,450);
    setWindowFlags(Qt::WindowStaysOnTopHint);
}

MainWindow::~MainWindow()
{

}
