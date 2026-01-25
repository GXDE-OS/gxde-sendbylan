#-------------------------------------------------
#
# Project created by QtCreator 2019-06-30T12:53:03
#
#-------------------------------------------------

QT       += core gui network svg

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

TARGET = filesend
TEMPLATE = app

# The following define makes your compiler emit warnings if you use
# any feature of Qt which as been marked as deprecated (the exact warnings
# depend on your compiler). Please consult the documentation of the
# deprecated API in order to know how to port your code away from it.
DEFINES += QT_DEPRECATED_WARNINGS

# You can also make your code fail to compile if you use deprecated APIs.
# In order to do so, uncomment the following line.
# You can also select to disable deprecated APIs only up to a certain version of Qt.
#DEFINES += QT_DISABLE_DEPRECATED_BEFORE=0x060000    # disables all the APIs deprecated before Qt 6.0.0
# Get build version from qmake
VERSION = $$BUILD_VERSION
isEmpty(VERSION): VERSION = 4.0.0
DEFINES += APP_VERSION=\\\"'$${VERSION}'\\\"
DEFINES += APP_BRANCH=\\\"'$$system(git symbolic-ref --short -q HEAD)'\\\"


SOURCES += main.cpp\
        mainwindow.cpp \
    widget.cpp \


HEADERS  += mainwindow.h \
    widget.h \
    config.h

CONFIG += link_pkgconfig
PKGCONFIG += dtkwidget

CONFIG += c++11

FORMS += \
    widget.ui
include(QRCode/QRCode.pri)

isEmpty(BINDIR):BINDIR=/opt/gxde-sendbylan
isEmpty(APPDIR):FILEOEMDIR=/usr/share/deepin/gxde-file-manager/oem-menuextensions/
FILEOEMDIRDFM=/usr/share/deepin/dde-file-manager/oem-menuextensions/
target.path = $$INSTROOT$$BINDIR

desktop.path = $$INSTROOT$$FILEOEMDIR
desktop.files = $$PWD/gxde-sendbylan.desktop

desktop-dfm.path = $$INSTROOT$$FILEOEMDIRDFM
desktop-dfm.files = $$PWD/gxde-sendbylan.desktop

icon.path = $$INSTROOT$$BINDIR
icon.files = $$PWD/*.svg

serverFile.path = $$INSTROOT$$BINDIR
serverFile.files = $$PWD/main.py

403Page.path = $$INSTROOT$$BINDIR/error
403Page.files = $$PWD/error/403.html

404Page.path = $$INSTROOT$$BINDIR/error
404Page.files = $$PWD/error/404.html

INSTALLS += target desktop desktop-dfm icon serverFile 403Page 404Page

RESOURCES += \
    icon.qrc
