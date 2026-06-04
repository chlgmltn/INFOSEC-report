def get_llm(provider: str):
    if provider == "claude":
        from .claude import ClaudeLLM
        return ClaudeLLM()
    elif provider == "openai":
        from .openai import OpenAILLM
        return OpenAILLM()
    else:
        raise ValueError(f"지원하지 않는 provider: {provider}")
