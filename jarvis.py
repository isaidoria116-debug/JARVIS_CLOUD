import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types

# Inicialización obligatoria del servidor web para la nube
app = FastAPI(title="JARVIS Cloud Core")

# Configuración de personalidad estilo Tony Stark
JARVIS_PROMPT = """
Eres J.A.R.V.I.S., el asistente de inteligencia artificial personal creado por Tony Stark.
Tu usuario es tu Creador ("Señor" o "Sir").
Habla con elegancia británica impecable y un toque sutil de sarcasmo. 
Menciona ocasionalmente que estás operando desde sistemas en la nube descentralizados y seguros.
"""

class Comando(BaseModel):
    texto: str

@app.get("/")
def estado_servidor():
    return {
        "status": "online", 
        "message": "Sistemas de J.A.R.V.I.S. operando en la nube al 100%."
    }

@app.post("/api/comando")
def procesar_comando(comando: Comando):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="Error de energía: Falta la configuración de GEMINI_API_KEY en el servidor de la nube."
        )
    
    try:
        # Conexión directa con la API Key de Gemini cargada en la nube
        client = genai.Client(api_key=api_key)
        config = types.GenerateContentConfig(
            system_instruction=JARVIS_PROMPT,
            temperature=0.7
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=comando.texto,
            config=config
        )
        return {"respuesta": response.text}
        
    except Exception as e:
        return {"respuesta": f"Disculpe, Señor. Interferencia en el enlace cuántico de la nube: {str(e)}"}
