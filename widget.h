#ifndef WIDGET_H
#define WIDGET_H

#include <QWidget>
#include <string>
#include "config.h"
#include <QMenu>
#include <DMainWindow>
DWIDGET_USE_NAMESPACE
namespace Ui {
class Widget;
}

class Widget : public QWidget
{
    Q_OBJECT

public:
    explicit Widget(QWidget *parent = 0);
    QPixmap createQRCode(const QString &text);
    QString ip_address;
    ~Widget();

    QStringList getIpList();
private slots:
    void on_pushButton_clicked();

    void on_pushButton_openlink_clicked();

private:
    Ui::Widget *ui;

};
#endif // WIDGET_H
