---
name: email-advanced
description: 邮件高级操作 — himalaya + python-imap双方案。触发：email、IMAP、SMTP。
triggers:
  - email
  - 邮件
  - IMAP
  - SMTP
  - 发送邮件
version: "1.0"
author: Hermes Agent
created: 2026-08-10
tags:
  - email
  - imap
  - smtp
  - himalaya
  - python
---

# Email Advanced Skill

邮件高级操作双方案：himalaya CLI（生产级） + python-imap（无依赖备选）。

---

## 方案A — himalaya CLI（推荐）

### A1. 安装

```bash
brew install himalaya
himalaya --version   # 验证安装
```

### A2. 配置多账号

```bash
# 添加第一个账号（交互式引导）
himalaya config add personal

# 手动指定参数
himalaya config add work \
  --imap-host imap.example.com \
  --imap-port 993 \
  --imap-user user@work.example.com \
  --imap-passwd-cmd "security find-internet-password -s imap.example.com -a user@work.example.com -w" \
  --smtp-host smtp.example.com \
  --smtp-port 587 \
  --smtp-user user@work.example.com \
  --smtp-passwd-cmd "security find-internet-password -s smtp.example.com -a user@work.example.com -w" \
  --tls true \
  --from "User Name <user@example.com>"
```

**关键参数说明：**

| 参数 | 说明 |
|------|------|
| `--tls true` | 使用 IMAP port 993（SSL加密）|
| `--tls false --starttls true` | 使用 IMAP port 143（STARTTLS）|
| `--smtp-tls true` | SMTP 465（SSL） |
| `--smtp-starttls true` | SMTP 587（STARTTLS）|

### A3. 切换账号

```bash
himalaya config account    # 查看当前账号
himalaya config account work   # 切换到work账号
```

### A4. 发送邮件

```bash
# 从文件发送
himalaya email send < mail_body.txt

# 文件格式（RFC 5322）
# ---
# To: recipient@example.com
# Subject: Hello
# From: Your Name <you@example.com>
# ---
# Email body here
```

```bash
# 直接发送
himalaya email send \
  --to recipient@example.com \
  --subject "Hello" \
  --body "Email content"
```

### A5. 读取邮件

```bash
# 列出收件箱（默认50条）
himalaya email list

# 指定文件夹和数量
himalaya email list --folder INBOX --limit 20

# 查看指定邮件ID正文
himalaya email view 1
himalaya email view 1 --raw    # 显示原始邮件头
```

### A6. 文件夹/标签管理

```bash
himalaya email list folders          # 列出所有文件夹
himalaya email move 10 INBOX.Sent   # 移动邮件到已发送
himalaya email copy 10 INBOX.Archive # 复制邮件
himalaya email delete 10            # 删除邮件
```

### A7. 搜索邮件

```bash
himalaya email search "from:boss Subject:report" --folder INBOX
himalaya email search "since:2026-01-01 before:2026-08-01" --folder INBOX
```

---

## 方案B — python-imap（无依赖备选）

> Python 3自带imaplib/smtplib，无须安装额外包。

### B1. 连接IMAP服务器

```python
python3 -c "
import imaplib, getpass

# SSL连接 (port 993)
mail = imaplib.IMAP4_SSL('imap.example.com', 993)

# 或 STARTTLS (port 143)
# mail = imaplib.IMAP4('imap.example.com', 143)
# mail.starttls()

mail.login('user@example.com', getpass.getpass())
print('Connected:', mail.capabilities)
mail.logout()
"
```

### B2. 列出文件夹

```python
python3 -c "
import imaplib
mail = imaplib.IMAP4_SSL('imap.example.com', 993)
mail.login('user@example.com', 'password')
status, folders = mail.list()
for f in folders:
    print(f.decode())
mail.logout()
"
```

### B3. 搜索并读取邮件

```python
python3 -c "
import imaplib, email
from email.header import decode_header

mail = imaplib.IMAP4_SSL('imap.example.com', 993)
mail.login('user@example.com', 'password')
mail.select('INBOX')

status, messages = mail.search(None, 'ALL')
mail_ids = messages[0].split()
for mid in mail_ids[-10:]:
    status, data = mail.fetch(mid, '(RFC822)')
    msg = email.message_from_bytes(data[0][1])
    subject, enc = decode_header(msg['Subject'])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(enc or 'utf-8')
    print(f'From: {msg[\"From\"]} | Subject: {subject}')
mail.logout()
"
```

### B4. 发送邮件（SMTP）

