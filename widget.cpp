#include "widget.h"
#include "ui_widget.h"
#include <QDebug>
#include <QNetworkInterface>
#include <fstream>
#include <QtSvg>
#include <QString>
#include "QRCode/qrencode.h"
#include <QMenu>
#include <QDesktopServices>
#include <QDir>

Widget::Widget(const QString &folder, QWidget *parent) :
    QWidget(parent),
    ui(new Ui::Widget),
    folderPath(folder)
{
    ui->setupUi(this);
    ui->label->setText("正在加载");

    QString strPath = "ok.svg";
    QSvgRenderer* svgRender = new QSvgRenderer();
    svgRender->load(strPath);
    QPixmap* pixmap = new QPixmap(130,130);
    pixmap->fill(Qt::transparent);
    QPainter p(pixmap);
    svgRender->render(&p);

    system("chmod +x /tmp/http.sh");
    system("/tmp/http.sh&");

    ui->label->setPixmap(*pixmap);
    ui->label->setAlignment(Qt::AlignHCenter);
    ui->label->show();
    ui->label_2->setText("在接受端浏览器中输入：");
    QList<QHostAddress> network;
    network = QNetworkInterface().allAddresses();
    QStringList temp;
    std::string config_path=getenv("HOME");
    config_path+="/.config/SBL/";
    QDir cfgDir(QString::fromStdString(config_path));
    if (!cfgDir.exists())
        cfgDir.mkpath(".");

    std::fstream readconfig_port;
    std::string port;
    readconfig_port.open(config_path + "port", std::ios::in);
    if(readconfig_port){
        getline(readconfig_port, port);
    }else {
        port = "8080";
    }
    for (int i=0;i<network.size();i++) {
        ip_address = "http://" + QNetworkInterface().allAddresses().at(i).toString() + ":" + port.c_str();
        temp = ip_address.split(".");
        if(temp[0] == "http://192" || temp[0] == "http://10."){
            break;
        }
    }

    ui->label_3->setText(ip_address);
    ui->label->setPixmap(createQRCode(ip_address));

}

Widget::~Widget()
{
    system("rm /tmp/http.sh");
    system("pkill -f \"python\"");
    delete ui;
}

void Widget::on_pushButton_clicked()
{
      QClipboard *clipboard = QApplication::clipboard();
      clipboard->setText(ip_address);
}

QPixmap Widget::createQRCode(const QString &text)
{
    int margin = 2;
    if (text.length() == 0)
    {
        return QPixmap();
    }
    QRcode *qrcode = QRcode_encodeString(text.toLocal8Bit(), 2, QR_ECLEVEL_L, QR_MODE_8, 0);
    if (qrcode == NULL) {
        return QPixmap();
    }
    unsigned char *p, *q;
    p = NULL;
    q = NULL;
    int x, y, bit;
    int realwidth;

    realwidth = qrcode->width;
    QImage image = QImage(realwidth, realwidth, QImage::Format_Indexed8);
    QRgb value;
    value = qRgb(255,255,255);
    image.setColor(0, value);
    value = qRgb(0,0,0);
    image.setColor(1, value);
    image.setColor(2, value);
    image.fill(0);
    p = qrcode->data;
    for(y=0; y<qrcode->width; y++)
    {
        bit = 7;
        q += margin / 8;
        bit = 7 - (margin % 8);
        for(x=0; x<qrcode->width; x++)
        {
            if ((*p & 1) << bit)
                image.setPixel(x, y, 1);
            else
                image.setPixel(x, y, 0);
            bit--;
            if(bit < 0)
            {
                q++;
                bit = 7;
            }
            p++;
        }
    }
    return QPixmap::fromImage(image.scaledToWidth(130));
}


void Widget::on_pushButton_openlink_clicked()
{
    QString URL = ip_address;
    QDesktopServices::openUrl(QUrl(URL.toLatin1()));
}

void Widget::reloadSettings()
{
    system("pkill -f \"python\"");
    std::string config_path = getenv("HOME");
    config_path += "/.config/SBL/";
    std::fstream readconfig_port;
    std::string port;
    readconfig_port.open(config_path + "port", std::ios::in);
    if (readconfig_port) {
        getline(readconfig_port, port);
    } else {
        port = "8080";
    }
    std::fstream outhttp;
    outhttp.open("/tmp/http.sh", std::fstream::out);
    outhttp << "/opt/gxde-sendbylan/main.py ";
    outhttp << port;
    outhttp << " -d ";
    outhttp << folderPath.toStdString();
    outhttp.close();
    system("chmod +x /tmp/http.sh");
    system("/tmp/http.sh&");

    QList<QHostAddress> network = QNetworkInterface().allAddresses();
    QStringList temp;
    for (int i = 0; i < network.size(); i++) {
        ip_address = "http://" + QNetworkInterface().allAddresses().at(i).toString() + ":" + port.c_str();
        temp = ip_address.split(".");
        if (temp[0] == "http://192" || temp[0] == "http://10.") {
            break;
        }
    }
    ui->label_3->setText(ip_address);
    ui->label->setPixmap(createQRCode(ip_address));
}