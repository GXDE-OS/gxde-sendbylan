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
    // folder being shared is needed for autostart Exec line
    explicit SettingsDialog(const QString &folder, QWidget *parent = nullptr);
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

    QString m_folder; // absolute path of shared directory

    QString configPath() const;
    QString autostartFilePath() const;
    void loadSettings();
    void saveSettings();
};

#endif // SETTINGSDIALOG_H
