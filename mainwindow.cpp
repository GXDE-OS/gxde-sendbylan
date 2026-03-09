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
    setWindowFlags( (windowFlags() | Qt::CustomizeWindowHint) & ~Qt::WindowMaximizeButtonHint); // https://segmentfault.com/q/1010000042762264 最大化按钮隐藏
    // add settings menu to titlebar
    QAction *setting(new QAction(tr("设置"), this));
    m_menu->addAction(setting);
    titlebar()->setMenu(m_menu);
    connect(setting, &QAction::triggered, this, [=]() {
        // show advanced settings dialog
        SettingsDialog dlg(this);
        connect(&dlg, &SettingsDialog::settingsChanged, w, &Widget::reloadSettings);
        dlg.exec();
    });
}
MainWindow::~MainWindow()
{

}
