/********************************************************************************
** Form generated from reading UI file 'widget.ui'
**
** Created by: Qt User Interface Compiler version 5.11.3
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_WIDGET_H
#define UI_WIDGET_H

#include <QtCore/QVariant>
#include <QtGui/QIcon>
#include <QtWidgets/QApplication>
#include <QtWidgets/QGridLayout>
#include <QtWidgets/QHBoxLayout>
#include <QtWidgets/QLabel>
#include <QtWidgets/QLineEdit>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QSpacerItem>
#include <QtWidgets/QToolButton>
#include <QtWidgets/QVBoxLayout>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_Widget
{
public:
    QGridLayout *gridLayout;
    QPushButton *pushButton;
    QPushButton *pushButton_2;
    QWidget *widget;
    QVBoxLayout *verticalLayout_2;
    QWidget *widget_1;
    QHBoxLayout *horizontalLayout;
    QLabel *label;
    QWidget *widget_5;
    QHBoxLayout *horizontalLayout_2;
    QLineEdit *lineEdit;
    QToolButton *toolButton;
    QLabel *label_4;
    QWidget *widget_3;
    QVBoxLayout *verticalLayout_3;
    QWidget *widget_4;
    QVBoxLayout *verticalLayout_4;
    QLabel *label_2;
    QWidget *widget_2;
    QHBoxLayout *horizontalLayout_3;
    QLabel *label_3;
    QSpacerItem *horizontalSpacer_2;
    QLineEdit *lineEdit_2;
    QSpacerItem *verticalSpacer;
    QLabel *label_5;
    QSpacerItem *verticalSpacer_2;

    void setupUi(QWidget *Widget)
    {
        if (Widget->objectName().isEmpty())
            Widget->setObjectName(QStringLiteral("Widget"));
        Widget->resize(418, 407);
        gridLayout = new QGridLayout(Widget);
        gridLayout->setObjectName(QStringLiteral("gridLayout"));
        pushButton = new QPushButton(Widget);
        pushButton->setObjectName(QStringLiteral("pushButton"));

        gridLayout->addWidget(pushButton, 7, 0, 1, 1);

        pushButton_2 = new QPushButton(Widget);
        pushButton_2->setObjectName(QStringLiteral("pushButton_2"));

        gridLayout->addWidget(pushButton_2, 7, 1, 1, 1);

        widget = new QWidget(Widget);
        widget->setObjectName(QStringLiteral("widget"));
        QSizePolicy sizePolicy(QSizePolicy::Preferred, QSizePolicy::Maximum);
        sizePolicy.setHorizontalStretch(0);
        sizePolicy.setVerticalStretch(30);
        sizePolicy.setHeightForWidth(widget->sizePolicy().hasHeightForWidth());
        widget->setSizePolicy(sizePolicy);
        widget->setStyleSheet(QStringLiteral(""));
        verticalLayout_2 = new QVBoxLayout(widget);
        verticalLayout_2->setObjectName(QStringLiteral("verticalLayout_2"));
        widget_1 = new QWidget(widget);
        widget_1->setObjectName(QStringLiteral("widget_1"));
        QSizePolicy sizePolicy1(QSizePolicy::Preferred, QSizePolicy::Maximum);
        sizePolicy1.setHorizontalStretch(0);
        sizePolicy1.setVerticalStretch(40);
        sizePolicy1.setHeightForWidth(widget_1->sizePolicy().hasHeightForWidth());
        widget_1->setSizePolicy(sizePolicy1);
        widget_1->setStyleSheet(QStringLiteral(""));
        horizontalLayout = new QHBoxLayout(widget_1);
        horizontalLayout->setObjectName(QStringLiteral("horizontalLayout"));
        label = new QLabel(widget_1);
        label->setObjectName(QStringLiteral("label"));
        QSizePolicy sizePolicy2(QSizePolicy::Preferred, QSizePolicy::Maximum);
        sizePolicy2.setHorizontalStretch(0);
        sizePolicy2.setVerticalStretch(20);
        sizePolicy2.setHeightForWidth(label->sizePolicy().hasHeightForWidth());
        label->setSizePolicy(sizePolicy2);
        QFont font;
        font.setPointSize(15);
        label->setFont(font);
        label->setStyleSheet(QStringLiteral(""));
        label->setLineWidth(0);
        label->setIndent(-1);

        horizontalLayout->addWidget(label);


        verticalLayout_2->addWidget(widget_1);

        widget_5 = new QWidget(widget);
        widget_5->setObjectName(QStringLiteral("widget_5"));
        horizontalLayout_2 = new QHBoxLayout(widget_5);
        horizontalLayout_2->setObjectName(QStringLiteral("horizontalLayout_2"));
        lineEdit = new QLineEdit(widget_5);
        lineEdit->setObjectName(QStringLiteral("lineEdit"));
        QFont font1;
        font1.setPointSize(11);
        lineEdit->setFont(font1);
        lineEdit->setStyleSheet(QStringLiteral(""));
        lineEdit->setMaxLength(20);
        lineEdit->setEchoMode(QLineEdit::Password);
        lineEdit->setAlignment(Qt::AlignCenter);
        lineEdit->setDragEnabled(false);

        horizontalLayout_2->addWidget(lineEdit);

        toolButton = new QToolButton(widget_5);
        toolButton->setObjectName(QStringLiteral("toolButton"));
        toolButton->setAutoFillBackground(false);
        QIcon icon;
        icon.addFile(QStringLiteral(":/icons/icons/redeyes.svg"), QSize(), QIcon::Normal, QIcon::Off);
        icon.addFile(QStringLiteral(":/icons/icons/redeyes.svg"), QSize(), QIcon::Normal, QIcon::On);
        icon.addFile(QStringLiteral(":/icons/icons/image-red-eye.svg"), QSize(), QIcon::Disabled, QIcon::Off);
        icon.addFile(QStringLiteral(":/icons/icons/image-red-eye.svg"), QSize(), QIcon::Disabled, QIcon::On);
        icon.addFile(QStringLiteral(":/icons/icons/image-red-eye.svg"), QSize(), QIcon::Active, QIcon::Off);
        icon.addFile(QStringLiteral(":/icons/icons/image-red-eye.svg"), QSize(), QIcon::Active, QIcon::On);
        icon.addFile(QStringLiteral(":/icons/icons/image-red-eye.svg"), QSize(), QIcon::Selected, QIcon::Off);
        icon.addFile(QStringLiteral(":/icons/icons/image-red-eye.svg"), QSize(), QIcon::Selected, QIcon::On);
        toolButton->setIcon(icon);
        toolButton->setIconSize(QSize(20, 20));

        horizontalLayout_2->addWidget(toolButton);


        verticalLayout_2->addWidget(widget_5);

        label_4 = new QLabel(widget);
        label_4->setObjectName(QStringLiteral("label_4"));
        label_4->setAlignment(Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter);

        verticalLayout_2->addWidget(label_4);


        gridLayout->addWidget(widget, 0, 0, 1, 2);

        widget_3 = new QWidget(Widget);
        widget_3->setObjectName(QStringLiteral("widget_3"));
        widget_3->setAutoFillBackground(false);
        widget_3->setStyleSheet(QStringLiteral(""));
        verticalLayout_3 = new QVBoxLayout(widget_3);
        verticalLayout_3->setObjectName(QStringLiteral("verticalLayout_3"));
        widget_4 = new QWidget(widget_3);
        widget_4->setObjectName(QStringLiteral("widget_4"));
        verticalLayout_4 = new QVBoxLayout(widget_4);
        verticalLayout_4->setObjectName(QStringLiteral("verticalLayout_4"));
        label_2 = new QLabel(widget_4);
        label_2->setObjectName(QStringLiteral("label_2"));
        label_2->setFont(font);

        verticalLayout_4->addWidget(label_2);


        verticalLayout_3->addWidget(widget_4);

        widget_2 = new QWidget(widget_3);
        widget_2->setObjectName(QStringLiteral("widget_2"));
        horizontalLayout_3 = new QHBoxLayout(widget_2);
        horizontalLayout_3->setObjectName(QStringLiteral("horizontalLayout_3"));
        label_3 = new QLabel(widget_2);
        label_3->setObjectName(QStringLiteral("label_3"));
        QFont font2;
        font2.setPointSize(12);
        label_3->setFont(font2);

        horizontalLayout_3->addWidget(label_3);

        horizontalSpacer_2 = new QSpacerItem(40, 20, QSizePolicy::Maximum, QSizePolicy::Minimum);

        horizontalLayout_3->addItem(horizontalSpacer_2);

        lineEdit_2 = new QLineEdit(widget_2);
        lineEdit_2->setObjectName(QStringLiteral("lineEdit_2"));
        lineEdit_2->setStyleSheet(QStringLiteral(""));
        lineEdit_2->setMaxLength(5);
        lineEdit_2->setAlignment(Qt::AlignCenter);

        horizontalLayout_3->addWidget(lineEdit_2);


        verticalLayout_3->addWidget(widget_2);


        gridLayout->addWidget(widget_3, 1, 0, 1, 2);

        verticalSpacer = new QSpacerItem(20, 40, QSizePolicy::Minimum, QSizePolicy::Expanding);

        gridLayout->addItem(verticalSpacer, 5, 0, 1, 2);

        label_5 = new QLabel(Widget);
        label_5->setObjectName(QStringLiteral("label_5"));
        label_5->setStyleSheet(QStringLiteral("color:red"));
        label_5->setAlignment(Qt::AlignCenter);

        gridLayout->addWidget(label_5, 4, 0, 1, 2);

        verticalSpacer_2 = new QSpacerItem(20, 40, QSizePolicy::Minimum, QSizePolicy::Expanding);

        gridLayout->addItem(verticalSpacer_2, 3, 0, 1, 2);


        retranslateUi(Widget);

        QMetaObject::connectSlotsByName(Widget);
    } // setupUi

    void retranslateUi(QWidget *Widget)
    {
        Widget->setWindowTitle(QApplication::translate("Widget", "Form", nullptr));
        pushButton->setText(QApplication::translate("Widget", "\345\272\224\347\224\250", nullptr));
        pushButton_2->setText(QApplication::translate("Widget", "\351\207\215\347\275\256", nullptr));
        label->setText(QApplication::translate("Widget", "\345\257\206\347\240\201\350\256\277\351\227\256", nullptr));
        toolButton->setText(QString());
        label_4->setText(QApplication::translate("Widget", "\346\202\250\346\234\200\345\244\232\345\217\252\350\203\275\350\256\276\347\275\25620\344\275\215\345\257\206\347\240\201", nullptr));
        label_2->setText(QApplication::translate("Widget", "\347\253\257\345\217\243\350\256\276\347\275\256", nullptr));
        label_3->setText(QApplication::translate("Widget", "\347\253\257\345\217\243\345\217\267\357\274\232", nullptr));
        lineEdit_2->setText(QApplication::translate("Widget", "8080", nullptr));
        label_5->setText(QApplication::translate("Widget", "\350\257\267\346\243\200\346\237\245\345\241\253\345\206\231\346\230\257\345\220\246\345\220\210\346\263\225", nullptr));
    } // retranslateUi

};

namespace Ui {
    class Widget: public Ui_Widget {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_WIDGET_H
