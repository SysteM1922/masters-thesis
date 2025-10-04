from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import random

load_dotenv(".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AUDIO_FOLDER = "audio"

openai = AsyncOpenAI(
    api_key=OPENAI_API_KEY
)

async def text_to_speech(text: str, intent: str):
    """Convert text to speech using OpenAI's TTS model."""
    
    # check if audio/{intent}/ folder exists and has at least 5 files
    if os.path.exists(f"{AUDIO_FOLDER}/{intent}/"):
        if len(os.listdir(f"{AUDIO_FOLDER}/{intent}/")) > 4:
            files = os.listdir(f"{AUDIO_FOLDER}/{intent}/")
            return f"{AUDIO_FOLDER}/{intent}/{random.choice(files)}"
    
    else:
        os.makedirs(f"{AUDIO_FOLDER}/{intent}/", exist_ok=True)

    response = await openai.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text,
        instructions="Speak in European Portuguese",
        response_format="mp3",
    )
    current_audio_folder_size = len(os.listdir(f"{AUDIO_FOLDER}/{intent}/"))
    filename = f"{AUDIO_FOLDER}/{intent}/{intent}_{current_audio_folder_size}.mp3"
    response.write_to_file(filename)
    return filename

async def greet(): # intent
    texts = [
        "Olá! Como posso ajudar?",
    ]
    full_text = " ".join(texts)
    filename = await text_to_speech(full_text, "greet")
    return filename

async def affirm(): # intent
    texts = [
        "Entendido!",
    ]
    full_text = random.choice(texts)
    filename = await text_to_speech(full_text, "affirm")
    return filename

async def next_exercise(): # intent
    texts = [
        "Tem a certeza que quer passar este exercício?",
    ]
    full_text = " ".join(texts)
    print(full_text)
    filename = await text_to_speech(full_text, "next_exercise")
    return filename

async def help(): # intent
    texts = [
        "Estou aqui para ajudar. De momento apenas posso explicar-lhe o exercício que estamos a fazer ou então podemos passar para o próximo exercício.",
        "Se precisar de ajuda, é só dizer Olá Jim!",
    ]
    full_text = " ".join(texts)
    filename = await text_to_speech(full_text, "help")
    return filename

async def help_exercise(exercise_nr: int): # intent
    if (exercise_nr == 1):
        return await arms_exercise()
    elif (exercise_nr == 2):
        return await legs_exercise()
    elif (exercise_nr == 3):
        return await walk_exercise()

async def presentation():
    texts = [
        "Eu sou o Jim, o seu assistente de treino virtual.",
        "Estou aqui para ajudar a guiá-lo através dos seus exercícios, dar-lhe motivação e garantir que mantenha uma execução correta durante o treino.",
        "Para falar comigo, basta dizer Olá Jim!",
        "Se precisar de ajuda, é só dizer!"
    ]
    full_text = " ".join(texts)
    filename = await text_to_speech(full_text, "presentation")
    return filename

async def presentation_0():
    texts = [
        "Olá! Eu sou o Jim, o seu assistente de treino virtual. Bem-vindo ao seu ginásio em casa!",
        "Estou aqui para ajudar a guiá-lo através dos seus exercícios, dar-lhe motivação e garantir que mantenha uma execução correta durante o treino.",
        "Antes de começarmos vamos conversar um pouco!"
    ]
    full_text = " ".join(texts)
    filename = await text_to_speech(full_text, "presentation_0")
    return filename

async def presentation_1():
    texts = [
        "Sempre que quiser falar comigo basta dizer; Olá Jim!",
        "Vamos tentar? Diga Olá Jim!",
    ]
    full_text = " ".join(texts)
    filename = await text_to_speech(full_text, "presentation_1")
    return filename

async def presentation_2():
    texts = [
        "Muito bem! Diga-me o que comeu hoje de manhã.",
    ]
    full_text = " ".join(texts)
    filename = await text_to_speech(full_text, "presentation_2")
    return filename

async def presentation_3():
    texts = [
        "Ótimo! Agora diga-me, qual é a sua cor preferida?",
    ]
    full_text = " ".join(texts)
    filename = await text_to_speech(full_text, "presentation_3")
    return filename

