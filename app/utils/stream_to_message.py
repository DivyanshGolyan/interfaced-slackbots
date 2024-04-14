from app.objects import *
import re


async def handle_stream(end_model, payload):
    text_buffer = ""  # Buffer to accumulate text
    async for char_stream in end_model.call_model(payload, stream=True):
        if char_stream is not None:
            text_buffer += char_stream  # Accumulate text from the stream

        # Process complete sentences in the buffer
        while True:
            # Search for the end of a sentence marked by punctuation followed by a space/newline or end of text
            match = re.search(r"(?<=[.!?])(\s|$)", text_buffer)
            if not match:
                break  # No complete sentence found, wait for more text

            # Extract the sentence and adjust the buffer
            end_of_sentence = match.end()
            sentence = text_buffer[:end_of_sentence]  # Keep original whitespace
            text_buffer = text_buffer[end_of_sentence:]

            # Yield the complete sentence, check if it's not just whitespace
            if sentence.strip():
                yield AgentResponse(sentence)

    # After the stream ends, check if there's any remaining text in the buffer
    if text_buffer.strip():
        yield AgentResponse(
            text_buffer
        )  # Yield any remaining incomplete sentence with original whitespace
