from rasa.core.agent import Agent
import asyncio

agent = Agent.load("models")  # ou caminho para a pasta do modelo treinado

async def main():
    while True:
        user_input = input("Você: ")
        result = await agent.handle_text(user_input)
        print(result)

asyncio.run(main())