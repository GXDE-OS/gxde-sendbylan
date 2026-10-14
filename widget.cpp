#include "widget.h"
#include "ui_widget.h"
#include "sblconfig.h"
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

    SBL::startServer(folderPath);

    ui->label->setPixmap(*pixmap);
    ui->label->setAlignment(Qt::AlignHCenter);
    ui->label->show();

    refreshAddress();
}

Widget::~Widget()
{
    stopServer();
    QFile::remove(SBL_LAUNCHER_SCRIPT);
    delete ui;
}

void Widget::stopServer()
{
    // 只结束本程序启动的 server.py，避免误杀系统里其它 python 进程
    SBL::stopServer();
}

void Widget::refreshAddress()
{
    const QString address = SBL::preferredAddress();

    QString hint = SBL::addressHint();
    const QString warning = SBL::warningText();
    if (!warning.isEmpty())
        hint += "\n" + warning;

    ui->label_2->setText(hint);
    ip_address = SBL::shareUrl(address, folderPath);
    ui->label_3->setText(ip_address);
    ui->label_3->setToolTip(ip_address);
    ui->label->setPixmap(createQRCode(ip_address));
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
    QDesktopServices::openUrl(QUrl(ip_address));
}

void Widget::reloadSettings()
{
    stopServer();
    SBL::startServer(folderPath);
    refreshAddress();
}
