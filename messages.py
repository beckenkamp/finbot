import os
import random
import requests

# Configurations
token = os.environ.get('FB_ACCESS_TOKEN')

chat_responses = {}

chat_responses['greetings'] = [
    'Oi, {name}',
    'Olá, {name}',
]

chat_responses['intro'] = [
    'Olá! Eu sou o Fin e estou aqui para ajudá-lo a organizar seu orçamento doméstico! Vamos começar?',
    'Oi! Meu nome é Fin e meu objetivo é lhe ajudar a organizar o seu orçamento. Vamos começar?',
]

chat_responses['no_answer'] = [
    'Estou sem resposta para você...',
    'Desculpe, não entendi.',
    'Ooops, não captei vossa mensagem...',
]

chat_responses['begin_add_data'] = [
    'Vamos adicionar uma {} para a categoria {}. Me diga uma descrição, um valor e uma data, separados por vírgula.',
]

chat_responses['confirm_add_data'] = [
    'Vou adicionar uma {} no valor de R$ {} no dia {} com descrição {}. Está correto?',
]

chat_responses['sorry_wrong_add'] = [
    'Desculpe se não entendi direito :( Vamos alterar isso então. Me fale a descrição, o valor e a data novamente.',
    'Oh, oh... Foi mal =/ Bora tentar de novo? Me fale a descrição, o valor e a data novamente.',
    'Putz =( Vamos tentar de novo. Me fale a descrição, o valor e a data novamente.',
]

chat_responses['begin_add_category'] = [
    'Vamos adicionar algumas novas categorias? Envie as categorias que quer cadastrar, separadas por vírgula.',
]

chat_responses['waiting'] = [
    'O que fazer agora?',
    'O que vamos fazer?',
    'Escolha uma opção...',
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
    'oi',
    'olá',
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


# CREATE FACEBOOK MESSENGER STYLE RESPONSES
def get_quick_replies(options_type='default', **kwargs):
    """
    Creates the quick replies payload
    """
    if options_type == 'default':
        quick_replies = [{
                            'content_type': 'text',
                            'title': 'Adicionar saída',
                            'payload': 'withdrawal'
                        },
                        {
                            'content_type': 'text',
                            'title': 'Adicionar entrada',
                            'payload': 'deposit'
                        },
                        {
                            'content_type': 'text',
                            'title': 'Ver categorias',
                            'payload': 'list_categories'
                        },
                        {
                            'content_type': 'text',
                            'title': 'Adicionar categoria',
                            'payload': 'add_category'
                        }]
    elif options_type == 'begin_add_data':
        # Returns a list of categories as quick replies
        quick_replies = []
        for category in kwargs.get('categories', []):
            payload = {
                'content_type': 'text',
                'title': category,
                'payload': category
            }
            quick_replies.append(payload)

    return quick_replies


def get_button_reply(options_type='default', **kwargs):
    """
    Creates button replies
    """
    if options_type == 'default':
        button_reply = [
              {
                'type': 'postback',
                'title': 'Sim, está correto',
                'payload': 'finalize'
              },
              {
                'type': 'postback',
                'title': 'Não, quero mudar',
                'payload': 'retry'
              }
            ]

    return button_reply


def send_message(payload):
    """
    Sends a message to the user
    """
    requests.post('https://graph.facebook.com/v2.6/me/messages/?access_token=' + token, json=payload)


def send_loading_message(sender):
    """
    Sends a signal to messenger informing is loading the data
    """
    payload = {'recipient': {'id': sender}, 'sender_action': 'typing_on'}
    send_message(payload)


def create_response_message(user, income_message):
    """
    Build the response to any message
    """
    response_type = define_response_by_keyword(income_message)
    if response_type:
        return get_response(response_type).format(name=user.first_name)
    return get_response(None)


def send_text_message(sender, message):
    payload = {'recipient': {'id': sender}, 'message': {'text': message}}
    send_message(payload)


def send_quick_replies(sender, message, options_type="default", **kwargs):
    """
    Send a quick reply style of payload
    """
    options = get_quick_replies(options_type, **kwargs)
    payload = {'recipient': {'id': sender}, 'message': {'text': message, 'quick_replies': options}}
    send_message(payload)


def send_buttons(sender, message, options_type="default", **kwargs):
    """
    Send a button style of payload
    """
    options = get_button_reply(options_type, **kwargs)
    payload = {
        'recipient': {
            'id': sender
        }, 
        'message': {
            'attachment': {
                'type': 'template', 
                'payload': {
                    'template_type': 'button',
                    'text': message,
                    'buttons': options
                }
            }
        }
    }
    print(payload)
    send_message(payload)

