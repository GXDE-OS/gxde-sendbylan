#include "widget.h"
#include "ui_widget.h"
#include <QDebug>
#include <fstream>
#include <QtSvg>
#include <QString>
#include <dswitchbutton.h>
#include <stdio.h>
DWIDGET_USE_NAMESPACE
Widget::Widget(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::Widget)
{
    ui->setupUi(this);
    //UI组织
    ui->label_4->hide();
    ui->label_5->hide();
    ui->label_4->setStyleSheet("color:red");
    ui->widget_1->layout()->addWidget(switch_btn);
    connect(switch_btn,&DSwitchButton::clicked,[=](){
        ui->label_5->hide();
        if(!switch_btn->isChecked()){
            ui->lineEdit->hide();
            ui->toolButton->hide();
        }else {
            ui->lineEdit->show();
            ui->toolButton->show();
            qDebug()<<"show";
        }
    });
    //初始化配置
    config_path+="/.config/SBL/";
    //密码模块

    std::fstream readconfig_passwd;
    readconfig_passwd.open(config_path+"passwd",std::ios::in);
    std::string passwd;
    if(readconfig_passwd){
        qDebug()<<"存在";
        switch_btn->setChecked(true);
        getline(readconfig_passwd,passwd);
        ui->lineEdit->setText(QString::fromStdString(passwd));
    }else {
        qDebug()<<"不存在";
        switch_btn->setChecked(false);
    }
    if(!switch_btn->isChecked()){
        ui->lineEdit->hide();
        ui->toolButton->hide();
    }else {
        ui->lineEdit->show();
        ui->toolButton->show();
        qDebug()<<"show";
    }
    //端口模块
    std::fstream readconfig_port;
    std::string port;
    readconfig_port.open(config_path+"port",std::ios::in);
    if(readconfig_port){
        getline(readconfig_port,port);
        ui->lineEdit_2->setText(QString::fromStdString(port));
    }else {
        ui->lineEdit_2->setText("8080");
    }
    readconfig_port.close();
    readconfig_passwd.close();
}
Widget::~Widget()
{

    delete ui;
}

void Widget::on_lineEdit_textChanged(const QString &arg1)
{
    ui->label_5->hide();
    if(arg1.length()==20){
        ui->label_4->show();
    }else {
        ui->label_4->hide();
    }
}

void Widget::on_toolButton_pressed()
{
    ui->lineEdit->setEchoMode(QLineEdit::Normal);
}

void Widget::on_toolButton_released()
{
    ui->lineEdit->setEchoMode(QLineEdit::Password);
}

void Widget::on_pushButton_clicked() //写入配置
{



    if(ui->lineEdit->text()== "" && switch_btn->isChecked()){
        system("notify-send \"请填写密码。\" --icon=preferences-system");
        ui->label_5->show();
        return;
    }
    if(ui->lineEdit->text().toInt()>1024 && ui->lineEdit->text().toInt()<65535){
        system("notify-send \"超出可定义的端口号范围。\" --icon=preferences-system");
        ui->label_5->show();
        return;
    }
    //密码模块
    if (switch_btn->isChecked()) {
        std::fstream passwd;
        passwd.open(config_path+"passwd",std::ios::out);
        passwd<<ui->lineEdit->text().toStdString();
        passwd.close();
    }else {
        std::string passwd_file=config_path+"passwd";
        remove(passwd_file.c_str());
    }
    //端口模块
    std::fstream port;
    port.open(config_path+"port",std::ios::out);
    port<<ui->lineEdit_2->text().toStdString();
    port.close();

    system("notify-send \"您需要重新打开分享功能以应用设置。\" --icon=preferences-system");
}

void Widget::on_lineEdit_2_textChanged(const QString &arg1)
{
    ui->label_5->hide();
}
