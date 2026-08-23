---
name: email-advanced
description: "邮件IMAP/SMTP — himalaya配置 + python-imap编程接口"
triggers:
  - email
  - 邮件
  - IMAP
  - SMTP
  - 发送邮件
  - 邮件读取
  - himalaya
version: "1.0.0"
author: Hermes Agent
created: "2026-08-10"
tags:
  - email
  - imap
  - smtp
  - himalaya
---

# Email Advanced — 邮件 IMAP/SMTP 操作

Mac mini M4 (macOS 26.5) 邮件操作技能，两套方案：himalaya CLI（推荐）和 Python imaplib（备用）。

---

## 方案 A：himalaya CLI（推荐）

### 安装

```bash
brew install himalaya
himalaya --version
```

### 配置账号

```bash
# 交互式配置（推荐先走一遍）
himalaya config setup

# 手动添加QQ邮箱示例
himalaya config add default \
  --name "Your Name" \
  --email "yourname@qq.com" \
  --imap-host "imap.qq.com" \
  --imap-port 993 \
  --imap-tls on \
  --smtp-host "smtp.qq.com" \
  --smtp-port 465 \
  --smtp-tls on

# 列出配置
himalaya config list
```

常见邮箱配置参考：

| 邮箱 | IMAP主机 | IMAP端口 | SMTP主机 | SMTP端口 |
|------|----------|----------|----------|----------|
| QQ邮箱 | imap.qq.com | 993 | smtp.qq.com | 465 |
| 163邮箱 | imap.163.com | 993 | smtp.163.com | 465 |
| Gmail | imap.gmail.com | 993 | smtp.gmail.com | 465 |

### 发送邮件

```bash
# 从stdin发送
echo "邮件正文" | himalaya email send \
  --from "yourname@qq.com" \
  --to "recipient@example.com" \
  --subject "主题"

# 从文件发送
himalaya email send < email_body.txt \
  --from "yourname@qq.com" \
  --to "recipient@example.com" \
  --subject "测试邮件"

# 带附件
himalaya email send --file /path/to/attachment.txt \
  --from "yourname@qq.com" \
  --to "recipient@example.com" \
  --subject "带附件的邮件"
```

### 读取邮件

```bash
# 列出收件箱（最新20封）
himalaya email list -w 30

# 查看指定邮件
himalaya email view <message_id>

# 搜索邮件
himalaya email search "subject:报告 from:boss@company.com"

# 移动邮件到文件夹
himalaya email move <message_id> +Archive
```

### SMTP授权码

QQ/163邮箱需要授权码而非登录密码：
1. 登录网页邮箱 → 设置 → 账户
2. 开启IMAP/SMTP服务
3. 生成授权码
4. `himalaya config` 中使用授权码作为密码

---

## 方案 B：python-imap（无需安装）

Python 内置 `imaplib`，无需任何依赖。

### 连接 IMAP 并读取邮件

```python
import imaplib
import email
from email.header import decode_header

def decode_str(s):
    """解码邮件header字符串"""
    if not s:
        return ""
    parts = decode_header(s)
    result = []
    for part, charset in parts:
        if isinstance(part, bytes):
            charset = charset or 'utf-8'
            result.append(part.decode(charset, errors='replace'))
        else:
            result.append(part)
    return ''.join(result)

def list_folders():
    """列出所有文件夹"""
    mail = imaplib.IMAP4_SSL('imap.qq.com', 993)
    mail.login('yourname@qq.com', 'your_auth_code')
    
    # 列出所有文件夹
    status, folders = mail.list()
    for folder in folders:
        print(folder.decode())
    
    mail.logout()

def read_inbox(limit=10):
    """读取最近N封邮件"""
    mail = imaplib.IMAP4_SSL('imap.qq.com', 993)
    mail.login('yourname@qq.com', 'your_auth_code')
    mail.select('INBOX')
    
    # 搜索所有邮件，取最新limit封
    status, messages = mail.search(None, 'ALL')
    mail_ids = messages[0].split()
    recent = mail_ids[-limit:] if len(mail_ids) > limit else mail_ids
    
    for uid in reversed(recent):
        status, msg_data = mail.fetch(uid, '(RFC822)')
        msg = email.message_from_bytes(msg_data[0][1])
        
        subject = decode_str(msg['Subject'])
        sender = decode_str(msg['From'])
        date = msg['Date']
        
        print(f"ID: {uid.decode()}")
        print(f"发件人: {sender}")
        print(f"主题: {subject}")
        print(f"时间: {date}")
        print("-" * 40)
    
    mail.logout()

def search_emails(subject=None, sender=None, since=None):
    """搜索邮件"""
    mail = imaplib.IMAP4_SSL('imap.qq.com', 993)
    mail.login('yourname@qq.com', 'your_auth_code')
    mail.select('INBOX')
    
    criteria = []
    if subject:
        criteria.append(f'SUBJECT {subject}')
    if sender:
        criteria.append(f'FROM {sender}')
    if since:
        criteria.append(f'SINCE {since}')
    
    search_string = ' '.join(criteria)
    status, messages = mail.search(None, search_string)
    ids = messages[0].split()
    
    print(f"找到 {len(ids)} 封邮件:")
    for uid in ids[:20]:
        status, msg_data = mail.fetch(uid, '(RFC822)')
        msg = email.message_from_bytes(msg_data[0][1])
        print(f"  {decode_str(msg['From'])} | {decode_str(msg['Subject'])} | {msg['Date']}")
    
    mail.logout()
    return ids

# 运行
if __name__ == "__main__":
    read_inbox(5)
    # search_emails(sender='noreply@alipay.com')
```

