#include "widget.h"
#include "ui_widget.h"
#include <QDebug>
#include <QNetworkInterface>
#include <fstream>
#include <QtSvg>
#include <QString>
#include "QRCode/qrencode.h"
Widget::Widget(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::Widget)
{
    ui->setupUi(this);
    ui->label->setText("正在加载");

    //加载ok图标
    QString strPath = "ok.svg";
    QSvgRenderer* svgRender = new QSvgRenderer();
    svgRender->load(strPath);
    QPixmap* pixmap = new QPixmap(130,130);
    pixmap->fill(Qt::transparent);//设置背景透明
    QPainter p(pixmap);
    svgRender->render(&p);

    //运行运行脚本
    system("chmod +x /tmp/http.sh");
    system("/tmp/http.sh&");

    //显示
    ui->label->setPixmap(*pixmap);

    ui->label->setAlignment(Qt::AlignHCenter);
    ui->label->show();
    ui->label_2->setText("在接受端浏览器中输入：");
    QList<QHostAddress> network;
    network = QNetworkInterface().allAddresses();
    QStringList temp;

    //读取显示本地局域网IP
    for (int i=0;i<network.size();i++) {
        ip_address="http://"+QNetworkInterface().allAddresses().at(i).toString()+":8080";
        temp=ip_address.split(".");
        if(temp[0]=="http://192"){
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

QPixmap Widget::createQRCode(const QString &text) //二维码创建函数
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


void Widget::on_pushButton_2_clicked()
{

}
