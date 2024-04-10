import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import pytz

load_dotenv()

# Slack API credentials
SLACK_BOTS = {
    "bot1": {
        "bot_token": os.environ.get("SLACK_BOT_TOKEN_1"),
        "app_token": os.environ.get("SLACK_APP_TOKEN_1"),
        "agent": "agent1",
    },
    "bot2": {
        "bot_token": os.environ.get("SLACK_BOT_TOKEN_2"),
        "app_token": os.environ.get("SLACK_APP_TOKEN_2"),
        "agent": "agent2",
    },
    # ...
}

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


def custom_time(*args):
    utc_dt = pytz.utc.localize(datetime.utcnow())
    converted = utc_dt.astimezone(pytz.timezone("Asia/Kolkata"))
    return converted.timetuple()


logging.Formatter.converter = custom_time

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

MAX_SLACK_FILE_SIZE = os.environ.get("MAX_SLACK_FILE_SIZE")
GPT_MODEL = os.environ.get("GPT_MODEL")
DALLE_MODEL = os.environ.get("DALLE_MODEL")
WHISPER_MODEL = os.environ.get("WHISPER_MODEL")
