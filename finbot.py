import os
import requests
import json
import traceback
import random

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import BIGINT
from flask import Flask, request

# Configurations
token = os.environ.get('FB_ACCESS_TOKEN')
db_file = os.path.realpath('finbot.db')

# App and modules creations
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(db_file)
db = SQLAlchemy(app)

# Verify if database exists and create it
if not os.path.isfile(db_file):
    db.create_all()


class User(db.Model):
    """
    Model that keeps user information
    """
    id = db.Column(db.Integer, primary_key=True)
    facebook_id = db.Column(BIGINT(unsigned=True))
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    profile_pic = db.Column(db.Text)
    locale = db.Column(db.String(20))
    timezone = db.Column(db.Integer)
    gender = db.Column(db.String(20))

    def __init__(self, first_name):
        self.first_name = first_name

    def __repr__(self):
        return '{} {}'.format(self.first_name, self.last_name)


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

            user.first_name = response["first_name"]
            user.last_name = response["last_name"]
            user.profile_pic = response["profile_pic"]
            user.locale = response["locale"]
            user.timezone = response["timezone"]
            user.gender = response["gender"]

            db.session.add(user)
            db.session.commit()

    return user


@app.route('/')
def index():
    return 'Finbot'

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        try:
            data = json.loads(request.data.decode())
            text = data['entry'][0]['messaging'][0]['message']['text'] # Incoming Message Text
            sender = data['entry'][0]['messaging'][0]['sender']['id'] # Sender ID

            user = get_or_create_user(sender)

            payload = {'recipient': {'id': sender}, 'message': {'text': "Hello, {}".format(user.first_name)}}
            r = requests.post('https://graph.facebook.com/v2.6/me/messages/?access_token=' + token, json=payload)
        except Exception as e:
            print(traceback.format_exc())  # something went wrong
    elif request.method == 'GET': # For the initial verification
        if request.args.get('hub.verify_token') == os.environ.get('FB_VERIFY_TOKEN'):
            return request.args.get('hub.challenge')
        return "Wrong Verify Token"

if __name__ == '__main__':
    app.run(debug=True)
