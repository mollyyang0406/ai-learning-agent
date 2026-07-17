#!/usr/bin/env python3
"""
Step 2 - 学习计划生成 Agent
根据 research.json + 用户反馈，生成个性化 Markdown 学习计划并发送邮件
"""

import asyncio
import json
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from claude_agent_sdk import ClaudeAgentOptions, query
from claude_agent_sdk.types import AssistantMessage, TextBlock
from send_email import send_html_email

load_dotenv()

RESEARCH_FILE = Path("research.json")
PLAN_FILE     = Path("daily_plan.md")
AGENT_OPTIONS = ClaudeAgentOptions(
    max_turns=20,
    allowed_tools=["WebSearch", "WebFetch", "Write"],
)


def build_plan_prompt(research: dict, feedback: str, today: str) -> str:
    research_str = json.dumps(research, ensure_ascii=False, indent=2)
    return f"""
今天是 {today}。

以下是今日收集的 AI 研究资料（JSON 格式）：

```json
{research_str}
```

用户的反馈和重点关注：
> {feedback if feedback.strip() else "无特别指定，请全面覆盖所有内容"}

---

请根据以上内容生成一份完整的个性化学习计划，Markdown 格式，包含以下板块：

# AI 每日学习计划 —— {today}

## 📰 今日资讯摘要
（表格形式，含论文/动态标题、来源、核心价值）

## 🔷 SAP AI 专项分析
（重点展开 SAP 部分，包括技术细节、产品影响、SAP 工程师/顾问的学习建议）

## 🔬 技术原理深解
（根据用户反馈重点深入解释，含算法原理、架构图思路、关键公式直觉）

## 🗺️ 学习路线
（入门 0-1周 / 进阶 1-4周 / 参考资料）

## 🛠️ 实操建议
（3 个具体可执行的动手项目，含技术栈和关键代码片段）

---

用 Write 工具将计划写入 daily_plan.md，然后输出完整内容。
"""


async def generate_plan(feedback: str) -> None:
    today = date.today().strftime("%Y年%m月%d日")

    if not RESEARCH_FILE.exists():
        print("❌  research.json 不存在，请先运行 python research.py")
        return

    research = json.loads(RESEARCH_FILE.read_text(encoding="utf-8"))

    print(f"\n📝  学习计划生成 Agent 启动  [{today}]")
    print(f"💬  用户反馈：{feedback or '（无）'}")
    print("=" * 60)

    async for message in query(
        prompt=build_plan_prompt(research, feedback, today),
        options=AGENT_OPTIONS,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock) and block.text:
                    print(block.text, end="", flush=True)

    print("\n" + "=" * 60)
    print("✅  学习计划已生成！")

    if PLAN_FILE.exists():
        plan_md = PLAN_FILE.read_text(encoding="utf-8")
        send_html_email(
            subject=f"🎓 AI 每日学习计划 —— {today}",
            markdown_content=plan_md,
            today=today,
        )


def main() -> None:
    import sys
    feedback = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    asyncio.run(generate_plan(feedback))


if __name__ == "__main__":
    main()
