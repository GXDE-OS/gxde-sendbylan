#ifndef WIDGET_H
#define WIDGET_H

#include <QWidget>
#include <string>
#include "config.h"
#include <QMenu>

namespace Ui {
class Widget;
}

class Widget : public QWidget
{
    Q_OBJECT

public:
    explicit Widget(const QString &folder, QWidget *parent = nullptr);
    QPixmap createQRCode(const QString &text);
    QString ip_address;
    QString folderPath;
    ~Widget();

    QStringList getIpList();

public slots:
    void reloadSettings();
private slots:
    void on_pushButton_clicked();

    void on_pushButton_openlink_clicked();

private:
    Ui::Widget *ui;

};
#endif // WIDGET_H