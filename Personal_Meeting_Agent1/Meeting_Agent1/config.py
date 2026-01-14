"""Config settings for the meeting agent"""
import os
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

# load env vars from .env file
load_dotenv()

# OpenRouter API config
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "openai/gpt-4o-mini"  # using openrouter for access

# reference date for deadline resolution
ref_date_str = os.getenv("REFERENCE_DATE", "2026-01-10")
REFERENCE_DATE = datetime.strptime(ref_date_str, "%Y-%m-%d").date()

# file paths
PEOPLE_DIRECTORY_PATH = "data/people.json"
OUTPUT_DIRECTORY = "outputs"

# LLM settings
LLM_TEMPERATURE = 0.1  # low temp = more deterministic
LLM_MAX_TOKENS = 4000  # TODO: might need to increase this for longer meetings

# quality control thresholds
CONFIDENCE_THRESHOLD = 0.7  # flag anything below 70%
MAX_RETRIES = 3

def validate_config():
    # check if api key is set
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "your_openrouter_api_key_here":
        logger.error("OpenRouter API key not configured!")
        raise ValueError(
            "OPENROUTER_API_KEY not set.\n"
            "Please edit the .env file and add your API key.\n"
            "Get one from: https://openrouter.ai/"
        )
    
    logger.success("✅ Configuration looks good!")
    return True
