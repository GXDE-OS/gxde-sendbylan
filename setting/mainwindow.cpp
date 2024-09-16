#include "mainwindow.h"
#include <DMainWindow>

DWIDGET_USE_NAMESPACE

MainWindow::MainWindow(QWidget *parent)
    : DMainWindow(parent)
{
    w = new Widget;
    setCentralWidget(w);

    setMinimumSize(450,450);
    setMaximumSize(450,450);
    setWindowFlags(Qt::WindowStaysOnTopHint);
}

MainWindow::~MainWindow()
{

}
