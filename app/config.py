import os
from dotenv import load_dotenv

load_dotenv()

# Slack API credentials
SLACK_BOTS = {
    "bot1": {
        "bot_token": os.environ.get("SLACK_BOT_TOKEN_1"),
        "app_token": os.environ.get("SLACK_APP_TOKEN_1"),
    },
    "bot2": {
        "bot_token": os.environ.get("SLACK_BOT_TOKEN_2"),
        "app_token": os.environ.get("SLACK_APP_TOKEN_2"),
    },
    # Add more bots as needed
}

# ... (rest of the configuration remains the same)

# LLM API credentials
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# MySQL database connection settings
MYSQL_HOST = os.environ.get("MYSQL_HOST")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_USER = os.environ.get("MYSQL_USER")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
MYSQL_DB = os.environ.get("MYSQL_DB")

# Caching settings
CACHE_TYPE = os.environ.get("CACHE_TYPE", "simple")
CACHE_DEFAULT_TIMEOUT = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", 300))

# Logging settings
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
