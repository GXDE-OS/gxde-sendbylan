#include "mainwindow.h"
#include "settingsdialog.h"
#include <DMainWindow>
#include <QMenu>
#include <QMenuBar>
#include <DTitlebar>
#include <QDebug>
DWIDGET_USE_NAMESPACE

MainWindow::MainWindow(const QString &folder, QWidget *parent)
    : DMainWindow(parent),
      m_menu(new QMenu)
{
    w = new Widget(folder);
    setCentralWidget(w);

    setMinimumSize(450,350);
    setMaximumSize(450,350);
    setWindowFlags(Qt::WindowStaysOnTopHint);
    setWindowFlags( (windowFlags() | Qt::CustomizeWindowHint) & ~Qt::WindowMaximizeButtonHint);
    QAction *setting(new QAction(tr("设置"), this));
    m_menu->addAction(setting);
    titlebar()->setMenu(m_menu);
    connect(setting, &QAction::triggered, this, [=]() {
        SettingsDialog dlg(folder, this);
        connect(&dlg, &SettingsDialog::settingsChanged, w, &Widget::reloadSettings);
        dlg.exec();
    });
}

MainWindow::~MainWindow()
{

}