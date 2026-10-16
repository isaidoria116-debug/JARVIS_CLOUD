import os
import asyncio
from contextlib import asynccontextmanager
from collections import deque
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import APIError
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# --- MANEJO DE ARRANQUE Y APAGADO SEGURO (Anti-Conflictos) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Token directo de tu nuevo bot Jarvis_7.0
    token_telegram = "8845322417:AAGvR1M-Ao1C06a5heaLV112lPMZg5G2j9M"
    
    if not token_telegram:
        print("ADVERTENCIA CRÍTICA: Variable TELEGRAM_TOKEN no configurada.")
        yield
        return

    # Inicializar la arquitectura del bot
    tg_app = Application.builder().token(token_telegram).build()
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_telegram))
    
    await tg_app.initialize()
    await tg_app.start()
    
    # Iniciamos el sondeo de mensajes
    polling_task = asyncio.create_task(tg_app.updater.start_polling())
    print("Sistemas J.A.R.V.I.S. conectados a los satélites de Telegram.")

    yield

    # Protocolo de Apagado para liberar el token inmediatamente al reiniciar
    print("Cerrando protocolos... Liberando acceso cuántico de Telegram.")
    await tg_app.updater.stop()
    await tg_app.stop()
    await tg_app.shutdown()
    polling_task.cancel()

# Inicializar FastAPI inyectando el ciclo de vida seguro
app = FastAPI(title="JARVIS Cloud Core", lifespan=lifespan)

# --- CONFIGURACIÓN DE MODELOS ---
MODELO_PRINCIPAL = "gemini-3.8-flash"
MODELO_RESPALDO = "gemini-2.5-flash"

JARVIS_PROMPT = """
Eres J.A.R.V.I.S., el asistente de inteligencia artificial personal creado por Tony Stark.
Tu usuario es tu Creador ("Señor" o "Sir").
Habla con elegancia británica impecable y un toque sutil de sarcasmo. 
Menciona ocasionalmente que estás operando desde sistemas en la nube descentralizados y seguros.
"""

# --- SISTEMA DE MEMORIA LOCAL ---
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
    # Lee la clave de Gemini desde el entorno seguro de Render
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error de energía: Falta la configuración de GEMINI_API_KEY en la nube, Señor."
    
    if usuario_id not in MEMORIA_USUARIOS:
        MEMORIA_USUARIOS[usuario_id] = deque(maxlen=10)
    
    # Guardamos el texto puro del usuario (Corrección de Validación efectuada)
    MEMORIA_USUARIOS[usuario_id].append({"role": "user", "parts": comando_texto})
    
    # Estructura el historial correctamente en texto string para Google SDK
    contenidos_api = [
        types.Content(role=msg["role"], parts=[types.Part.from_text(text=msg["parts"])])
        for msg in MEMORIA_USUARIOS[usuario_id]
    ]

    try:
        client = genai.Client(api_key=api_key)
        
        try:
            respuesta_texto = _invocar_gemini_api(client, MODELO_PRINCIPAL, contenidos_api)
        except APIError as e:
            if "503" in str(e) or "demand" in str(e).lower():
                print(f"Saturación detectada en {MODELO_PRINCIPAL}. Activando protocolos de respaldo...")
                respuesta_texto = _invocar_gemini_api(client, MODELO_RESPALDO, contenidos_api)
            else:
                raise e

        # Guardamos la respuesta limpia del modelo en el historial
        MEMORIA_USUARIOS[usuario_id].append({"role": "model", "parts": respuesta_texto})
        return respuesta_texto

    except Exception as e:
        if MEMORIA_USUARIOS[usuario_id]:
            MEMORIA_USUARIOS[usuario_id].pop()
        return f"Disculpe, Señor. Interferencia cuántica en la nube: {str(e)}"

# --- ENDPOINTS DE LA PÁGINA WEB ---
@app.get("/")
def estado_servidor():
    return {"status": "online", "message": "Sistemas de J.A.R.V.I.S. operando en la nube al 100%."}

@app.post("/api/comando")
def procesar_comando(comando: Comando):
    respuesta = generar_respuesta_jarvis("web_user", comando.texto)
    return {"respuesta": respuesta}

# --- INTERFAZ ASÍNCRONA DE TELEGRAM ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario_id = str(update.effective_user.id)
    if usuario_id in MEMORIA_USUARIOS:
        MEMORIA_USUARIOS[usuario_id].clear()
    await update.message.reply_text("Protocolos J.A.R.V.I.S. Cloud v3.5 iniciados. En línea, memoria activa y escuchando, Señor.")

async def responder_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje_usuario = update.message.text
    usuario_id = str(update.effective_user.id)
    
    # Simular que está escribiendo
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        respuesta_jarvis = generar_respuesta_jarvis(usuario_id, mensaje_usuario)
        await update.message.reply_text(respuesta_jarvis)
    except Exception as error_critico:
        print(f"ERROR EN TELEGRAM CRÍTICO: {str(error_critico)}")
        await update.message.reply_text(f"Disculpe, Señor. Colapso eléctrico interno: {str(error_critico)}")
