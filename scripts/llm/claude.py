import os
import yaml
import anthropic

from .base import BaseLLM


def _load_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "../../config.yml")
    with open(os.path.abspath(config_path), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class ClaudeLLM(BaseLLM):
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        config = _load_config()
        self.model = config["llm"]["claude_model"]
        self.max_tokens = config["llm"]["max_tokens"]

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        messages = [{"role": "user", "content": prompt}]

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=messages,
        )

        # tool_use 블록과 text 블록이 섞여 오므로 text 블록만 추출해서 합침
        text_parts = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)

        # web_search 결과가 포함된 경우 follow-up 메시지 처리
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "",  # 실제 검색 결과는 API가 내부 처리
                    })

            # 검색 결과를 포함한 후속 응답 요청
            followup_messages = messages + [
                {"role": "assistant", "content": response.content},
                {"role": "user", "content": tool_results},
            ]
            followup = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=followup_messages,
            )
            for block in followup.content:
                if block.type == "text":
                    text_parts.append(block.text)

        return "\n".join(text_parts)
