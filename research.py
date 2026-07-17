#!/usr/bin/env python3
"""
Step 1 - 研究收集 Agent
- arxiv.org 最新 AI 论文
- 各大厂 AI 创新动态
- SAP 最新 AI 研究和产品专项分析
- 保存 research.json + 发摘要邮件（邮件主题含特定标记供回复检测）
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
AGENT_OPTIONS = ClaudeAgentOptions(
    max_turns=30,
    allowed_tools=["WebSearch", "WebFetch", "Write"],
)


def build_research_prompt(today: str) -> str:
    return f"""
今天是 {today}。你是一位 AI 研究分析师，请完成以下任务：

---

## 任务 1：arxiv.org 最新 AI 论文

访问以下页面获取最新论文列表：
- https://arxiv.org/list/cs.AI/recent
- https://arxiv.org/list/cs.LG/recent
- https://arxiv.org/list/cs.CL/recent

优先选择涉及 LLM、Agent、RAG、多模态、扩散模型的论文，每个方向各选 2 篇最重要的，记录：
标题、作者、arxiv 链接、核心贡献（一句话）。

---

## 任务 2：大厂 AI 创新动态（最近 7 天）

搜索以下关键词：
- "OpenAI new research OR model 2025"
- "Google DeepMind AI 2025"
- "Meta AI research 2025"
- "Microsoft AI research 2025"
- "Anthropic research 2025"

每家公司选 1 条最重要动态。

---

## 任务 3：SAP AI 专项分析

搜索并访问：
- https://news.sap.com/tags/artificial-intelligence/
- "SAP Joule agent 2025"
- "SAP Business AI new features 2025"
- "SAP AI research paper 2025"

重点关注：SAP Joule 最新能力、Business AI 新产品、SAP 发表的论文、与 AI 公司的合作。

---

## 任务 4：保存 research.json

用 Write 工具将以下 JSON 格式写入 research.json：

{{
  "date": "{today}",
  "arxiv_papers": [
    {{
      "title": "论文标题",
      "authors": "作者",
      "url": "https://arxiv.org/abs/xxxx.xxxxx",
      "contribution": "核心贡献",
      "category": "LLM/RAG/Agent/Diffusion/Multimodal"
    }}
  ],
  "big_tech": [
    {{
      "company": "公司名",
      "title": "动态标题",
      "summary": "简介",
      "url": "来源链接"
    }}
  ],
  "sap_focus": [
    {{
      "title": "标题",
      "type": "research/product/partnership",
      "summary": "详细介绍（3-5句话）",
      "url": "来源链接",
      "impact": "对 SAP 用户/开发者的影响"
    }}
  ]
}}

请现在开始执行。
"""


def build_summary_email(data: dict, today: str) -> str:
    """将 research.json 转为邮件正文 Markdown"""
    lines = [
        f"# 📬 AI 研究日报 —— {today}\n\n",
        "> **请直接回复此邮件**，告诉我你想深入了解哪部分，我将根据你的反馈生成完整学习计划。\n\n---\n\n",

        "## 📄 arxiv 最新论文\n\n",
    ]
    for i, p in enumerate(data.get("arxiv_papers", []), 1):
        lines.append(f"**{i}. [{p['title']}]({p['url']})**  \n")
        lines.append(f"*{p.get('authors', '')}* | 类别：{p.get('category', '')}  \n")
        lines.append(f"{p['contribution']}\n\n")

    lines.append("---\n\n## 🏢 大厂 AI 动态\n\n")
    for t in data.get("big_tech", []):
        lines.append(f"**{t['company']}**：[{t['title']}]({t['url']})  \n")
        lines.append(f"{t['summary']}\n\n")

    lines.append("---\n\n## 🔷 SAP AI 专项\n\n")
    for s in data.get("sap_focus", []):
        lines.append(f"**[{s['title']}]({s['url']})**（{s['type']}）  \n")
        lines.append(f"{s['summary']}  \n")
        if s.get("impact"):
            lines.append(f"*影响：{s['impact']}*\n\n")

    lines.append("\n---\n\n*直接回复此邮件填写反馈，系统将自动为你生成个性化学习计划。*\n")
    return "".join(lines)


async def run_research() -> None:
    today = date.today().strftime("%Y年%m月%d日")

    print(f"\n🔬  研究收集 Agent 启动  [{today}]")
    print("=" * 60)

    async for message in query(prompt=build_research_prompt(today), options=AGENT_OPTIONS):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock) and block.text:
                    print(block.text, end="", flush=True)

    print("\n" + "=" * 60)
    print("✅  研究收集完成！")

    if RESEARCH_FILE.exists():
        data = json.loads(RESEARCH_FILE.read_text(encoding="utf-8"))
        body = build_summary_email(data, today)
        # 邮件主题含 [AI日报] 标记，wait_reply.py 通过此标记识别原始邮件
        send_html_email(
            subject=f"[AI-Daily] {today} Research Summary - Please Reply with Feedback",
            markdown_content=body,
            today=today,
        )
        print("\n⏳  等待你的邮件回复，运行 python wait_reply.py 开始监听…")
    else:
        print("⚠️  research.json 未生成，请检查 Agent 输出。")


def main() -> None:
    asyncio.run(run_research())


if __name__ == "__main__":
    main()
