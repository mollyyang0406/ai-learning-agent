#!/usr/bin/env python3
"""快速测试：读取 daily_plan.md 并发送邮件"""
from main import send_email
from datetime import date

today = date.today().strftime("%Y年%m月%d日")
send_email(today)
