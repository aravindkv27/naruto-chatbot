from asyncio import events
from cgi import test
from cgitb import text
from crypt import methods
from http import client
import imp
from tabnanny import check
from urllib import request
import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter

env_path = Path(".") / '.env'

load_dotenv(dotenv_path=env_path)

app = Flask(__name__)

slack_event_ada = SlackEventAdapter(os.environ['SIGNING_SECRET'],"/slack/events", app)


client = slack.WebClient(os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']

message_counts= {}
welcome_messages = {}

class WelcomeMessage:

    START_TEXT = {
        'type' : 'section',
        'text' : {
            'type' : 'mrkdwn',
            'text' : (
                'Welcome to naruto channel! \n\n'
                '*Get Started by completing the tasks!*'
            )
        }
    }

    DIVIDER = {'type':'divider'}
    
    def __init__(self, channel, user):

        self.channel = channel
        self.user = user
        self.icon_emoji = ':wave:'
        self.timestamp = ''
        self.completed = False

    def get_message(self):

        return {

            'ts' : self.timestamp,
            'channel' : self.channel,
            'username' : 'Ino Yamanaka',
            'icon_emoji': self.icon_emoji,
            'blocks': [
                self.START_TEXT,
                self.DIVIDER,
                self._get_reaction_task()
            ]

        }

    def _get_reaction_task(self):

        checkmark = ':white_check_mark:'
        if not self.completed:
            checkmark = ':white_large_square:'

        text = f'{checkmark} *React to this message!*'

        return {'type':'section','text':{'type':'mrkdwn', 'text':text}}

def send_welcome_mess(channel,user):

    # welcome_messages[channel][user] = welcome
    welcome = WelcomeMessage(channel,user)
    message = welcome.get_message()
    response = client.chat_postMessage(**message)
    welcome.timestamp = response['ts']

    if channel not in welcome_messages:

        welcome_messages[channel] = {}
    
    welcome_messages[channel][user] = welcome
    

@slack_event_ada.on('message')
def message(payload):

    event = payload.get('event',{})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')

    if user_id != None and BOT_ID != user_id:
        if user_id in message_counts:
            message_counts[user_id] += 1
        else:
            message_counts[user_id] = 1
        # client.chat_postMessage(channel=channel_id, text = text)

        if text.lower() == 'start':

            send_welcome_mess(f'@{user_id}',user_id)

#reaction handling
@slack_event_ada.on('reaction_added')
def reaction(payload):

    event = payload.get('event',{})
    channel_id = event.get('item',{})('channel')
    user_id = event.get('user')

    if channel_id not in welcome_messages:

        return
    
    welcome = welcome_messages[channel_id][user_id]
    welcome.completed = True

    message = welcome.get_message()
    updated_message = client.chat_update(**message)
    welcome.timestamp = updated_message['ts']


# COMMAND        
@app.route('/message-count',methods=['POST'])
def message_count():

    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    message_count = message_counts.get(user_id, 0)

    client.chat_postMessage(channel=channel_id, text= f"Sasuke Uchicha: {message_count}")
    # return Response(), 200


if __name__ == "__main__":

    app.run(debug=True, port=5000)