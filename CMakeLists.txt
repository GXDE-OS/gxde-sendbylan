cmake_minimum_required(VERSION 3.16)

project(gxde-sendbylan VERSION 4.0.0 LANGUAGES CXX C)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 REQUIRED COMPONENTS Core Widgets Network Svg DBus)

find_package(Dtk6 REQUIRED Core)

set(CMAKE_PREFIX_PATH "/usr/lib/x86_64-linux-gnu/cmake/Dtk2widget" ${CMAKE_PREFIX_PATH})
find_package(Dtk2widget REQUIRED)

qt_standard_project_setup()

set(QRCODE_SOURCES
    QRCode/bitstream.c
    QRCode/mask.c
    QRCode/mmask.c
    QRCode/mqrspec.c
    QRCode/qrencode.c
    QRCode/qrinput.c
    QRCode/qrspec.c
    QRCode/rscode.c
    QRCode/split.c
)

set(QRCODE_HEADERS
    QRCode/bitstream.h
    QRCode/config.h
    QRCode/mask.h
    QRCode/mmask.h
    QRCode/mqrspec.h
    QRCode/qrencode.h
    QRCode/qrencode_inner.h
    QRCode/qrinput.h
    QRCode/qrspec.h
    QRCode/rscode.h
    QRCode/split.h
)

set(SOURCES
    main.cpp
    mainwindow.cpp
    widget.cpp
    settingsdialog.cpp
    ${QRCODE_SOURCES}
)

set(HEADERS
    mainwindow.h
    widget.h
    config.h
    settingsdialog.h
    ${QRCODE_HEADERS}
)

set(FORMS
    widget.ui
)

set(RESOURCES
    icon.qrc
)

qt_add_executable(gxde-sendbylan
    ${SOURCES}
    ${HEADERS}
    ${FORMS}
    ${RESOURCES}
)

target_include_directories(gxde-sendbylan PRIVATE
    ${PROJECT_SOURCE_DIR}
    ${PROJECT_SOURCE_DIR}/QRCode
    ${DTK2WIDGET_INCLUDE_DIR}
    ${DtkCore_INCLUDE_DIRS}
)

target_link_libraries(gxde-sendbylan PRIVATE
    Qt6::Core
    Qt6::Widgets
    Qt6::Network
    Qt6::Svg
    Qt6::DBus
    ${Dtk2widget_LIBRARIES}
    Dtk6::Core
)

set(BINDIR "/opt/gxde-sendbylan" CACHE PATH "Install directory for binaries")

install(TARGETS gxde-sendbylan
    RUNTIME DESTINATION ${BINDIR}
)

install(FILES gxde-sendbylan.desktop
    DESTINATION /usr/share/deepin/gxde-file-manager/oem-menuextensions/
)

install(FILES gxde-sendbylan.desktop
    DESTINATION /usr/share/deepin/dde-file-manager/oem-menuextensions/
)

install(FILES ok.svg sendbylan.svg
    DESTINATION ${BINDIR}
)

install(PROGRAMS main.py
    DESTINATION ${BINDIR}
)

install(FILES error/403.html error/404.html
    DESTINATION ${BINDIR}/error
)