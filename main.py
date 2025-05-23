from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
from datetime import datetime
import uuid
import httpx
import os

app = FastAPI()

# --- Configuración de API de WhatsApp y OpenAI ---
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "test-token")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# --- Modelos de datos ---

class Message(BaseModel):
    sender: str
    timestamp: datetime
    text: str

class ChatInput(BaseModel):
    chat_id: str
    group_name: str
    participants: List[str]
    messages: List[Message]

# Simulación de base de datos
database = {
    "chats": {},
    "tasks": {}
}

# --- Endpoint para recibir mensajes ---

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

# --- Utilidades ---

def format_for_ia(chat: ChatInput) -> str:
    conversation = ""
    for msg in chat.messages:
        conversation += f"[{msg.timestamp.strftime('%Y-%m-%d %H:%M')}] {msg.sender}: {msg.text}\n"
    return f"Grupo: {chat.group_name}\nParticipantes: {', '.join(chat.participants)}\n\nConversación:\n{conversation}"

async def ask_openai(prompt: str) -> dict:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}".encode("utf-8").decode("utf-8"),
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
            response = await client.post(OPENAI_API_URL, headers=headers, json=body)
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
