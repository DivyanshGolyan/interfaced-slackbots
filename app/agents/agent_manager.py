class Agent:
    def can_process_input(self, input_data):
        """Check if the input data type is supported by the agent."""
        raise NotImplementedError

    def transform_input(self, input_data):
        """Transform input data into a format that can be processed by the agent."""
        raise NotImplementedError

    def validate_input(self, input_data):
        """Validate the transformed input."""
        raise NotImplementedError

    async def process_request(self, input_data):
        """Process the request after the validation."""
        raise NotImplementedError


class AgentManager:
    def __init__(self):
        self.agents = {}

    def register_agent(self, agent_name, agent):
        self.agents[agent_name] = agent

    async def handle_request(self, thread, agent_name):
        agent = self.agents.get(agent_name)
        if agent:
            return await agent.process_request(thread)
        else:
            raise ValueError(f"No agent found for the given name: {agent_name}")
