import os
import yaml
from openai import OpenAI

from .base import BaseLLM


def _load_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "../../config.yml")
    with open(os.path.abspath(config_path), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class OpenAILLM(BaseLLM):
    def __init__(self):
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        config = _load_config()
        self.model = config["llm"]["openai_model"]
        self.max_tokens = config["llm"]["max_tokens"]

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            tools=[{"type": "function", "function": {
                "name": "search_web",
                "description": "Search the web for current information",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            }}],
        )

        return response.choices[0].message.content or ""
