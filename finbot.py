import os
import requests
import json
import traceback
import random
import re

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import BIGINT
from flask import Flask, request

from messages import send_loading_message, send_message, send_quick_replies, get_response, \
                     send_text_message, send_buttons

# Configurations
token = os.environ.get('FB_ACCESS_TOKEN')
db_file = os.path.realpath('finbot.db')

# App and modules creations
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(db_file)
db = SQLAlchemy(app)


class User(db.Model):
    """
    Model that keeps user information
    """
    id = db.Column(db.Integer, primary_key=True)
    facebook_id = db.Column(BIGINT(unsigned=True), index=True)
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    profile_pic = db.Column(db.Text)
    locale = db.Column(db.String(20))
    timezone = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.now())

    def __init__(self):
        self.created_at = datetime.now()

    def __repr__(self):
        return '{} {}'.format(self.first_name, self.last_name)


class Category(db.Model):
    """
    Model that store categories
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), index=True)
    name = db.Column(db.String(120))
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.now())

    def __init__(self):
        self.created_at = datetime.now()

    def __repr__(self):
        return '{}'.format(self.name)


class Budget(db.Model):
    """
    Model that store the items and values
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), index=True)
    description = db.Column(db.String(120))
    value = db.Column(db.Float)
    date_time = db.Column(db.DateTime)
    status = db.Column(db.String(120))
    entry_type = db.Column(db.String(120))
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.now())

    def __init__(self):
        self.created_at = datetime.now()
        self.status = 'draft'

    def __repr__(self):
        return '{}'.format(self.description)


