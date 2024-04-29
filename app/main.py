import sys
import os
import asyncio

sys.path.insert(0, "/Users/divyanshgolyan/Documents/GitHub/interaced-slackbots")

from app import create_app


async def main():
    flask_app, _ = await create_app()

    # Run the Flask application
    flask_app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    asyncio.run(main())
