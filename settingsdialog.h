#ifndef SETTINGSDIALOG_H
#define SETTINGSDIALOG_H

#include <QDialog>

class QCheckBox;
class QComboBox;
class QLabel;
class QLineEdit;
class QPushButton;
class QSpinBox;

class SettingsDialog : public QDialog
{
    Q_OBJECT
public:
    explicit SettingsDialog(const QString &folder, QWidget *parent = nullptr);
    ~SettingsDialog();

signals:
    void settingsChanged();

private slots:
    void accept() override;
    void updateProtocolHint();

private:
    QSpinBox *m_portSpin;
    QComboBox *m_protocolBox;
    QLabel *m_protocolHint;
    QCheckBox *m_uploadCheck;
    QLineEdit *m_shareNameEdit;
    QCheckBox *m_autostart;
    QPushButton *m_ok;
    QPushButton *m_cancel;

    QString m_folder;

    QString autostartFilePath() const;
    void loadSettings();
    void saveSettings();
};

#endif // SETTINGSDIALOG_H