```python
python3 -c "
import smtplib, email.utils
from email.message import EmailMessage

msg = EmailMessage()
msg['To'] = 'recipient@example.com'
msg['From'] = email.utils.formataddr(('Your Name', 'you@example.com'))
msg['Subject'] = 'Hello from Python'
msg.set_content('Email body text')

# SMTP SSL (port 465)
with smtplib.SMTP_SSL('smtp.example.com', 465) as server:
    server.login('you@example.com', 'password')
    server.send_message(msg)

# 或 SMTP STARTTLS (port 587)
# with smtplib.SMTP('smtp.example.com', 587) as server:
#     server.starttls()
#     server.login('you@example.com', 'password')
#     server.send_message(msg)
print('Sent successfully')
"
```

### B5. 移动/删除邮件

```python
python3 -c "
import imaplib
mail = imaplib.IMAP4_SSL('imap.example.com', 993)
mail.login('user@example.com', 'password')
mail.select('INBOX')
mail.copy('10', 'INBOX.Archive')
mail.store('10', '+FLAGS', '(\\Deleted)')
mail.expunge()
mail.logout()
"
```

---

## 坑点汇总

### 🔴 端口混淆（最常见）

| 协议 | 加密类型 | Port |
|------|----------|------|
| IMAP | SSL/TLS | **993** |
| IMAP | STARTTLS | 143 |
| SMTP | SSL/TLS | **465** |
| SMTP | STARTTLS | **587** |

### 🔴 himalaya `--tls` vs `--starttls`

```bash
# IMAP SSL → port 993 + --tls true
himalaya config add personal --imap-host imap.gmail.com --imap-port 993 --tls true

# IMAP STARTTLS → port 143 + --starttls true
himalaya config add personal --imap-host imap.gmail.com --imap-port 143 --starttls true
```

### 🔴 Gmail必须用应用密码

Gmail不支持直接密码认证。**必须开启两步验证后生成应用密码**：
```
Google Account → Security → 2-Step Verification → App Passwords
```

### 🔴 多账号切换

```bash
himalaya config account          # 查看当前账号
himalaya config account <name>   # 切换账号
```

### 🔴 STARTTLS证书错误（临时跳过，仅测试用）

```python
import ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
mail = imaplib.IMAP4_SSL('imap.example.com', 993, ssl_context=ctx)
```

### 🔴 中文乱码

```python
from email.mime.text import MIMEText
msg = MIMEText('正文内容', 'plain', 'utf-8')  # 必须指定utf-8
```

### 🔴 multipart邮件正文读取

```python
if msg.is_multipart():
    for part in msg.walk():
        if part.get_content_type() == 'text/plain':
            print(part.get_payload(decode=True).decode())
else:
    print(msg.get_payload(decode=True).decode())
```

---

## 验证步骤

### 验证1 — himalaya可执行
```bash
himalaya --version
himalaya config account
```

### 验证2 — 读取收件箱
```bash
himalaya email list --limit 5
```
期望：列出最近5封邮件的 From / Subject / Date。

### 验证3 — 发送测试邮件
```bash
cat > /tmp/test_mail.txt << 'EOF'
To: your_other_email@example.com
Subject: Hermes Email Skill Test
From: Your Name <your_email@example.com>

This is a test email sent via the email-advanced skill.
EOF
himalaya email send < /tmp/test_mail.txt
echo "Exit code: $?"   # 0 = 成功
```

### 验证4 — Python IMAP连接
```bash
python3 -c "import imaplib; m=imaplib.IMAP4_SSL('imap.gmail.com',993); print(m.capabilities); m.logout(); print('OK')"
```

### 验证5 — Python SMTP发送
```bash
python3 -c "
import smtplib, email.utils
from email.message import EmailMessage
msg=EmailMessage()
msg['To']='your_other_email@example.com'
msg['From']=email.utils.formataddr(('Test','your_email@example.com'))
msg['Subject']='Python SMTP Test'
msg.set_content('Test')
with smtplib.SMTP_SSL('smtp.gmail.com',465) as s:
    s.login('your_email@gmail.com','your_app_password')
    s.send_message(msg)
print('Sent OK')
"
```

---

## 快速参考

```bash
# himalaya
himalaya email list                        # 列出收件箱
himalaya email view <id>                  # 查看邮件
himalaya email send < file.txt            # 发送邮件
himalaya email move <id> INBOX.Archive    # 归档
himalaya config account                   # 查看/切换账号

# python 一行发送
python3 -c "import smtplib,ssl; msg=open('mail.txt').read(); \
  with smtplib.SMTP_SSL('smtp.example.com',465) as s: \
    s.login('u','p'); s.sendmail('u@x','y@z',msg)"
```