#!/usr/bin/env python3
"""公共邮件发送工具"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import markdown as md_lib
from dotenv import load_dotenv

load_dotenv()

RECIPIENT_EMAIL = "mollyyang0406@gmail.com"
SMTP_HOST       = os.getenv("SMTP_HOST", "smtp.gmail.com")
SENDER_EMAIL    = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_APP_PASSWORD", "")


def send_html_email(subject: str, markdown_content: str, today: str = "") -> None:
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("⚠️  未配置邮件凭据，跳过发送。")
        return

    body_html = md_lib.markdown(markdown_content, extensions=["tables", "fenced_code"])
    html = f"""
    <html><head><meta charset="utf-8">
    <style>
      body  {{ font-family: -apple-system, Helvetica, Arial, sans-serif;
               max-width: 820px; margin: 40px auto; color: #333; line-height: 1.75; }}
      h1    {{ color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 8px; }}
      h2    {{ color: #0d47a1; margin-top: 32px; }}
      h3    {{ color: #1565c0; }}
      table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
      th,td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
      th    {{ background: #e8f0fe; }}
      a     {{ color: #1a73e8; }}
      code  {{ background: #f5f5f5; padding: 2px 6px; border-radius: 4px; font-family: monospace; }}
      pre   {{ background: #f5f5f5; padding: 16px; border-radius: 8px; overflow-x: auto; }}
      blockquote {{ border-left: 4px solid #1a73e8; margin: 0; padding-left: 16px; color: #555; }}
    </style></head>
    <body>{body_html}</body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = RECIPIENT_EMAIL
    msg.attach(MIMEText(markdown_content, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    port = int(os.getenv("SMTP_PORT", "465"))
    print(f"\n📧  发送邮件至 {RECIPIENT_EMAIL} …")
    if port == 465:
        with smtplib.SMTP_SSL(SMTP_HOST, port, timeout=15) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
    else:
        with smtplib.SMTP(SMTP_HOST, port, timeout=15) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
    print("✉️   邮件发送成功！")
