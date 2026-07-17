#!/usr/bin/env python3
"""
AI 每日学习方案 Agent
- 搜索当天最新 AI 技术资讯（WebSearch）
- 读取文章详情（WebFetch）
- 生成包含"技术原理/学习路线/实操建议"的 Markdown 学习计划（Write）
- 将计划以 HTML 邮件形式发送到指定邮箱
"""

import asyncio
import os
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import markdown
from dotenv import load_dotenv

from claude_agent_sdk import ClaudeAgentOptions, query
from claude_agent_sdk.types import AssistantMessage, TextBlock

load_dotenv()

# ── 邮件配置（从 .env 读取，不要硬编码密码）─────────────────────
RECIPIENT_EMAIL = "mollyyang0406@gmail.com"
SMTP_HOST       = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT       = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL    = os.getenv("SENDER_EMAIL", "")        # 你的 Gmail 地址
SENDER_PASSWORD = os.getenv("SENDER_APP_PASSWORD", "") # Gmail App 密码


# ── 工具配置 ──────────────────────────────────────────────────
AGENT_OPTIONS = ClaudeAgentOptions(
    max_turns=15,
    allowed_tools=["WebSearch", "WebFetch", "Write"],
)

PLAN_FILE = Path("daily_plan.md")


# ── 提示词构建 ─────────────────────────────────────────────────
def build_prompt(today: str) -> str:
    """根据当天日期构造 Agent 任务提示词"""
    return f"""
今天是 {today}。请按以下步骤完成 AI 每日学习计划的生成：

---

## 步骤 1：搜索今日 AI 技术资讯

使用 WebSearch 搜索今天（{today}）最重要的 3 条 AI 技术新闻。
搜索关键词建议：
- "AI news {today}"
- "artificial intelligence breakthrough {today}"
- "large language model {today}"

---

## 步骤 2：阅读文章详情

对搜索到的每篇文章，使用 WebFetch 读取完整内容，重点关注：
- 核心技术突破或创新点
- 涉及的模型、算法或框架
- 实际应用场景

---

## 步骤 3：生成每日学习计划

将内容整理为以下 Markdown 格式的学习计划：

```
# AI 每日学习计划 —— {today}

## 📰 今日资讯摘要

| # | 标题 | 来源 | 核心价值 |
|---|------|------|----------|
| 1 | ... | ... | ... |
| 2 | ... | ... | ... |
| 3 | ... | ... | ... |

---

## 🔬 技术原理

[深入解释今日新闻涉及的核心技术概念，包括算法原理、模型架构、关键创新等]

---

## 🗺️ 学习路线

[根据今日内容推荐的学习路径]

### 入门（0–1 周）
- ...

### 进阶（1–4 周）
- ...

### 参考资料
- 论文 / 博客 / 视频链接

---

## 🛠️ 实操建议

[具体可执行的动手练习项目]

### 项目 1：...
- 目标：...
- 技术栈：...
- 步骤：...

### 项目 2：...
...

---

*生成时间：{today} | 工具：Claude Agent SDK*
```

---

## 步骤 4：保存文件

使用 Write 工具将完整的学习计划写入 `daily_plan.md`。

请现在开始执行以上步骤。
"""


# ── Agent 执行逻辑 ──────────────────────────────────────────────
async def run_agent() -> None:
    """异步启动 Agent，流式输出执行过程"""
    today = date.today().strftime("%Y年%m月%d日")
    prompt = build_prompt(today)

    print(f"\n🚀  AI 每日学习方案 Agent 启动  [{today}]")
    print("=" * 60)

    # 逐条处理 Agent 返回的消息流
    async for message in query(prompt=prompt, options=AGENT_OPTIONS):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock) and block.text:
                    print(block.text, end="", flush=True)

    print("\n" + "=" * 60)
    print("✅  完成！学习计划已保存至 daily_plan.md")


# ── 邮件发送 ────────────────────────────────────────────────────
def send_email(today: str) -> None:
    """读取 daily_plan.md，转为 HTML 邮件后发送"""
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("⚠️  未配置 SENDER_EMAIL / SENDER_APP_PASSWORD，跳过邮件发送。")
        print("   请在 .env 文件中填写发件人信息后重试。")
        return

    plan_md = PLAN_FILE.read_text(encoding="utf-8")

    # Markdown → HTML（带基础样式）
    body_html = markdown.markdown(plan_md, extensions=["tables", "fenced_code"])
    html = f"""
    <html><head><meta charset="utf-8">
    <style>
      body  {{ font-family: -apple-system, Helvetica, Arial, sans-serif;
               max-width: 800px; margin: 40px auto; color: #333; line-height: 1.7; }}
      h1    {{ color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 8px; }}
      h2    {{ color: #0d47a1; margin-top: 32px; }}
      h3    {{ color: #1565c0; }}
      table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
      th,td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
      th    {{ background: #e8f0fe; }}
      code  {{ background: #f5f5f5; padding: 2px 6px; border-radius: 4px;
               font-family: 'Courier New', monospace; }}
      pre   {{ background: #f5f5f5; padding: 16px; border-radius: 8px;
               overflow-x: auto; }}
    </style></head>
    <body>{body_html}</body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🤖 AI 每日学习计划 —— {today}"
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = RECIPIENT_EMAIL
    msg.attach(MIMEText(plan_md, "plain", "utf-8"))   # 纯文本备用
    msg.attach(MIMEText(html,    "html",  "utf-8"))   # 优先展示 HTML

    print(f"\n📧  正在发送邮件至 {RECIPIENT_EMAIL} …")
    port = int(os.getenv("SMTP_PORT", "465"))
    if port == 465:
        # SSL 直连（不需要 STARTTLS）
        with smtplib.SMTP_SSL(SMTP_HOST, port, timeout=15) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
    else:
        # STARTTLS（587）
        with smtplib.SMTP(SMTP_HOST, port, timeout=15) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
    print("✉️   邮件发送成功！")


# ── 程序入口 ────────────────────────────────────────────────────
def main() -> None:
    today = date.today().strftime("%Y年%m月%d日")
    asyncio.run(run_agent())
    send_email(today)


if __name__ == "__main__":
    main()