### 发送邮件（SMTP）

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to_addr, subject, body, from_addr=None, password=None):
    """发送邮件"""
    from_addr = from_addr or 'yourname@qq.com'
    password = password or 'your_auth_code'  # QQ邮箱授权码
    
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    with smtplib.SMTP_SSL('smtp.qq.com', 465) as server:
        server.login(from_addr, password)
        server.sendmail(from_addr, [to_addr], msg.as_string())
    
    print(f"✅ 邮件已发送至 {to_addr}")

def send_email_with_attachment(to_addr, subject, body, attachment_path):
    """发送带附件的邮件"""
    from email.mime.base import MIMEBase
    from email import encoders
    
    from_addr = 'yourname@qq.com'
    password = 'your_auth_code'
    
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    with open(attachment_path, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{attachment_path}"')
        msg.attach(part)
    
    with smtplib.SMTP_SSL('smtp.qq.com', 465) as server:
        server.login(from_addr, password)
        server.sendmail(from_addr, [to_addr], msg.as_string())
    
    print(f"✅ 带附件邮件已发送")

if __name__ == "__main__":
    send_email(
        to_addr='recipient@example.com',
        subject='测试邮件',
        body='这是邮件正文'
    )
```

---

## 常见坑点

### IMAP 坑

1. **port 993 vs 143**：993是IMAP SSL（推荐），143是STARTTLS（需后握手）
2. **授权码 ≠ 密码**：QQ/163/企业邮箱用授权码，Gmail用应用专用密码
3. **文件夹名称编码**：中文文件夹名可能编码为 `&- 中文 -`，需正确解码
4. **中文搜索**：IMAP SEARCH对中文支持差，可用Python正则过滤
5. **连接超时**：网络慢时imaplib默认10s超时偏短，可设 `mail.shutdown()`

### SMTP 坑

1. **port 465 vs 587**：465是SMTPS（直接SSL），587是SUBMISSION（STARTTLS）
2. **QQ邮箱limit**：每月最多500封，超限会报 `554 DT:SPM`
3. **附件中文名**：需 `email.header.encode` 处理

---

## 验证

```bash
# 验证himalaya配置
himalaya config list && echo "✅ himalaya配置正常"

# 用python验证IMAP连接
python3 -c "
import imaplib
try:
    m = imaplib.IMAP4_SSL('imap.qq.com', 993)
    print('✅ IMAP连接成功')
    m.logout()
except Exception as e:
    print(f'❌ 连接失败: {e}')
"

# 发送测试邮件
python3 -c "
import smtplib
from email.mime.text import MIMEText
msg = MIMEText('test', 'plain', 'utf-8')
msg['From'] = 'yourname@qq.com'
msg['To'] = 'yourname@qq.com'
msg['Subject'] = 'Hermes邮件测试'
with smtplib.SMTP_SSL('smtp.qq.com', 465) as s:
    s.login('yourname@qq.com', 'your_auth_code')
    s.sendmail('yourname@qq.com', ['yourname@qq.com'], msg.as_string())
print('✅ 邮件发送成功')
"
```
