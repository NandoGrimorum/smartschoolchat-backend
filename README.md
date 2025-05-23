
# Microservicio Chat Escolar con WhatsApp + OpenAI

Este microservicio recibe mensajes de un grupo de WhatsApp escolar, los procesa con GPT-4 (OpenAI), resume la conversación y propone acciones como encuestas o confirmaciones, enviadas automáticamente a través de WhatsApp Business API.

---

## 🚀 Despliegue en Render (Fácil y Gratis)

### 1. Sube este repositorio a tu cuenta de GitHub

### 2. Ve a https://render.com y crea un servicio nuevo:

- Click en "New Web Service"
- Selecciona "Deploy from GitHub"
- Elige este repositorio
- **Environment:** Docker
- Render usará el Dockerfile para construir

### 3. Agrega variables de entorno:

- `WHATSAPP_TOKEN` → tu token de la API de WhatsApp Business
- `OPENAI_API_KEY` → tu API Key de OpenAI

### 4. Tu API estará disponible en una URL como:
```
https://microservicio-chat.onrender.com
```

---

## 📦 Endpoints

### POST `/webhook/messages`
Recibe mensajes del grupo.

### GET `/summary/{task_id}`
Consulta resumen y acciones generadas.

---

## 🧾 Requisitos

- Cuenta en WhatsApp Business API
- Clave API de OpenAI
- Cuenta gratuita en Render

---

## 📄 Licencia
MIT
