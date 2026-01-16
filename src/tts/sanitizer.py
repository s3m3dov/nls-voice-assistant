import re
import logging
from src.logger import logger
from emoji import replace_emoji
from strip_markdown import strip_markdown


def sanitize_for_tts(text: str) -> str:
    """
    Clean text for TTS by removing Markdown and special characters.
    
    Args:
        text: Raw text from LLM response.
        
    Returns:
        Clean text suitable for speech synthesis.
    """
    if not text:
        return ""
    
    original_text = text
    try:
        # 1. Remove multiline code blocks before stripping markdown
        # (strip-markdown might keep the content, which we don't want to read)
        text = re.sub(r"```[\s\S]*?```", "", text)
        
        # 2. Remove Markdown formatting using strip-markdown
        text = strip_markdown(text)
        
        # 2. Remove emojis using emoji library
        text = replace_emoji(text, replace='')
        
        # 3. Expand common abbreviations
        replacements = {
            "°C": " degrees Celsius",
            "°F": " degrees Fahrenheit",
            "km/h": " kilometers per hour",
            "mph": " miles per hour",
            "%": " percent",
            "&": " and ",
            "e.g.": "for example",
            "i.e.": "that is",
            "etc.": "etcetera",
        }
        for abbr, expansion in replacements.items():
            text = text.replace(abbr, expansion)
        
        # 4. Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        
        logger.info(f"Sanitized text for TTS. Input: '{original_text[:50]}...', Output: '{text[:50]}...'")
        
    except Exception as e:
        logger.error(f"Error during text sanitization: {e}")
        # If library processing fails, return a basic cleaned version or the original
        return re.sub(r"\s+", " ", text).strip()
    
    return text
