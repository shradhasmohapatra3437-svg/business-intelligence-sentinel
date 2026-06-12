"""
Unified LLM wrapper — abstracts local Ollama vs. cloud Groq.
Same function signature regardless of backend.
"""

import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Track token usage across calls
_total_prompt_tokens = 0
_total_completion_tokens = 0


def generate_text(
    prompt: str,
    system_prompt: str = "",
    max_tokens: int = 2048,
    temperature: float = 0.3,
) -> str:
    """
    Generate text using either Ollama (local) or Groq (cloud).
    Returns the generated text string.
    """
    if settings.USE_LOCAL_LLM:
        return _generate_ollama(prompt, system_prompt, max_tokens, temperature)
    else:
        return _generate_groq(prompt, system_prompt, max_tokens, temperature)


def get_token_usage() -> dict:
    """Return accumulated token usage."""
    return {
        "prompt_tokens": _total_prompt_tokens,
        "completion_tokens": _total_completion_tokens,
        "total_tokens": _total_prompt_tokens + _total_completion_tokens,
    }


def reset_token_usage():
    """Reset token counters (called at start of each pipeline run)."""
    global _total_prompt_tokens, _total_completion_tokens
    _total_prompt_tokens = 0
    _total_completion_tokens = 0


def get_model_name() -> str:
    """Return the current model identifier."""
    if settings.USE_LOCAL_LLM:
        return f"ollama/{settings.OLLAMA_MODEL}"
    return f"groq/{settings.GROQ_MODEL}"


# ── Ollama (Local) ────────────────────────────────────────────────────────

def _generate_ollama(
    prompt: str,
    system_prompt: str = "",
    max_tokens: int = 2048,
    temperature: float = 0.3,
) -> str:
    """Generate text using Ollama local inference."""
    global _total_prompt_tokens, _total_completion_tokens

    try:
        import ollama

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        logger.info(f"Calling Ollama ({settings.OLLAMA_MODEL})...")
        response = ollama.chat(
            model=settings.OLLAMA_MODEL,
            messages=messages,
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        )

        content = response.get("message", {}).get("content", "")

        # Estimate token usage from character count (Ollama doesn't provide this natively)
        est_prompt_tokens = len(prompt) // 4
        est_completion_tokens = len(content) // 4
        _total_prompt_tokens += est_prompt_tokens
        _total_completion_tokens += est_completion_tokens

        logger.info(f"Ollama response: {len(content)} chars (~{est_completion_tokens} tokens)")
        return content

    except ImportError:
        logger.error("ollama package not installed. Run: pip install ollama")
        return _generate_groq_fallback(prompt, system_prompt, max_tokens, temperature)
    except Exception as e:
        logger.warning(f"Ollama failed: {e}. Falling back to Groq.")
        return _generate_groq_fallback(prompt, system_prompt, max_tokens, temperature)


# ── Groq (Cloud) ──────────────────────────────────────────────────────────

def _generate_groq(
    prompt: str,
    system_prompt: str = "",
    max_tokens: int = 2048,
    temperature: float = 0.3,
) -> str:
    """Generate text using Groq cloud inference."""
    global _total_prompt_tokens, _total_completion_tokens

    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not configured. Returning empty response.")
        return ""

    try:
        from groq import Groq

        client = Groq(api_key=settings.GROQ_API_KEY)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        logger.info(f"Calling Groq ({settings.GROQ_MODEL})...")
        completion = client.chat.completions.create(
            messages=messages,
            model=settings.GROQ_MODEL,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = completion.choices[0].message.content

        # Track actual token usage from Groq response
        usage = completion.usage
        if usage:
            _total_prompt_tokens += usage.prompt_tokens
            _total_completion_tokens += usage.completion_tokens
            logger.info(
                f"Groq response: {usage.completion_tokens} tokens "
                f"(prompt: {usage.prompt_tokens})"
            )

        return content

    except Exception as e:
        logger.error(f"Groq API call failed: {e}")
        return ""


def _generate_groq_fallback(
    prompt: str,
    system_prompt: str = "",
    max_tokens: int = 2048,
    temperature: float = 0.3,
) -> str:
    """Automatic fallback from Ollama to Groq."""
    if settings.GROQ_API_KEY:
        logger.info("Attempting Groq fallback...")
        return _generate_groq(prompt, system_prompt, max_tokens, temperature)
    logger.warning("No LLM available (Ollama failed, Groq not configured).")
    return ""
