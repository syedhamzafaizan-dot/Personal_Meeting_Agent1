"""Helper utilities - common functions used across stages"""
import json
from typing import Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
import requests
import config


# setup logger formatting
logger.remove()  # remove default
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    colorize=True,
    level="INFO"
)


def clean_json_response(text: str) -> str:
    """
    Clean up AI responses that might have markdown formatting
    
    Sometimes the AI wraps JSON in ```json ``` blocks.
    This function strips that away to get just the JSON.
    
    Args:
        text: The raw response from the AI
        
    Returns:
        Clean JSON string
    """
    text = text.strip()
    
    # remove code block markers
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    
    if text.endswith("```"):
        text = text[:-3]
    
    return text.strip()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def call_openai_with_retry(
    prompt: str,
    system_message: str = "You are a helpful assistant.",
    temperature: float = None,
    max_tokens: int = None
) -> str:
    """Call OpenRouter API with auto-retry on failure"""
    # use defaults from config if not specified
    if temperature is None:
        temperature = config.LLM_TEMPERATURE
    if max_tokens is None:
        max_tokens = config.LLM_MAX_TOKENS
    
    # print(f"DEBUG: calling {config.OPENROUTER_MODEL}")  # for debugging
    logger.debug(f"Calling {config.OPENROUTER_MODEL}...")
    
    # TODO: add request timeout?
    resp = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": config.OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
    )
    
    if resp.status_code != 200:
        err = resp.text
        logger.error(f"OpenRouter API Error: {resp.status_code} - {err}")
        raise Exception(f"OpenRouter API failed: {err}")
    
    result = resp.json()['choices'][0]['message']['content'].strip()
    logger.debug(f"Got response ({len(result)} chars)")
    
    return result


def parse_json_safely(text: str, fallback: Optional[dict] = None) -> dict:
    """
    Parse JSON with error handling
    
    Tries to parse JSON text. If it fails, returns a fallback value
    instead of crashing the whole program.
    
    """
    try:
        cleaned = clean_json_response(text)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON: {str(e)}")
        if fallback is not None:
            return fallback
        raise


def format_list_nicely(items: list, prefix: str = "  • ") -> str:
    # format list with bullets
    if not items:
        return "(none)"
    return "\n".join(f"{prefix}{item}" for item in items)


def count_words(text: str) -> int:
    # rough word count
    return len(text.split())


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    # shorten text if too long
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