async def presentation_4():
    texts = [
        "Excelente! Agora que percebeu como falar comigo. Diga-me quando quiser começar o treino.",
    ]
    full_text = " ".join(texts)
    filename = await text_to_speech(full_text, "presentation_4")
    return filename

async def start_training_session():
    texts = [
        "Tem a certeza que quer começar o treino?",
    ]
    full_text = " ".join(texts)
    filename = await text_to_speech(full_text, f"start_training_session")
    return filename

async def arms_exercise():
    texts = [
        "Para este exercício coloque-se à frente da tela.",
        "Mantenha sempre as costas direitas e levante os braços esticados até acima dos ombros.",
        "Abra os braços até ficarem paralelos ao chão, como se fosse um avião.",
        "Repita o movimento 10 vezes. Vamos começar?"
    ]
    full_text = " ".join(texts)
    filename = await text_to_speech(full_text, f"arms_exercise")
    return filename

async def legs_exercise():
    texts = [
        "Para este exercício irá precisar de uma cadeira.",
        "Coloque a cadeira numa posição diagonal relativamente à tela de forma a ver as suas duas pernas.",
        "Sente-se na cadeira e levante uma perna de cada vez, esticando-a para a frente.",
        "Primeiro irá só fazer o movimento com uma perna e após 10 repetições, troca para a outra perna.",
        "Vamos começar?"
    ]
    full_text = " ".join(texts)
    filename = await text_to_speech(full_text, f"legs_exercise")
    return filename

async def walk_exercise():
    texts = [
        "Para este exercício, fique em pé e comece a marchar no lugar.",
        "Levante os joelhos o mais alto que conseguir, como se estivesse a caminhar.",
        "Balance os braços para ajudar no movimento e manter o equilíbrio.",
        "As mãos devem balançar o suficiente para ficarem por cima da perna contrária.",
        "mantenha a coordenação e levante sempre a perna do lado contrário do braço que baloiçou.",
        "Terá de caminhar durante 60 segundos e os seus passos corretos serão contados.",
        "Vamos começar?"
    ]
    full_text = " ".join(texts)
    filename = await text_to_speech(full_text, f"walk_exercise")
    return filename

async def exercise_done():
    texts = [
        "Parabéns por ter completado o exercício!",
        "Ótimo trabalho! Está a ir muito bem.",
        "Lembre-se de manter-se hidratado e fazer pausas quando necessário.",
    ]
    full_text = " ".join(texts)
    filename = await text_to_speech(full_text, "exercise_done")
    return filename

async def goodbye(): # intent
    texts = [
        "Até logo! Foi ótimo treinar consigo hoje.",
        "Lembre-se de manter-se ativo e cuidar do seu corpo.",
        "Estou ansioso para o nosso próximo treino juntos. Adeus!",
    ]
    full_text = " ".join(texts)
    filename = await text_to_speech(full_text, "goodbye")
    return filename

async def change_legs():
    texts = [
        "Vamos trocar de perna. Prepare-se!",
    ]
    full_text = " ".join(texts)
    filename = await text_to_speech(full_text, "change_legs")
    return filename

async def simple_exercise_done():
    texts = [
        "Excelente! Concluiu o exercício com sucesso.",
        "Bom trabalho, concluiu o exercício!",
        "Ótimo esforço! Terminou o exercício.",
    ]
    full_text = random.choice(texts)
    filename = await text_to_speech(full_text, "simple_exercise_done")
    return filename

async def lets_go():
    texts = [
        "Vamos lá!",
        "Vamos lá começar!",
        "Vamos a isto!",
    ]
    full_text = random.choice(texts)
    filename = await text_to_speech(full_text, "lets_go")
    return filename

async def unknown():
    texts = [
        "Desculpe, não entendi. Pode repetir, por favor?",
        "Não percebi o que disse. Pode tentar novamente?",
        "Pode repetir? Não consegui compreender.",
    ]
    full_text = random.choice(texts)
    filename = await text_to_speech(full_text, "unknown")
    return filename