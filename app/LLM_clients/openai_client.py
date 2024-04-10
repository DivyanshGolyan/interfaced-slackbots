from openai import AsyncOpenAI
from app.config import OPENAI_API_KEY

client = AsyncOpenAI(api_key=OPENAI_API_KEY, max_retries=4)
