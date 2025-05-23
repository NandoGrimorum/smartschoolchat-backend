# Estructura base de un microservicio en FastAPI para procesar mensajes de WhatsApp de un grupo de colegio

from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import httpx
import os

app = FastAPI()

# --- Configuración de API de WhatsApp Business ---
WHATSAPP_API_URL = "https://graph.facebook.com/v19.0/<tu-numero-id>/messages"
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")  # asegúrate de definir esta variable de entorno

# --- Configuración de API de OpenAI ---
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # asegúrate de definir esta variable de entorno

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

# Simulación de base de datos en memoria (puede ser reemplazada por MongoDB, PostgreSQL, etc.)
database = {
    "chats": {},  # chat_id: ChatInput
    "tasks": {},  # task_id: resumen generado + CTA propuestos
}

# --- Endpoint para recibir mensajes del grupo ---

@app.post("/webhook/messages")
async def receive_chat(chat: ChatInput):
    chat_id = chat.chat_id
    database["chats"][chat_id] = chat

    # Preparar payload para enviar a la IA
    formatted_conversation = format_for_ia(chat)

    # Enviar a IA (OpenAI)
    ai_response = await ask_openai(formatted_conversation)

    # Guardar resumen y CTAs sugeridas
    task_id = str(uuid.uuid4())
    database["tasks"][task_id] = ai_response

    # Enviar CTAs al grupo (simulación)
    for cta in ai_response.get("cta", []):
        await send_whatsapp_cta(chat.group_name, cta)

    return {"task_id": task_id, "summary": ai_response}

# --- Formateo del chat para IA ---

def format_for_ia(chat: ChatInput) -> str:
    conversation = ""
    for msg in chat.messages:
        conversation += f"[{msg.timestamp.strftime('%Y-%m-%d %H:%M')}] {msg.sender}: {msg.text}\n"
    return f"Grupo: {chat.group_name}\nParticipantes: {', '.join(chat.participants)}\n\nConversación:\n{conversation}"

# --- Consulta real a OpenAI (GPT-4) ---

async def ask_openai(formatted_text: str) -> dict:
    prompt = f"""
Actúa como un asistente virtual para un grupo de WhatsApp de padres y madres de familia del colegio.

1. Resume brevemente el tema principal de la conversación.
2. Enumera tareas o cosas que deben traer los estudiantes.
3. Menciona actividades próximas y fechas importantes.
4. Señala preguntas o dudas abiertas.
5. Si corresponde, sugiere un CTA interactivo como una encuesta o confirmación.

Responde en formato JSON con las siguientes claves:
summary, things_to_bring, upcoming_dates, cta (lista de objetos con question y options).

Conversación:
{formatted_text}
"""

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "Eres un asistente que estructura resúmenes escolares de WhatsApp"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(OPENAI_API_URL, headers=headers, json=body)
        if response.status_code == 200:
            content = response.json()
            try:
                return eval(content["choices"][0]["message"]["content"])
            except:
                return {"summary": "Error procesando respuesta IA"}
        else:
            print("Error OpenAI:", response.text)
            return {"summary": "Error consultando IA"}

# --- Enviar CTA a WhatsApp Business ---

async def send_whatsapp_cta(group_name: str, cta: dict):
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": "<número-del-grupo-o-contacto>",
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": cta.get("question")},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": opt, "title": opt}}
                    for opt in cta.get("options", [])
                ]
            }
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(WHATSAPP_API_URL, headers=headers, json=payload)
        if response.status_code != 200:
            print("Error enviando CTA:", response.text)

# --- Endpoint para consultar resumen generado ---

@app.get("/summary/{task_id}")
async def get_summary(task_id: str):
    return database["tasks"].get(task_id, {"error": "Resumen no encontrado"})