class Conversation(db.Model):
    """
    Model that stores the conversation context
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    status = db.Column(db.String(120))
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.now())

    def __init__(self):
        self.created_at = datetime.now()


def get_or_create_user(sender):
    """
    Receives the user data from Facebook
    """
    user = User.query.filter_by(facebook_id=sender).first()

    # If user does not exists, we create it
    if not user:
        r = requests.get('https://graph.facebook.com/v2.6/{}?access_token={}'.format(sender, token))
        response = r.json()

        if response:
            user = User()

            user.facebook_id = sender
            user.first_name = response["first_name"]
            user.last_name = response["last_name"]
            user.profile_pic = response["profile_pic"]
            user.locale = response["locale"]
            user.timezone = response["timezone"]
            user.gender = response["gender"]

            db.session.add(user)
            db.session.commit()

    return user


def get_or_create_conversation(user_id):
    """
    Return the status of the conversation with an user
    """
    conversation = Conversation.query.filter_by(user_id=user_id).first()

    if not conversation:
        conversation = Conversation()
        conversation.status = 'init'
        conversation.user_id = user_id
        db.session.add(conversation)
        db.session.commit()

    return conversation


def save_categories(user_id, categories):
    """
    Save the new cagtegoies
    """
    category_list = categories.split(',')
    for category in category_list:
        category = category.strip()  # trim
        c = Category.query.filter_by(user_id=user_id, name=category).first()
        if not c:
            c = Category()
            c.user_id = user_id
            c.name = category
            db.session.add(c)

    db.session.commit()


def get_category_list(user_id):
    """
    Returns the text with a category list
    """
    response_text = 'Categorias:\n'
    categories = Category.query.filter_by(user_id=user_id).all()
    for c in categories:
        response_text += '- {}\n'.format(c.name)
    return response_text


def change_conversation_status(user_id, new_status):
    """
    Change the status of a conversation
    """
    conversation = Conversation.query.filter_by(user_id=user_id).first()
    conversation.status = new_status
    db.session.commit()


def verify_quick_message(user_id, sender, payload, conversation_status):
    """
    Verify the user request and the conversation status to manage the response
    """
    if conversation_status == 'begin_add_withdrawal':
        if payload:
            category = Category.query.filter_by(user_id=user_id, name=payload).first()
            send_text_message(sender, get_response('begin_add_data').format('saída', category))

            new_entry = Budget()
            new_entry.user_id = user_id
            new_entry.category_id = category.id
            new_entry.entry_type = 'withdrawal'
            db.session.add(new_entry)
            db.session.commit()

            change_conversation_status(user_id, 'draft_add_withdrawal')
        else:
            # Tries again
            verify_quick_message(user_id, sender, 'withdrawal', None)
    else:
        if payload == 'deposit':
            pass
        if payload == 'withdrawal':
            send_quick_replies(sender, 
                               "Escolha uma categoria...", 
                               'begin_add_withdrawal', 
                               categories=[c.name for c in Category.query.filter_by(user_id=user_id)])
            change_conversation_status(user_id, 'begin_add_withdrawal')
        if payload == 'add_category':
            send_text_message(sender, get_response('begin_add_category'))
            change_conversation_status(user_id, 'begin_add_category')
        if payload == 'list_categories':
            response_text = get_category_list(user_id)
            send_text_message(sender, response_text)
            send_quick_replies(sender, get_response('waiting'))


def verify_new_entry(user_id, sender, text, conversation_status):
    """
    Verify and handles the new entry as a draft
    """

    parts_raw = text.split(',')
    parts = [part.strip() for part in parts_raw]

    description = parts[0]
    value = handle_value(parts[1])
    if len(parts) > 2:
        entry_date = handle_date(parts[3])
    else:
        entry_date = datetime.now()

    if conversation_status != 'confirm_add_withdrawal':
        new_entry = Budget.query.filter_by(user_id=user_id, status='draft', entry_type='withdrawal').first()
    else:
        new_entry = Budget.query.filter_by(user_id=user_id, status='revision', entry_type='withdrawal').first()

    if new_entry:
        new_entry.description = description
        new_entry.value = value
        new_entry.date_time = entry_date
        new_entry.status = 'revision'
        db.session.commit()

    if conversation_status != 'confirm_add_withdrawal':
        change_conversation_status(user_id, 'confirm_add_withdrawal')


def handle_date(raw):
    # TODO: Handle datetime
    return datetime.now()


def handle_value(raw):
    """
    Extracts a float from a given string
    """
    float_number = re.findall(r"[-+]?\d*\.\d+|\d+", raw)
    return float(float_number[0])


@app.route('/')
def index():
    return 'Finbot'

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        try:
            data = json.loads(request.data.decode())
            sender = data['entry'][0]['messaging'][0]['sender']['id']  # Sender ID

            if 'message' in data['entry'][0]['messaging'][0]:
                text = data['entry'][0]['messaging'][0]['message']['text']  # Incoming Message Text
                message_data = data['entry'][0]['messaging'][0]['message']

            if 'postback' in data['entry'][0]['messaging'][0]:
                message_data = data['entry'][0]['messaging'][0]['postback']

            user = get_or_create_user(sender)
            send_loading_message(sender)  # Typing on signal

            conversation = get_or_create_conversation(user.id)  # The conversation status
            print(conversation.status)

            if conversation.status == 'init':
                send_text_message(sender, get_response('intro'))
                send_text_message(sender, 'Ainda não temos categorias cadastradas. Vamos começar com elas?')
                send_text_message(sender, get_response('begin_add_category'))
                
                conversation.status = 'begin_add_category'
                db.session.commit()

            elif conversation.status == 'waiting':
                if 'quick_reply' in message_data:
                    payload = message_data['quick_reply']['payload']
                    verify_quick_message(user.id, sender, payload, conversation.status)
                else:
                    send_quick_replies(sender, get_response('waiting'))

            elif conversation.status == 'begin_add_category':
                save_categories(user.id, text)
                
                conversation.status = 'waiting'
                db.session.commit()

                # Sends the category list
                send_text_message(sender, get_category_list(user.id))

                send_quick_replies(sender, get_response('waiting'))

            elif conversation.status == 'begin_add_withdrawal':
                if 'quick_reply' in message_data:
                    payload = message_data['quick_reply']['payload']
                    verify_quick_message(user.id, sender, payload, conversation.status)
                else:
                    # Tries again
                    verify_quick_message(user.id, sender, 'withdrawal', None)

            elif conversation.status == 'draft_add_withdrawal':
                verify_new_entry(user.id, sender, text, conversation.status)

            elif conversation.status == 'confirm_add_withdrawal':
                if 'postback' in message_data:
                    payload = message_data['postback']['payload']
                    print(payload)
                    send_text_message(sender, 'ok')
                    conversation.status = 'waiting'
                    db.session.commit()
                else:
                    new_entry = Budget.query.filter_by(user_id=user.id, status='revision', entry_type='withdrawal').first()
                    send_buttons(sender, get_response('confirm_add_data').format('saída', 
                                                                                 new_entry.value,
                                                                                 new_entry.date_time.strftime('%d/%m/%Y'),
                                                                                 new_entry.description))


            # message = create_response_message(user, text)
            # send_message(sender, message)
        except Exception as e:
            print(traceback.format_exc())  # something went wrong
    elif request.method == 'GET': # For the initial verification
        if request.args.get('hub.verify_token') == os.environ.get('FB_VERIFY_TOKEN'):
            return request.args.get('hub.challenge')
        return "Wrong Verify Token"
    return "Nothing"

if __name__ == '__main__':
    # Verify if database exists and create it
    if not os.path.isfile(db_file):
        db.create_all()
    app.run(debug=True)
