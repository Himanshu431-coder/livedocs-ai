import requests
import tiktoken
import time
from app.config import get_settings
from typing import Generator


class LLMClient:
    def __init__(self):
        self.settings = get_settings()
        self._encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        return len(self._encoding.encode(text))

    def chat(self, messages: list[dict], temperature: float | None = None,
             max_tokens: int | None = None, json_mode: bool = False) -> str:
        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://livedocs-ai.app",
            "X-Title": "LiveDocs AI v2",
        }
        payload = {
            "model": self.settings.llm_model,
            "messages": messages,
            "max_tokens": max_tokens or self.settings.llm_max_tokens,
            "temperature": temperature or self.settings.llm_temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        for attempt in range(3):
            try:
                response = requests.post(
                    self.settings.llm_base_url, headers=headers,
                    json=payload, timeout=self.settings.llm_timeout,
                )
                if response.status_code == 429:
                    wait_time = 5 * (attempt + 1)
                    print(f"  Rate limited, waiting {wait_time}s... (attempt {attempt+1}/3)")
                    time.sleep(wait_time)
                    continue
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except requests.exceptions.HTTPError as e:
                if attempt < 2 and response.status_code >= 500:
                    time.sleep(3)
                    continue
                raise e
        raise Exception("Failed after 3 retries - API rate limit hit")

    def chat_stream(self, messages: list[dict], temperature: float | None = None) -> Generator[str, None, None]:
        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://livedocs-ai.app",
            "X-Title": "LiveDocs AI v2",
        }
        payload = {
            "model": self.settings.llm_model,
            "messages": messages,
            "max_tokens": self.settings.llm_max_tokens,
            "temperature": temperature or self.settings.llm_temperature,
            "stream": True,
        }
        with requests.post(self.settings.llm_base_url, headers=headers, json=payload, timeout=self.settings.llm_timeout, stream=True) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        import json
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

    def classify_complexity(self, question: str) -> str:
        keywords_complex = ["compare", "analyze", "versus", "difference", "relationship", "contrast"]
        keywords_analytical = ["evaluate", "assess", "justify", "predict", "estimate", "recommend"]
        q = question.lower()
        if any(kw in q for kw in keywords_analytical):
            return "analytical"
        if any(kw in q for kw in keywords_complex):
            return "complex"
        if len(q.split()) > 15:
            return "moderate"
        return "simple"


_llm_client: LLMClient | None = None

def get_llm() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
