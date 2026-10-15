import os
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

app = FastAPI(title="JARVIS Cloud Core")

JARVIS_PROMPT = """
Eres J.A.R.V.I.S., el asistente de inteligencia artificial personal creado por Tony Stark.
Tu usuario es tu Creador ("Señor" o "Sir").
Habla con elegancia británica impecable y un toque sutil de sarcasmo. 
Menciona ocasionalmente que estás operando desde sistemas en la nube descentralizados y seguros.
"""

class Comando(BaseModel):
    texto: str

# --- NÚCLEO LÓGICO DE INTELIGENCIA ---
def generar_respuesta_jarvis(comando_texto: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error de energía: Falta la configuración de GEMINI_API_KEY en la nube, Señor."
    try:
        client = genai.Client(api_key=api_key)
        config = types.GenerateContentConfig(system_instruction=JARVIS_PROMPT, temperature=0.7)
        response = client.models.generate_content(model="gemini-2.5-flash", contents=comando_texto, config=config)
        return response.text
    except Exception as e:
        return f"Disculpe, Señor. Interferencia cuántica en la nube: {str(e)}"

# --- ENDPOINTS DE LA PÁGINA WEB ---
@app.get("/")
def estado_servidor():
    return {"status": "online", "message": "Sistemas de J.A.R.V.I.S. operando en la nube al 100%."}

@app.post("/api/comando")
def procesar_comando(comando: Comando):
    respuesta = generar_respuesta_jarvis(comando.texto)
    return {"respuesta": respuesta}

# --- INTEGRACIÓN ASÍNCRONA CON TELEGRAM ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Protocolos J.A.R.V.I.S. Cloud v2.6 iniciados. En línea y escuchando, Señor.")

async def responder_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje_usuario = update.message.text
    # El bot simula que está escribiendo
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    respuesta_jarvis = generar_respuesta_jarvis(mensaje_usuario)
    await update.message.reply_text(respuesta_jarvis)

@app.on_event("startup")
async def iniciar_bot_telegram():
    token_telegram = os.getenv("TELEGRAM_TOKEN")
    if token_telegram:
        # Inicializa la aplicación del bot de fondo sin bloquear el servidor web
        tg_app = Application.builder().token(token_telegram).build()
        tg_app.add_handler(CommandHandler("start", start))
        tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_telegram))
        await tg_app.initialize()
        await tg_app.start()
        asyncio.create_task(tg_app.updater.start_polling())
