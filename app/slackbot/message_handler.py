from app.llm_integration.openai_client import generate_text, generate_image, speech_to_text, text_to_speech
from slack_sdk import WebClient
import os
from app.database.dao import create_conversation, get_conversation, create_message


def process_message(event, say):
    # Extract relevant information from the event
    text = event.get("text")
    user_id = event.get("user")
    channel_id = event.get("channel") or event.get("channel_id")

    # Ensure that the response is always in a thread
    # If the event has a thread timestamp, use that; otherwise, use the event's timestamp
    thread_ts = event.get("thread_ts") or event.get("ts")

    # Handle different event types
    event_type = event.get("type")
    if event_type == "app_mention":
        # In case of app_mention, we need to ensure we're responding in thread if it's a threaded message
        thread_ts = thread_ts or event.get("item", {}).get("ts")

    # Check if the message contains audio data
    if event.get("subtype") == "file_share" and event.get("file", {}).get("mimetype", "").startswith("audio/"):
        audio_url = event["file"]["url_private"]
        # Download the audio data from the URL
        audio_data = download_audio_data(audio_url)
        # Use OpenAI's Whisper to transcribe the audio
        text = speech_to_text(audio_data)

    # Generate a response using OpenAI's GPT-4
    response_text = generate_text(text)

    # Get or create the conversation
    conversation = get_conversation(channel_id, thread_ts)
    if not conversation:
        conversation = create_conversation(user_id, channel_id, thread_ts)

    # Save the user's message to the database
    create_message(conversation.id, user_id, text)

    # Generate a response using OpenAI's GPT-4
    response_text = generate_text(text)

    # Save the bot's response to the database
    create_message(conversation.id, "bot", response_text)

    # Check if the user requested an image
    if "image" in text.lower():
        # Generate an image using OpenAI's DALL-E
        image_url = generate_image(text)
        # Send the image response back to Slack in a thread
        send_image_response(image_url, channel_id, thread_ts)
    else:
        # Send the text response back to Slack in a thread
        send_text_response(response_text, channel_id, thread_ts)


def download_audio_data(url):
    # Implement the logic to download audio data from the given URL
    pass


def send_image_response(image_url, channel_id, thread_ts):
    client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
    client.chat_postMessage(
        channel=channel_id,
        text="Here's the generated image:",
        attachments=[{"image_url": image_url}],
        thread_ts=thread_ts
    )


def send_text_response(text, channel_id, thread_ts):
    client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
    client.chat_postMessage(
        channel=channel_id,
        text=text,
        thread_ts=thread_ts
    )
