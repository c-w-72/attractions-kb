"""
LLM 接口封装 — 支持 Claude / OpenAI
用法: 设置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY 环境变量
"""

import json
import logging
import os
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


def get_llm() -> "LLMClient | None":
    """根据环境变量创建 LLM 客户端 (None = 不可用)"""
    key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key:
        return None

    if os.environ.get("ANTHROPIC_API_KEY"):
        return ClaudeClient()
    return OpenAIClient()


class LLMClient:
    """LLM 客户端基类"""

    def chat(self, messages: list, max_tokens: int = 1024) -> str | None:
        raise NotImplementedError

    def chat_stream(self, messages: list, max_tokens: int = 1024):
        """流式生成，逐段 yield 文本 (默认回退为非流式)"""
        result = self.chat(messages, max_tokens)
        if result:
            yield result


class ClaudeClient(LLMClient):
    """Anthropic Claude API"""

    MODEL = "claude-sonnet-4-6"  # 使用最新稳定版
    API_URL = "https://api.anthropic.com/v1/messages"

    def chat(self, messages: list, max_tokens: int = 1024) -> str | None:
        key = os.environ["ANTHROPIC_API_KEY"]
        system = [m["content"] for m in messages if m["role"] == "system"]
        body = {
            "model": self.MODEL,
            "max_tokens": max_tokens,
            "messages": [m for m in messages if m["role"] != "system"],
        }
        if system:
            body["system"] = system[0]

        req = urllib.request.Request(
            self.API_URL,
            data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
            return data.get("content", [{}])[0].get("text", "")
        except urllib.error.HTTPError as e:
            logger.error(f"Claude API error: {e.code} {e.read().decode()[:200]}")
            return None
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return None

    def chat_stream(self, messages: list, max_tokens: int = 1024):
        key = os.environ["ANTHROPIC_API_KEY"]
        system = [m["content"] for m in messages if m["role"] == "system"]
        body = {
            "model": self.MODEL,
            "max_tokens": max_tokens,
            "stream": True,
            "messages": [m for m in messages if m["role"] != "system"],
        }
        if system:
            body["system"] = system[0]

        req = urllib.request.Request(
            self.API_URL,
            data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                for raw_line in resp:
                    line = raw_line.decode().strip()
                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            data = json.loads(data_str)
                            if data.get("type") == "content_block_delta":
                                delta = data.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    text = delta.get("text", "")
                                    if text:
                                        yield text
                        except json.JSONDecodeError:
                            pass
        except urllib.error.HTTPError as e:
            logger.error(f"Claude stream error: {e.code} {e.read().decode()[:200]}")
        except Exception as e:
            logger.error(f"Claude stream error: {e}")


class OpenAIClient(LLMClient):
    """OpenAI API"""

    MODEL = "gpt-4o-mini"
    API_URL = "https://api.openai.com/v1/chat/completions"

    def chat(self, messages: list, max_tokens: int = 1024) -> str | None:
        key = os.environ["OPENAI_API_KEY"]
        body = {
            "model": self.MODEL,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        req = urllib.request.Request(
            self.API_URL,
            data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except urllib.error.HTTPError as e:
            logger.error(f"OpenAI API error: {e.code} {e.read().decode()[:200]}")
            return None
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None

    def chat_stream(self, messages: list, max_tokens: int = 1024):
        key = os.environ["OPENAI_API_KEY"]
        body = {
            "model": self.MODEL,
            "max_tokens": max_tokens,
            "stream": True,
            "messages": messages,
        }
        req = urllib.request.Request(
            self.API_URL,
            data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                for raw_line in resp:
                    line = raw_line.decode().strip()
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                text = delta.get("content", "")
                                if text:
                                    yield text
                        except json.JSONDecodeError:
                            pass
        except urllib.error.HTTPError as e:
            logger.error(f"OpenAI stream error: {e.code} {e.read().decode()[:200]}")
        except Exception as e:
            logger.error(f"OpenAI stream error: {e}")


def make_prompt(query: str, entities: dict, attractions: list) -> list:
    """构建 LLM 对话消息"""
    context_parts = [f"当前问题: {query}"]

    if entities.get("attraction_name"):
        context_parts.append(f"景点: {entities['attraction_name']}")
    if entities.get("province"):
        context_parts.append(f"省份: {entities['province']}")
    if entities.get("city"):
        context_parts.append(f"城市: {entities['city']}")
    if entities.get("category"):
        context_parts.append(f"分类: {entities['category']}")
    if entities.get("scenario"):
        context_parts.append(f"咨询场景: {entities['scenario']}")

    if attractions:
        ctx = "\n".join(
            f"- {a['name']}({a['province']}, {a['category']}, 评分{a.get('rating','')})"
            for a in attractions[:8]
        )
        context_parts.append(f"\n相关景点数据:\n{ctx}")

    return [
        {
            "role": "system",
            "content": (
                "你是一个专业的中国旅游景点助手。请基于提供的景点数据，"
                "用中文回答用户关于旅游景点的咨询。回答要简明实用，"
                "包括具体建议（门票、开放时间、游玩时长、交通等信息）。"
                "如果用户问行程规划，给出每日详细安排。"
                "如果不知道确切信息，如实告知不要编造。"
            ),
        },
        {"role": "user", "content": "\n".join(context_parts)},
    ]
