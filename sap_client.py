#!/usr/bin/env python3
"""
SAP AI Core client — wraps direct HTTP calls to SAP GenAI Hub foundation-models.
Provides a drop-in interface matching the parts of anthropic.Anthropic() used in this project.
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

_token_cache: dict = {}


def get_token() -> str:
    now = time.time()
    if _token_cache.get("token") and now < _token_cache.get("expires_at", 0) - 60:
        return _token_cache["token"]

    resp = requests.post(
        os.getenv("SAP_AUTH_URL", "").rstrip("/") + "/oauth/token",
        data={"grant_type": "client_credentials"},
        auth=(os.getenv("SAP_CLIENT_ID", ""), os.getenv("SAP_CLIENT_SECRET", "")),
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 3600)
    return _token_cache["token"]


def _invoke_url() -> str:
    ai_api_url = os.getenv("SAP_AI_API_URL", "").rstrip("/")
    deployment_id = os.getenv("SAP_DEPLOYMENT_ID", "")
    return f"{ai_api_url}/v2/inference/deployments/{deployment_id}/invoke"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {get_token()}",
        "AI-Resource-Group": os.getenv("SAP_RESOURCE_GROUP", "default"),
        "Content-Type": "application/json",
    }


class _MessagesResponse:
    def __init__(self, data: dict):
        self._data = data
        self.content = [_TextBlock(b) for b in data.get("content", [])]
        self.stop_reason = data.get("stop_reason")

    def __iter__(self):
        return iter(self.content)


class _TextBlock:
    def __init__(self, block: dict):
        self.type = block.get("type")
        self.text = block.get("text", "") if block.get("type") == "text" else ""


class _StreamContextManager:
    def __init__(self, payload: dict):
        self._payload = payload
        self.text_stream = None
        self._full_text = ""

    def __enter__(self):
        url = _invoke_url().replace("/invoke", "/invoke-with-response-stream")
        resp = requests.post(url, json=self._payload, headers=_headers(), stream=True, timeout=120)
        resp.raise_for_status()

        def _stream():
            import json
            for line in resp.iter_lines():
                if not line:
                    continue
                decoded = line.decode("utf-8") if isinstance(line, bytes) else line
                if decoded.startswith("data:"):
                    chunk = decoded[5:].strip()
                    if chunk == "[DONE]":
                        break
                    try:
                        obj = json.loads(chunk)
                        delta = obj.get("delta", {})
                        if delta.get("type") == "text_delta":
                            text = delta.get("text", "")
                            self._full_text += text
                            yield text
                    except Exception:
                        continue

        self.text_stream = _stream()
        return self

    def __exit__(self, *args):
        pass


class _Messages:
    def create(self, *, model: str, max_tokens: int, messages: list, tools: list = None, **kwargs):
        payload = {"anthropic_version": "bedrock-2023-05-31", "max_tokens": max_tokens, "messages": messages}
        if tools:
            payload["tools"] = tools
        resp = requests.post(_invoke_url(), json=payload, headers=_headers(), timeout=120)
        resp.raise_for_status()
        return _MessagesResponse(resp.json())

    def stream(self, *, model: str, max_tokens: int, messages: list, **kwargs):
        payload = {"anthropic_version": "bedrock-2023-05-31", "max_tokens": max_tokens, "messages": messages}
        return _StreamContextManager(payload)


class SAPAnthropicClient:
    def __init__(self):
        self.messages = _Messages()


def get_client() -> SAPAnthropicClient:
    return SAPAnthropicClient()
