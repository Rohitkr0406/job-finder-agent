import os
import re
import asyncio
import litellm

litellm.suppress_debug_info = True

def _normalize_provider(provider: str) -> str:
    provider_name = (provider or "groq").strip().lower().replace("-", "_")
    aliases = {
        "build.nvidia.com": "nvidia_nim",
        "nvidia": "nvidia_nim",
        "nvidia_nim": "nvidia_nim",
    }
    return aliases.get(provider_name, provider_name)

def _is_rate_limit_error(exc: BaseException) -> bool:
    if exc.__class__.__name__ == "RateLimitError":
        return True

    for module_name in ("errors", "exceptions"):
        module = getattr(litellm, module_name, None)
        if module is not None:
            rate_limit_class = getattr(module, "RateLimitError", None)
            if rate_limit_class is not None and isinstance(exc, rate_limit_class):
                return True

    return False

async def acompletion_with_retry(
    model: str,
    messages: list,
    max_tokens: int | None = None,
    temperature: float | None = None,
    max_retries: int = 3,
    initial_delay: float = 5.0
):
    for attempt in range(max_retries + 1):
        try:
            return await litellm.acompletion(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
        except Exception as e:
            if not _is_rate_limit_error(e):
                raise
            if attempt == max_retries:
                raise
            err_msg = str(e)
            match = re.search(r"Please try again in ([\d\.]+)s", err_msg)
            wait_time = float(match.group(1)) + 1.0 if match else initial_delay * (2 ** attempt)
            print(f"  [LLM] Rate limit hit. Retrying (attempt {attempt + 1}/{max_retries}) in {wait_time:.2f}s...")
            await asyncio.sleep(wait_time)

def get_model_string() -> str:
    provider = _normalize_provider(os.getenv("LLM_PROVIDER", "groq"))
    model = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
    if provider in {"openai", "anthropic"}:
        return model
    return f"{provider}/{model}"

def configure_llm():
    provider = _normalize_provider(os.getenv("LLM_PROVIDER", "groq"))
    key = os.getenv("LLM_API_KEY", "")
    mapping = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "groq": "GROQ_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "cohere": "COHERE_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "together": "TOGETHERAI_API_KEY",
        "nvidia_nim": "NVIDIA_NIM_API_KEY",
    }
    env_var = mapping.get(provider)
    if env_var:
        os.environ[env_var] = key
    else:
        os.environ["OPENAI_API_KEY"] = key

    if provider == "nvidia_nim":
        os.environ["NVIDIA_API_KEY"] = key
