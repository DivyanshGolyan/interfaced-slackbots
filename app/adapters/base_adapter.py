class LLMAdapter:
    def convert_message(self, message):
        raise NotImplementedError

    def convert_conversation(self, conversation):
        raise NotImplementedError
