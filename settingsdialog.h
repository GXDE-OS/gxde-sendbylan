#ifndef SETTINGSDIALOG_H
#define SETTINGSDIALOG_H

#include <QDialog>

class QSpinBox;
class QCheckBox;
class QPushButton;

class SettingsDialog : public QDialog
{
    Q_OBJECT
public:
    explicit SettingsDialog(QWidget *parent = nullptr);
    ~SettingsDialog();

signals:
    void settingsChanged();

private slots:
    void accept() override;

private:
    QSpinBox *m_portSpin;
    QCheckBox *m_autostart;
    QPushButton *m_ok;
    QPushButton *m_cancel;

    QString configPath() const;
    QString autostartFilePath() const;
    void loadSettings();
    void saveSettings();
};

#endif // SETTINGSDIALOG_H
