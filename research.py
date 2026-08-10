#!/usr/bin/env python3
"""
Step 1 - 研究收集
使用 Anthropic SDK + web_search 工具搜索：
- arxiv 最新 AI 论文
- 大厂 AI 动态
- SAP AI 最新研究和产品
保存为 research.json 并发摘要邮件
"""

import json
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from tavily import TavilyClient
from send_email import send_html_email
from sap_client import get_client

load_dotenv()

RESEARCH_FILE = Path("research.json")
client = get_client()
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def search(query: str) -> str:
    """用 Tavily 执行搜索，返回结果文本"""
    result = tavily.search(query=query, search_depth="advanced", max_results=5)
    texts = []
    for r in result.get("results", []):
        texts.append(f"**{r.get('title', '')}** ({r.get('url', '')})\n{r.get('content', '')}")
    return "\n\n".join(texts)


def collect_research(today: str) -> dict:
    """分别搜索三个方向，整合为 research dict"""
    print("📄  搜索 arxiv 最新 AI 论文…")
    arxiv_raw = search(
        f"Search arxiv.org for the most important AI papers published this week in 2025. "
        f"Focus on LLM, Agent, RAG, multimodal, diffusion models. "
        f"For each paper give: title, authors, arxiv URL, one-sentence contribution, category."
    )

    print("🏢  搜索大厂 AI 动态…")
    bigtech_raw = search(
        f"Search for the latest AI announcements from OpenAI, Google DeepMind, Meta AI, "
        f"Microsoft AI, and Anthropic in the past 7 days (around {today}). "
        f"For each company give: company name, announcement title, summary, source URL."
    )

    print("🔷  搜索 SAP AI 最新动态…")
    sap_raw = search(
        f"Search for the latest SAP AI news in 2025: SAP Joule new features, SAP Business AI, "
        f"SAP AI research papers, SAP AI partnerships. "
        f"Visit news.sap.com if possible. "
        f"For each item give: title, type (product/research/partnership), detailed summary, URL, impact on SAP users."
    )

    print("🧠  整合研究结果…")
    # 让模型把三段原始文本整合成结构化 JSON
    synthesis = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": f"""Based on the following research results, create a structured JSON object.

=== arxiv papers ===
{arxiv_raw}

=== Big Tech AI news ===
{bigtech_raw}

=== SAP AI news ===
{sap_raw}

Return ONLY valid JSON in this exact format (no markdown, no explanation):
{{
  "date": "{today}",
  "arxiv_papers": [
    {{
      "title": "paper title",
      "authors": "author names",
      "url": "https://arxiv.org/abs/...",
      "contribution": "one sentence core contribution",
      "category": "LLM/RAG/Agent/Diffusion/Multimodal"
    }}
  ],
  "big_tech": [
    {{
      "company": "company name",
      "title": "news title",
      "summary": "brief summary",
      "url": "source URL"
    }}
  ],
  "sap_focus": [
    {{
      "title": "title",
      "type": "research/product/partnership",
      "summary": "detailed 3-5 sentence summary",
      "url": "source URL",
      "impact": "impact on SAP users/developers"
    }}
  ]
}}"""
        }],
    )

    text = next(b.text for b in synthesis.content if hasattr(b, "text"))
    # 清理可能的 markdown 代码块
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


def build_summary_email(data: dict, today: str) -> str:
    lines = [
        f"# 📬 AI 研究日报 —— {today}\n\n",
        "> **请直接回复此邮件**，告诉我你想深入了解哪部分，系统将自动生成完整学习计划。\n\n---\n\n",
        "## 📄 arxiv 最新论文\n\n",
    ]
    for i, p in enumerate(data.get("arxiv_papers", []), 1):
        lines.append(f"**{i}. [{p['title']}]({p['url']})**  \n")
        lines.append(f"*{p.get('authors', '')}* | {p.get('category', '')}  \n")
        lines.append(f"{p['contribution']}\n\n")

    lines.append("---\n\n## 🏢 大厂 AI 动态\n\n")
    for t in data.get("big_tech", []):
        lines.append(f"**{t['company']}**：[{t['title']}]({t['url']})  \n{t['summary']}\n\n")

    lines.append("---\n\n## 🔷 SAP AI 专项\n\n")
    for s in data.get("sap_focus", []):
        lines.append(f"**[{s['title']}]({s['url']})**（{s['type']}）  \n")
        lines.append(f"{s['summary']}  \n")
        if s.get("impact"):
            lines.append(f"*影响：{s['impact']}*\n\n")

    lines.append("\n---\n\n*直接回复此邮件填写反馈，系统将自动生成个性化学习计划。*\n")
    return "".join(lines)


def main() -> None:
    today = date.today().strftime("%Y年%m月%d日")
    print(f"\n🔬  研究收集启动  [{today}]")
    print("=" * 60)

    data = collect_research(today)

    RESEARCH_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n✅  research.json 已保存")

    body = build_summary_email(data, today)
    send_html_email(
        subject=f"[AI-Daily] {today} Research Summary - Please Reply with Feedback",
        markdown_content=body,
        today=today,
    )
    print("⏳  等待你的邮件回复，运行 python wait_reply.py 开始监听…")


if __name__ == "__main__":
    main()
