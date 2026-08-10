#!/usr/bin/env python3
"""
Step 3 - 邮件回复监听器
- 每天美东时间中午 12:00 检查一次收件箱
- 检测到对 [AI日报] 邮件的回复后，提取反馈内容
- 自动触发 generate_plan.py 生成学习计划
"""

import email
import imaplib
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from email.header import decode_header
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

SENDER_EMAIL    = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_APP_PASSWORD", "")
IMAP_HOST       = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT       = int(os.getenv("IMAP_PORT", "993"))

EASTERN = ZoneInfo("America/New_York")
CHECK_HOUR = 12  # 美东时间 12:00


def decode_str(s: str) -> str:
    """解码邮件头"""
    parts = decode_header(s)
    result = []
    for part, enc in parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


def extract_reply_body(msg: email.message.Message) -> str:
    """提取回复邮件的正文（去掉引用的原始邮件内容）"""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                charset = part.get_content_charset() or "utf-8"
                body = part.get_payload(decode=True).decode(charset, errors="replace")
                break
    else:
        charset = msg.get_content_charset() or "utf-8"
        body = msg.get_payload(decode=True).decode(charset, errors="replace")

    # 去掉引用部分（以 ">" 开头的行、"On ... wrote:" 之后的内容）
    lines = body.splitlines()
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(">"):
            continue
        if re.match(r"^On .+ wrote:$", stripped):
            break
        if "-----Original Message-----" in stripped:
            break
        clean_lines.append(line)

    return "\n".join(clean_lines).strip()


def check_for_reply() -> str | None:
    """
    连接 Gmail IMAP，查找对今日 [AI日报] 邮件的回复。
    返回回复正文，未找到则返回 None。
    """
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(SENDER_EMAIL, SENDER_PASSWORD)
        mail.select("INBOX")

        # IMAP SEARCH 不支持中文，改为只按日期搜索今日所有邮件，再在本地过滤主题
        today_str = datetime.now().strftime("%d-%b-%Y")
        _, data = mail.search(None, f'(SINCE "{today_str}")')

        msg_ids = data[0].split()
        if not msg_ids:
            mail.logout()
            return None

        for msg_id in reversed(msg_ids):  # 最新的优先
            _, msg_data = mail.fetch(msg_id, "(RFC822)")
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            subject = decode_str(msg.get("Subject", ""))

            # 本地过滤：是回复（Re:）且主题含 AI-Daily 或 AI日报 标记
            is_reply = subject.lower().startswith("re:")
            is_daily = "AI-Daily" in subject or "AI日报" in subject
            if is_reply and is_daily:
                body = extract_reply_body(msg)
                if body:
                    print(f"\n📨  检测到回复！")
                    print(f"    主题：{subject}")
                    print(f"    内容：{body[:200]}{'...' if len(body) > 200 else ''}")
                    mail.logout()
                    return body

        mail.logout()
        return None

    except Exception as e:
        print(f"⚠️  IMAP 检查失败：{e}")
        return None


def wait_for_reply() -> None:
    """等待到美东时间 12:00，检查一次邮件回复，触发学习计划生成"""
    now_et = datetime.now(EASTERN)
    target = now_et.replace(hour=CHECK_HOUR, minute=0, second=0, microsecond=0)

    # 如果今天 12 点已过，直接立即检查
    if now_et >= target:
        print(f"[{now_et.strftime('%H:%M ET')}] 已过 12:00，立即检查收件箱…")
    else:
        wait_secs = (target - now_et).total_seconds()
        print(f"\n⏰  等待至美东时间 12:00 检查邮件（还有 {int(wait_secs // 3600)}h {int((wait_secs % 3600) // 60)}m）")
        print("    （按 Ctrl+C 可跳过等待立即检查）")
        try:
            time.sleep(wait_secs)
        except KeyboardInterrupt:
            print("\n↩️  手动触发检查…")

    now_str = datetime.now(EASTERN).strftime("%H:%M ET")
    print(f"\n[{now_str}] 检查收件箱…", end=" ", flush=True)

    feedback = check_for_reply()

    if feedback:
        print("\n🚀  触发学习计划生成…")
        subprocess.run(
            [sys.executable, "generate_plan.py", feedback],
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        print("\n✅  完成！")
    else:
        print("未收到回复。")
        print("    如需手动生成计划，请运行：python generate_plan.py")


if __name__ == "__main__":
    wait_for_reply()
