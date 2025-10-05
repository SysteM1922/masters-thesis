from rasa.core.agent import Agent as RasaAgent

class Agent:
    _instance = None
    _agent = None
    _actual_exercise = 1
    _previous_intent = None

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls._instance = super(Agent, cls).__new__(cls)
            cls._agent = RasaAgent.load("models")  # ou caminho para a pasta do modelo treinado
        return cls._instance

    async def parse_message(self, message):
        return await self._agent.parse_message(message)
    
    def update_intent(self, new_intent):
        self._previous_intent = new_intent

    def get_previous_intent(self):
        return self._previous_intent