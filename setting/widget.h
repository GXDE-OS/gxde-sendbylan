#ifndef WIDGET_H
#define WIDGET_H

#include <QWidget>
#include <string>
#include <dswitchbutton.h>
DWIDGET_USE_NAMESPACE
namespace Ui {
class Widget;
}

class Widget : public QWidget
{
    Q_OBJECT

public:
    explicit Widget(QWidget *parent = 0);
    std::string config_path=getenv("HOME");
    DSwitchButton *switch_btn=new DSwitchButton;
    ~Widget();
private slots:

    void on_lineEdit_textChanged(const QString &arg1);

    void on_toolButton_pressed();

    void on_toolButton_released();

    void on_pushButton_clicked();

    void on_lineEdit_2_textChanged(const QString &arg1);

private:
    Ui::Widget *ui;
};
#endif // WIDGET_H
