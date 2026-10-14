#ifndef SBLCONFIG_H
#define SBLCONFIG_H

#include <QAbstractSocket>
#include <QDir>
#include <QFile>
#include <QHostAddress>
#include <QNetworkInterface>
#include <QString>
#include <QStringList>
#include <QTextStream>

#include <unistd.h>

#include "config.h"

/*
 * 这里集中处理与 python 服务端（server.py）相关的配置与启动逻辑。
 * 配置文件沿用老版本的位置：~/.config/SBL/<键名>，新键为 protocol/upload/smb_share。
 */
namespace SBL {

inline QString configDir()
{
    const QString path = QDir::homePath() + "/.config/SBL/";
    QDir dir(path);
    if (!dir.exists())
        dir.mkpath(".");
    return path;
}

inline QString readValue(const QString &key, const QString &fallback = QString())
{
    QFile file(configDir() + key);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text))
        return fallback;
    const QString value = QString::fromUtf8(file.readLine()).trimmed();
    return value.isEmpty() ? fallback : value;
}

inline void writeValue(const QString &key, const QString &value)
{
    QFile file(configDir() + key);
    if (!file.open(QIODevice::WriteOnly | QIODevice::Text | QIODevice::Truncate))
        return;
    QTextStream out(&file);
    out << value;
}

/* 共享端口，默认 8080（与旧版本一致） */
inline QString port()
{
    return readValue("port", "8080");
}

/* 共享协议：http（默认，与原行为一致）、webdav（可挂载）、smb */
inline QString protocol()
{
    return readValue("protocol", "http");
}

/* 是否允许接收端在网页里上传文件，默认开启 */
inline bool uploadEnabled()
{
    return readValue("upload", "1") != "0";
}

/* 把任意名字整理成合法的 SMB 共享名：与 server.py 的 sanitize_share_name 保持一致 */
inline QString sanitizeShareName(const QString &name)
{
    QString cleaned;
    for (const QChar &ch : name) {
        const bool safe = (ch >= '0' && ch <= '9')
                || (ch >= 'A' && ch <= 'Z')
                || (ch >= 'a' && ch <= 'z')
                || ch == '.' || ch == '_' || ch == '-' || ch == '$';
        cleaned.append(safe ? ch : QChar('-'));
    }
    while (cleaned.startsWith('-'))
        cleaned.remove(0, 1);
    while (cleaned.endsWith('-'))
        cleaned.chop(1);
    return cleaned.isEmpty() ? QStringLiteral("share") : cleaned;
}

inline QString shareName(const QString &folderPath)
{
    const QString configured = readValue("smb_share");
    const QString candidate = configured.isEmpty() ? QDir(folderPath).dirName() : configured;
    return sanitizeShareName(candidate);
}

/* 用单引号包裹，避免共享目录里的空格/引号把命令行拆坏 */
inline QString shellQuote(const QString &value)
{
    QString escaped = value;
    escaped.replace("'", "'\\''");
    return "'" + escaped + "'";
}

/* 与 server.py 命令行一一对应的启动参数 */
inline QString serverCommand(const QString &folderPath)
{
    const QString currentProtocol = protocol();

    QStringList parts;
    parts << shellQuote(QStringLiteral(SERVER_SCRIPT))
          << shellQuote(port())
          << QStringLiteral("-d") << shellQuote(folderPath)
          << QStringLiteral("-p") << shellQuote(currentProtocol)
          << QStringLiteral("--brand") << shellQuote(QStringLiteral("GXDE Sendbylan"))
          << QStringLiteral("--error-pages") << shellQuote(QStringLiteral(ERROR_PAGES_DIR));

    if (currentProtocol == QLatin1String("smb")) {
        // SMB 客户端不使用网页上传，这里只需要共享名
        parts << QStringLiteral("--smb-share") << shellQuote(shareName(folderPath));
    } else if (uploadEnabled()) {
        parts << QStringLiteral("--upload");
    }

    return parts.join(QLatin1Char(' '));
}

