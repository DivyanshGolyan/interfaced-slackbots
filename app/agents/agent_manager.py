import importlib


class Agent:
    def __init__(self):
        self.supported_mime_categories = []
        self.supported_file_types = {}
        self.model_adapter = None
        self.end_model = None

    async def process_conversation(self, conversation):
        raise NotImplementedError("This method should be implemented by subclasses.")

    async def process_message(self, message):
        raise NotImplementedError("This method should be implemented by subclasses.")

    async def process_file(self, file, message, transformed_message):
        raise NotImplementedError("This method should be implemented by subclasses.")


class AgentManager:
    def __init__(self, slack_bots_config):
        self.agents = {}
        self.initialise_agents(slack_bots_config)

    def initialise_agents(self, slack_bots_config):
        for bot_name, bot_info in slack_bots_config.items():
            agent_class_str = bot_info["agent"]
            module_name, class_name = agent_class_str.rsplit(".", 1)
            module = importlib.import_module(module_name)
            agent_class = getattr(module, class_name)
            self.agents[bot_name] = agent_class()

    def get_agent(self, bot_name):
        return self.agents.get(bot_name)
