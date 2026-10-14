#include "settingsdialog.h"
#include "sblconfig.h"
#include <QCheckBox>
#include <QComboBox>
#include <QCoreApplication>
#include <QDir>
#include <QFile>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QSpinBox>
#include <QTextStream>
#include <QVBoxLayout>

SettingsDialog::SettingsDialog(const QString &folder, QWidget *parent)
    : QDialog(parent), m_folder(folder)
{
    setWindowTitle(tr("高级设置"));

    m_portSpin = new QSpinBox(this);
    m_portSpin->setRange(1, 65535);
    m_portSpin->setSuffix(tr(" 端口"));

    m_protocolBox = new QComboBox(this);
    // data 里的值就是传给 server.py -p 的参数
    m_protocolBox->addItem(tr("网页 + WebDAV（推荐，可挂载为网络位置）"), QStringLiteral("webdav"));
    m_protocolBox->addItem(tr("仅网页浏览 / 下载 / 上传"), QStringLiteral("http"));
    m_protocolBox->addItem(tr("SMB 共享（Windows 可直接访问，需要管理员权限）"), QStringLiteral("smb"));

    m_protocolHint = new QLabel(this);
    m_protocolHint->setWordWrap(true);
    m_protocolHint->setStyleSheet(QStringLiteral("color: #808080;"));

    m_uploadCheck = new QCheckBox(tr("允许接收端在网页里上传文件"), this);

    m_shareNameEdit = new QLineEdit(this);
    m_shareNameEdit->setPlaceholderText(tr("留空则使用文件夹名"));

    m_autostart = new QCheckBox(tr("开机自启动"), this);

    m_ok = new QPushButton(tr("确定"), this);
    m_cancel = new QPushButton(tr("取消"), this);

    connect(m_ok, &QPushButton::clicked, this, &SettingsDialog::accept);
    connect(m_cancel, &QPushButton::clicked, this, &SettingsDialog::reject);
    connect(m_protocolBox, &QComboBox::currentTextChanged, this, &SettingsDialog::updateProtocolHint);

    QHBoxLayout *btnLayout = new QHBoxLayout;
    btnLayout->addStretch();
    btnLayout->addWidget(m_ok);
    btnLayout->addWidget(m_cancel);

    QVBoxLayout *mainLayout = new QVBoxLayout;
    mainLayout->addWidget(new QLabel(tr("端口号:"), this));
    mainLayout->addWidget(m_portSpin);
    mainLayout->addWidget(new QLabel(tr("共享方式:"), this));
    mainLayout->addWidget(m_protocolBox);
    mainLayout->addWidget(m_protocolHint);
    mainLayout->addWidget(m_uploadCheck);
    mainLayout->addWidget(new QLabel(tr("SMB 共享名:"), this));
    mainLayout->addWidget(m_shareNameEdit);
    mainLayout->addWidget(m_autostart);
    mainLayout->addStretch();
    mainLayout->addLayout(btnLayout);

    setLayout(mainLayout);
    loadSettings();
    updateProtocolHint();
}

SettingsDialog::~SettingsDialog() {}

QString SettingsDialog::autostartFilePath() const {
    return QDir::homePath() + "/.config/autostart/gxde-sendbylan.desktop";
}

void SettingsDialog::updateProtocolHint()
{
    const QString current = m_protocolBox->currentData().toString();
    const bool isSmb = current == QLatin1String("smb");

    if (isSmb) {
        m_protocolHint->setText(tr("SMB 使用 445 端口时需要 root 权限；若使用其它端口，"
                                   "请在地址后带上端口访问（Windows 资源管理器不支持自定义端口）。"));
    } else if (current == QLatin1String("http")) {
        m_protocolHint->setText(tr("只提供网页浏览、下载与上传，不支持挂载为网络位置。"));
    } else {
        m_protocolHint->setText(tr("浏览器可直接访问，也可以在文件管理器或手机中"
                                   "添加 WebDAV 网络位置（如 KDE/GNOME 文件管理器、ES 文件浏览器）。"));
    }

    m_uploadCheck->setEnabled(!isSmb);
    m_shareNameEdit->setEnabled(isSmb);
}

void SettingsDialog::loadSettings()
{
    bool ok = false;
    const int port = SBL::readValue(QStringLiteral("port"), QStringLiteral("8080")).toInt(&ok);
    m_portSpin->setValue(ok ? port : 8080);

    const QString protocol = SBL::protocol();
    const int protocolIndex = m_protocolBox->findData(protocol);
    m_protocolBox->setCurrentIndex(protocolIndex >= 0 ? protocolIndex : 0);

    m_uploadCheck->setChecked(SBL::uploadEnabled());
    m_shareNameEdit->setText(SBL::readValue(QStringLiteral("smb_share")));

    QFile autoFile(autostartFilePath());
    m_autostart->setChecked(autoFile.exists());
}

void SettingsDialog::saveSettings()
{
    SBL::writeValue(QStringLiteral("port"), QString::number(m_portSpin->value()));
    SBL::writeValue(QStringLiteral("protocol"), m_protocolBox->currentData().toString());
    SBL::writeValue(QStringLiteral("upload"), m_uploadCheck->isChecked() ? QStringLiteral("1") : QStringLiteral("0"));
    SBL::writeValue(QStringLiteral("smb_share"), m_shareNameEdit->text().trimmed());

    QFile autoFile(autostartFilePath());
    if (m_autostart->isChecked()) {
        QDir dir(QDir::homePath() + "/.config/autostart/");
        if (!dir.exists())
            dir.mkpath(".");
        QFile f(autostartFilePath());
        if (f.open(QIODevice::WriteOnly | QIODevice::Text)) {
            QTextStream out(&f);
            out << "[Desktop Entry]\n"
                << "Type=Application\n"
                << "Name=GXDE Sendbylan\n";
            QString execPath = QCoreApplication::applicationFilePath();
            out << "Exec=" << execPath;
            if (!m_folder.isEmpty()) {
                out << " " << m_folder;
            }
            out << "\n";
            out << "X-GNOME-Autostart-enabled=true\n";
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