inline bool writeLauncherScript(const QString &folderPath)
{
    QFile launcher(QStringLiteral(SBL_LAUNCHER_SCRIPT));
    if (!launcher.open(QIODevice::WriteOnly | QIODevice::Text | QIODevice::Truncate))
        return false;

    QTextStream out(&launcher);
    out << "#!/bin/sh\n";
    out << "exec " << serverCommand(folderPath) << "\n";
    launcher.close();

    QFile::setPermissions(QStringLiteral(SBL_LAUNCHER_SCRIPT),
                          QFile::ReadOwner | QFile::WriteOwner | QFile::ExeOwner
                          | QFile::ReadGroup | QFile::ExeGroup
                          | QFile::ReadOther | QFile::ExeOther);
    return true;
}

inline void startServer(const QString &folderPath)
{
    if (!writeLauncherScript(folderPath))
        return;
    system((QStringLiteral(SBL_LAUNCHER_SCRIPT) + " &").toUtf8().constData());
}

/* 只结束本程序启动的 server.py，避免像旧版本那样 pkill 掉系统里所有 python 进程 */
inline void stopServer()
{
    const QString pattern = shellQuote(QStringLiteral(SERVER_SCRIPT));
    system(QString("pkill -f %1").arg(pattern).toUtf8().constData());
}

inline bool isPrivateIPv4(const QString &ip)
{
    const QStringList parts = ip.split(QLatin1Char('.'));
    if (parts.size() != 4)
        return false;

    bool ok = false;
    const int first = parts.at(0).toInt(&ok);
    if (!ok)
        return false;
    const int second = parts.at(1).toInt(&ok);
    if (!ok)
        return false;

    if (first == 10)
        return true;
    if (first == 192 && second == 168)
        return true;
    if (first == 172 && second >= 16 && second <= 31)
        return true;
    return false;
}

/* 优先返回局域网内网 IPv4 地址，方便手机扫码 */
inline QString preferredAddress()
{
    QString fallback;
    const QList<QHostAddress> addresses = QNetworkInterface::allAddresses();
    for (const QHostAddress &address : addresses) {
        if (address.protocol() != QAbstractSocket::IPv4Protocol)
            continue;
        if (address.isLoopback())
            continue;

        const QString ip = address.toString();
        if (isPrivateIPv4(ip))
            return ip;
        if (fallback.isEmpty())
            fallback = ip;
    }
    return fallback;
}

/* 分享地址：WebDAV/HTTP 给浏览器或挂载用，SMB 给文件管理器用 */
inline QString shareUrl(const QString &address, const QString &folderPath)
{
    const QString currentPort = port();

    if (protocol() == QLatin1String("smb")) {
        const QString host = currentPort.isEmpty() || currentPort == QLatin1String("445")
                ? address
                : address + QLatin1Char(':') + currentPort;
        return QStringLiteral("smb://%1/%2").arg(host, shareName(folderPath));
    }
    return QStringLiteral("http://%1:%2/").arg(address, currentPort);
}

inline QString addressHint()
{
    const QString currentProtocol = protocol();
    if (currentProtocol == QLatin1String("smb"))
        return QStringLiteral("SMB 共享地址（Windows 资源管理器 / 手机文件管理器）：");
    if (currentProtocol == QLatin1String("webdav"))
        return QStringLiteral("浏览器访问，或作为 WebDAV 网络位置挂载：");
    return QStringLiteral("在接受端浏览器中输入：");
}

/* 返回需要提醒用户的注意事项，没有则返回空字符串 */
inline QString warningText()
{
    if (protocol() == QLatin1String("smb") && geteuid() != 0)
        return QStringLiteral("提示：SMB 默认端口 445 需要管理员权限，当前不是以 root 运行，共享可能无法启动。");
    return QString();
}

} // namespace SBL

#endif // SBLCONFIG_H
