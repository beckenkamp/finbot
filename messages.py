import random


chat_responses = {}

chat_responses['greetings'] = [
    'Oi, {name}',
    'Olá, {name}',
]

chat_responses['intro'] = [
    'Eu sou o Fin e estou aqui para ajudá-lo a organizar seu orçamento doméstico!',
    'Meu nome é Fin e meu objetivo é lhe ajudar a organizar o seu orçamento.',
]

chat_responses['no_answer'] = [
    'Estou sem resposta para você...',
    'Desculpe, não entendi.',
    'Ooops, não captei vossa mensagem...',
]

def get_response(response_type):
    """
    Return a random string message from a given type
    """
    if response_type in chat_responses:
        return random.choice(chat_responses[response_type])
    return random.choice(chat_responses['no_answer'])


chat_keywords = {}

chat_keywords['greetings'] = [
    'Oi',
    'Olá',
]

chat_keywords['intro'] = [
    'o que você faz',
    'quem é você',
    'qual o seu objetivo',
    'por que você existe',
]

def define_response_by_keyword(message):
    """
    Verify the keywords to return a response type
    """
    for key in chat_keywords:
        for value in chat_keywords[key]:
            if value in message.lower():
                return key
