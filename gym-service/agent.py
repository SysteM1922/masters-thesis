from rasa.core.agent import Agent as RasaAgent

class Agent:
    _instance = None
    _agent = None
    _actual_exercise = 1
    _previous_intent = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Agent, cls).__new__(cls)
        return cls._instance

    @classmethod
    def init(cls):
        instance = cls()
        if instance._agent is None:
            instance._agent = RasaAgent.load("models")  # ou caminho para a pasta do modelo treinado
        return instance

    @staticmethod
    async def parse_message(message):
        instance = Agent.get_instance()
        return await instance._agent.parse_message(message)

    @classmethod
    def get_instance(cls):
        if cls._instance is None or cls._instance._agent is None:
            return cls.init()
        return cls._instance
    
    @classmethod
    def update_intent(cls, new_intent):
        instance = cls.get_instance()
        instance._previous_intent = new_intent