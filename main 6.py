import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from datetime import datetime
import uuid
import httpx
import os
import json

app = FastAPI()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "test-token")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

class Message(BaseModel):
    sender: str
    timestamp: datetime
    text: str

class ChatInput(BaseModel):
    chat_id: str
    group_name: str
    participants: List[str]
    messages: List[Message]

database = {
    "chats": {},
    "tasks": {}
}

@app.post("/webhook/messages")
async def receive_chat(chat: ChatInput):
    chat_id = chat.chat_id
    database["chats"][chat_id] = chat

    formatted_conversation = format_for_ia(chat)
    ai_response = await ask_openai(formatted_conversation)

    task_id = str(uuid.uuid4())
    database["tasks"][task_id] = ai_response

    return {"task_id": task_id, "summary": ai_response}

@app.get("/summary/{task_id}")
async def get_summary(task_id: str):
    return database["tasks"].get(task_id, {"error": "Resumen no encontrado"})

def strip_non_ascii(text: str) -> str:
    return ''.join(c for c in text if ord(c) < 128)

def format_for_ia(chat: ChatInput) -> str:
    conversation = ""
    for msg in chat.messages:
        clean_text = strip_non_ascii(msg.text)
        conversation += f"[{msg.timestamp.strftime('%Y-%m-%d %H:%M')}] {msg.sender}: {clean_text}\n"
    return f"Grupo: {chat.group_name}\nParticipantes: {', '.join(chat.participants)}\n\nConversación:\n{conversation}"

async def ask_openai(prompt: str) -> dict:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "Eres un asistente escolar que ayuda a resumir mensajes de padres y extraer acciones clave."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method="POST",
                url=OPENAI_API_URL,
                headers=headers,
                content=json.dumps(body).encode("utf-8")
            )
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            return {
                "summary": content,
                "things_to_bring": [],
                "upcoming_dates": [],
                "cta": []
            }
    except Exception as e:
        return {"summary": "Error consultando IA", "error": str(e)}
