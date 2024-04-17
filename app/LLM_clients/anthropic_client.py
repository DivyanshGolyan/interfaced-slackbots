from anthropic import AsyncAnthropic
from app.config import ANTHROPIC_API_KEY

client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
