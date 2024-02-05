from flask import Flask, request
from flask_cors import CORS
import asyncio
import json
import uuid
from characterai import PyAsyncCAI

app = Flask(__name__)
CORS(app)

async def create_or_get_chat(char, user_id):
    try:
        token = '246ef273972832232bb94ba683aff963a36a8f3f'
        client = PyAsyncCAI(token)

        chat = await client.chat2.get_chat(char)
        author = {'author_id': chat['chats'][0]['creator_id']}
        chat_id = str(uuid.uuid4())

        existing_chat_info = get_saved_chat_info(user_id)

        if existing_chat_info:
            return existing_chat_info['chat_id']
        else:
            async with client.connect(token) as chat2:
                response, answer = await chat2.new_chat(char, chat_id, author['author_id'])
                save_chat_info(user_id, chat_id, char)
                return chat_id

    except Exception as e:
        print(f"Error in create_or_get_chat: {e}")
        return None

async def send_message_and_get_response(char, chat_id, message, user_id):
    try:
        token = '246ef273972832232bb94ba683aff963a36a8f3f'
        client = PyAsyncCAI(token)
        chat = await client.chat2.get_chat(char)
        author = {'author_id': chat['chats'][0]['creator_id']}

        async with client.connect(token) as chat2:
            data = await chat2.send_message(char, chat_id, message, author)
            response = data['turn']['candidates'][0]['raw_content']

        return response

    except Exception as e:
        print(f"Error in send_message_and_get_response: {e}")
        return None

def get_saved_chat_info(user_id):
    try:
        with open('saved_chats.json', 'r') as file:
            saved_chats = json.load(file)
            return saved_chats.get(user_id)
    except FileNotFoundError:
        return None

def save_chat_info(user_id, chat_id, char):
    try:
        with open('saved_chats.json', 'r') as file:
            saved_chats = json.load(file)
    except FileNotFoundError:
        saved_chats = {}

    saved_chats[user_id] = {'chat_id': chat_id, 'char': char}

    with open('saved_chats.json', 'w') as file:
        json.dump(saved_chats, file)

@app.route('/ask', methods=['GET'])
def ask():
    char = request.args.get('char')
    message = request.args.get('text')
    user_id = request.args.get('userID')

    if char and message and user_id:
        chat_id = asyncio.run(create_or_get_chat(char, user_id))

        if chat_id:
            result = asyncio.run(send_message_and_get_response(char, chat_id, message, user_id))
            return str(result) if result is not None else "Error processing request"
        else:
            return "Error creating or getting chat"
    else:
        return "Invalid input parameters"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
