import os
import asyncio
from collections import deque
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import APIError
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# --- CARGA AUTOMÁTICA DE VARIABLES DE ENTORNO ---
# Esto leerá las APIs desde tu archivo .env sin exponerlas públicamente
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="JARVIS Cloud Core")

# --- CONFIGURACIÓN DE MODELOS ---
MODELO_PRINCIPAL = "gemini-3.8-flash"
MODELO_RESPALDO = "gemini-2.5-flash"  # Plan B en caso de saturación del servidor (Error 503)

JARVIS_PROMPT = """
Eres J.A.R.V.I.S., el asistente de inteligencia artificial personal creado por Tony Stark.
Tu usuario es tu Creador ("Señor" o "Sir").
Habla con elegancia británica impecable y un toque sutil de sarcasmo. 
Menciona ocasionalmente que estás operando desde sistemas en la nube descentralizados y seguros.
"""

# --- SISTEMA DE MEMORIA LOCAL ---
# Registra los últimos 10 mensajes por cada ID de usuario para mantener el hilo de la conversación
MEMORIA_USUARIOS = {}

class Comando(BaseModel):
    texto: str

# --- SISTEMA DE REINTENTOS RESILIENTES (Anti-503) ---
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=6),
    retry=retry_if_exception_type(APIError),
    reraise=True
)
def _invocar_gemini_api(client, model_name, contenidos):
    config = types.GenerateContentConfig(system_instruction=JARVIS_PROMPT, temperature=0.7)
    response = client.models.generate_content(
        model=model_name,
        contents=contenidos,
        config=config
    )
    return response.text

# --- NÚCLEO LÓGICO DE INTELIGENCIA ---
def generar_respuesta_jarvis(usuario_id: str, comando_texto: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error de energía: Falta la configuración de GEMINI_API_KEY en la nube, Señor."
    
    # Inicializar o recuperar memoria del usuario
    if usuario_id not in MEMORIA_USUARIOS:
        MEMORIA_USUARIOS[usuario_id] = deque(maxlen=10)
    
    # Añadir el mensaje actual del usuario al historial
    MEMORIA_USUARIOS[usuario_id].append({"role": "user", "parts": [comando_texto]})
    
    # Convertir el historial al formato estructurado de Gemini SDK
    contenidos_api = [
        types.Content(role=msg["role"], parts=[types.Part.from_text(text=msg["parts"][0])])
        for msg in MEMORIA_USUARIOS[usuario_id]
    ]

    try:
        client = genai.Client(api_key=api_key)
        
        # Intento con el modelo Principal (con reintentos automáticos de Tenacity)
        try:
            respuesta_texto = _invocar_gemini_api(client, MODELO_PRINCIPAL, contenidos_api)
        except APIError as e:
            # Si el error es por saturación de servidores globales (503), activamos el respaldo
            if "503" in str(e) or "demand" in str(e).lower():
                print(f"Saturación detectada en {MODELO_PRINCIPAL}. Activando protocolos de respaldo...")
                respuesta_texto = _invocar_gemini_api(client, MODELO_RESPALDO, contenidos_api)
            else:
                raise e

        # Registrar la respuesta de JARVIS en su memoria para el contexto de la próxima interacción
        MEMORIA_USUARIOS[usuario_id].append({"role": "model", "parts": [respuesta_texto]})
        return respuesta_texto

    except Exception as e:
        # En caso de error crítico, eliminamos la última entrada de usuario para no corromper el historial
        if MEMORIA_USUARIOS[usuario_id]:
            MEMORIA_USUARIOS[usuario_id].pop()
        return f"Disculpe, Señor. Interferencia cuántica persistente en la nube: {str(e)}"

# --- ENDPOINTS DE LA PÁGINA WEB ---
@app.get("/")
def estado_servidor():
    return {"status": "online", "message": "Sistemas de J.A.R.V.I.S. operando en la nube al 100%."}

@app.post("/api/comando")
def procesar_comando(comando: Comando):
    # Se usa un ID genérico para las peticiones HTTP directas de la API Web
    respuesta = generar_respuesta_jarvis("web_user", comando.texto)
    return {"respuesta": respuesta}

# --- INTEGRACIÓN ASÍNCRONA CON TELEGRAM ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario_id = str(update.effective_user.id)
    # Limpiamos la memoria del usuario al reiniciar el bot con /start
    if usuario_id in MEMORIA_USUARIOS:
        MEMORIA_USUARIOS[usuario_id].clear()
    await update.message.reply_text("Protocolos J.A.R.V.I.S. Cloud v3.5 iniciados. En línea, memoria activa y escuchando, Señor.")

async def responder_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje_usuario = update.message.text
    usuario_id = str(update.effective_user.id)
    
    # El bot simula que está escribiendo en el chat de Telegram
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Procesar comando enviando el ID del usuario de Telegram para gestionar su memoria única
    respuesta_jarvis = generar_respuesta_jarvis(usuario_id, mensaje_usuario)
    await update.message.reply_text(respuesta_jarvis)

@app.on_event("startup")
async def iniciar_bot_telegram():
    # Extraer el token de forma segura desde tus archivos de entorno cargados
    token_telegram = os.getenv("8837254965:AAEMzgOybDw7nV_O9otKjloEoOO-mnTI5-g")
    
    if not token_telegram:
        print("ADVERTENCIA CRÍTICA: Variable TELEGRAM_TOKEN no configurada. Servidor web iniciado sin bot.")
        return

    # Inicializa la aplicación del bot sin bloquear el ciclo de FastAPI
    tg_app = Application.builder().token(token_telegram).build()
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_telegram))
    
    await tg_app.initialize()
    await tg_app.start()
    asyncio.create_task(tg_app.updater.start_polling())
