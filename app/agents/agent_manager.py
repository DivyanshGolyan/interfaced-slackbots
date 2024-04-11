import importlib


class Agent:
    def can_process_input(self, input_data):
        """Check if the input data type is supported by the agent."""
        raise NotImplementedError

    async def transform_input(self, input_data):
        """Transform input data into a format that can be processed by the agent."""
        raise NotImplementedError

    async def validate_input(self, input_data):
        """Validate the transformed input."""
        raise NotImplementedError

    async def process_request(self, input_data):
        """Process the request after the validation."""
        raise NotImplementedError


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