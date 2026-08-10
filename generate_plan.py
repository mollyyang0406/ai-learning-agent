#!/usr/bin/env python3
"""
Step 2 - 学习计划生成
根据 research.json + 用户反馈，生成个性化 Markdown 学习计划并发邮件
"""

import json
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from send_email import send_html_email
from sap_client import get_client

load_dotenv()

RESEARCH_FILE = Path("research.json")
PLAN_FILE     = Path("daily_plan.md")
client        = get_client()


def generate_plan(feedback: str) -> None:
    today = date.today().strftime("%Y年%m月%d日")

    if not RESEARCH_FILE.exists():
        print("❌  research.json 不存在，请先运行 python research.py")
        return

    research = json.loads(RESEARCH_FILE.read_text(encoding="utf-8"))
    research_str = json.dumps(research, ensure_ascii=False, indent=2)

    print(f"\n📝  学习计划生成  [{today}]")
    print(f"💬  用户反馈：{feedback or '（无，全面覆盖）'}")
    print("=" * 60)

    prompt = f"""今天是 {today}。

以下是今日 AI 研究资料：
```json
{research_str}
```

用户反馈和重点关注：
> {feedback if feedback.strip() else "无特别指定，请全面覆盖所有内容"}

请生成一份完整的个性化 Markdown 学习计划，包含：

# AI 每日学习计划 —— {today}

## 📰 今日资讯摘要
（表格：标题、来源、核心价值）

## 🔷 SAP AI 专项分析
（重点展开 SAP 部分：技术细节、产品影响、对 SAP 工程师/顾问的学习建议）

## 🔬 技术原理深解
（根据用户反馈重点深入，含算法原理、架构思路、关键直觉）

## 🗺️ 学习路线
（入门 0-1周 / 进阶 1-4周 / 参考资料链接）

## 🛠️ 实操建议
（3 个具体可执行项目，含技术栈和关键代码片段）

请直接输出 Markdown，不要加额外说明。"""

    plan_text = ""
    with client.messages.stream(
        model="claude-sonnet-4-5",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            plan_text += text

    print("\n" + "=" * 60)

    PLAN_FILE.write_text(plan_text, encoding="utf-8")
    print("✅  daily_plan.md 已保存")

    send_html_email(
        subject=f"🎓 AI 每日学习计划 —— {today}",
        markdown_content=plan_text,
        today=today,
    )


def main() -> None:
    feedback = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    generate_plan(feedback)


if __name__ == "__main__":
    main()
