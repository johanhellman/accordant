"""General settings and API configuration."""

import os

from dotenv import load_dotenv

load_dotenv()

# API Configuration (supports OpenRouter or LiteLLM)
# We use LLM_API_KEY/URL if available, otherwise fall back to OpenRouter defaults
OPENROUTER_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENROUTER_API_KEY")

# Concurrency and Timeout Configuration
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "4"))
LLM_REQUEST_TIMEOUT = float(os.getenv("LLM_REQUEST_TIMEOUT", "180.0"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))

# OpenRouter API endpoint
OPENROUTER_API_URL = os.getenv("LLM_API_URL", "https://openrouter.ai/api/v1/chat/completions")

# Data directory for conversation storage
DATA_DIR = "data/conversations"
