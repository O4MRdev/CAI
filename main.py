import json
import os 
import uuid
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
from characterai import aiocai

app = Flask(__name__)
CORS(app)

SAVED_CHATS_FILE = 'saved_chats.json'


def get_saved_chat_info(user_id):
    try:
        with open(SAVED_CHATS_FILE, 'r') as file:
            saved_chats = json.load(file)
            return saved_chats.get(user_id)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        print(f"Error in get_saved_chat_info: {e}")
        return None


def save_chat_info(user_id, chat_id, char):
    try:
        try:
            with open(SAVED_CHATS_FILE, 'r') as file:
                saved_chats = json.load(file)
        except FileNotFoundError:
            saved_chats = {}

        saved_chats[user_id] = {'chat_id': chat_id, 'char': char}

        with open(SAVED_CHATS_FILE, 'w') as file:
            json.dump(saved_chats, file)
    except Exception as e:
        print(f"Error in save_chat_info: {e}")


async def create_or_get_chat(char, user_id, token):
    try:
        client = aiocai.Client(token)
        me = await client.get_me()

        # Check for existing chat
        existing_chat_info = get_saved_chat_info(user_id)
        if existing_chat_info:
            return existing_chat_info['chat_id']

        # Create new chat
        async with await client.connect() as chat:
            new, _ = await chat.new_chat(char, me.id)
            chat_id = new.chat_id
            save_chat_info(user_id, chat_id, char)
            return chat_id

    except Exception as e:
        print(f"Error in create_or_get_chat: {e}")
        return None


async def send_message_and_get_response(char, chat_id, message, token):
    try:
        client = aiocai.Client(token)
        me = await client.get_me()

        async with await client.connect() as chat:
            msg = await chat.send_message(char, chat_id, message)
            return msg.name, msg.text

    except Exception as e:
        print(f"Error in send_message_and_get_response: {e}")
        return None


def ask(char, message, user_id, token):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    chat_id = loop.run_until_complete(create_or_get_chat(char, user_id, token))
    if chat_id:
        result = loop.run_until_complete(send_message_and_get_response(char, chat_id, message, token))
        if result:
            name, response_text = result
            return f'{name}: {response_text}'
        else:
            return "Error processing request"
    else:
        return "Error creating or getting chat"


@app.route('/ask', methods=['POST'])
def handle_ask():
    data = request.json
    char = data.get('char')
    message = data.get('message')
    user_id = data.get('user_id')
    token = data.get('token')

    if not char or not message or not user_id or not token:
        return "Invalid input parameters", 400

    response = ask(char, message, user_id, token)
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
