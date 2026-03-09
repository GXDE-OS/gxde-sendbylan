#include "settingsdialog.h"
#include <QSpinBox>
#include <QCheckBox>
#include <QPushButton>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QFile>
#include <QDir>
#include <QTextStream>

SettingsDialog::SettingsDialog(QWidget *parent)
    : QDialog(parent)
{
    setWindowTitle(tr("高级设置"));

    m_portSpin = new QSpinBox(this);
    m_portSpin->setRange(1, 65535);
    m_portSpin->setSuffix(tr(" 端口"));
    m_autostart = new QCheckBox(tr("开机自启动"), this);

    m_ok = new QPushButton(tr("确定"), this);
    m_cancel = new QPushButton(tr("取消"), this);

    connect(m_ok, &QPushButton::clicked, this, &SettingsDialog::accept);
    connect(m_cancel, &QPushButton::clicked, this, &SettingsDialog::reject);

    QHBoxLayout *btnLayout = new QHBoxLayout;
    btnLayout->addStretch();
    btnLayout->addWidget(m_ok);
    btnLayout->addWidget(m_cancel);

    QVBoxLayout *mainLayout = new QVBoxLayout;
    mainLayout->addWidget(new QLabel(tr("端口号:"), this));
    mainLayout->addWidget(m_portSpin);
    mainLayout->addWidget(m_autostart);
    mainLayout->addStretch();
    mainLayout->addLayout(btnLayout);

    setLayout(mainLayout);
    loadSettings();
}

SettingsDialog::~SettingsDialog() {}

QString SettingsDialog::configPath() const {
    QString path = QDir::homePath() + "/.config/SBL/";
    QDir dir(path);
    if (!dir.exists())
        dir.mkpath(".");
    return path;
}

QString SettingsDialog::autostartFilePath() const {
    return QDir::homePath() + "/.config/autostart/gxde-sendbylan.desktop";
}

void SettingsDialog::loadSettings()
{
    // load port
    QFile portFile(configPath() + "port");
    if (portFile.open(QIODevice::ReadOnly | QIODevice::Text)) {
        QByteArray line = portFile.readLine().trimmed();
        bool ok;
        int port = line.toInt(&ok);
        if (ok)
            m_portSpin->setValue(port);
    } else {
        m_portSpin->setValue(8080);
    }
    portFile.close();

    // load autostart state
    QFile autoFile(autostartFilePath());
    m_autostart->setChecked(autoFile.exists());
}

void SettingsDialog::saveSettings()
{
    // save port
    QFile portFile(configPath() + "port");
    if (portFile.open(QIODevice::WriteOnly | QIODevice::Text)) {
        QTextStream out(&portFile);
        out << m_portSpin->value();
    }
    portFile.close();

    // handle autostart
    QFile autoFile(autostartFilePath());
    if (m_autostart->isChecked()) {
        QDir dir(QDir::homePath() + "/.config/autostart/");
        if (!dir.exists())
            dir.mkpath(".");
        // create using path string to avoid copying QFile
        QFile f(autostartFilePath());
        if (f.open(QIODevice::WriteOnly | QIODevice::Text)) {
            QTextStream out(&f);
            out << "[Desktop Entry]\n"
                << "Type=Application\n"
                << "Name=GXDE Sendbylan\n"
                << "Exec=/opt/gxde-sendbylan/main\n"
                << "X-GNOME-Autostart-enabled=true\n";
        }
        f.close();
    } else {
        if (autoFile.exists())
            autoFile.remove();
    }
}

void SettingsDialog::accept()
{
    saveSettings();
    emit settingsChanged();
    QDialog::accept();
}
