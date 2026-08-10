# AI 每日学习方案 Agent

- 这是一个基于 Python 和 `claude_agent_sdk` 的项目。
- 目标：搜索当天最新的 AI 技术资讯，并生成一份 Markdown 格式的学习计划。
- 必须使用的工具（Tools）：`WebSearch`（搜索全网资讯）、`WebFetch`（读取网页详细内容）、`Write`（将生成的方案保存到本地文件）。
- 偏好：代码模块化，添加清晰的中文注释，并使用 `asyncio` 异步执行。
