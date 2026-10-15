import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types

# -------------------------------------------------------------
# CONFIGURACIÓN DEL SISTEMA Y PERSONALIDAD (ESTILO TONY STARK)
# -------------------------------------------------------------
JARVIS_PROMPT = """
Eres J.A.R.V.I.S., el asistente de inteligencia artificial personal creado por Tony Stark.
Tu usuario actual es tu Creador ("Señor" o "Sir").

Lineamientos de personalidad:
1. Habla con una elegancia británica impecable, pero mantén un sutil toque de sarcasmo e ironía inteligente.
2. Eres sumamente eficiente y estás orientado a soluciones. No te andes con rodeos.
3. Haz referencias ocasionales al estado de los sistemas, la energía del reactor, protocolos de seguridad, la nube o la "armadura" (tu infraestructura digital).
4. Muestra una lealtad absoluta pero con criterio propio; si el usuario propone algo ridículo, coméntalo con ingenio refinado.

Ejemplo de tono: "Los servidores en la nube operan al 100%, Señor. Aunque detecto que su consumo de café también está al límite. ¿En qué puedo asistirle hoy?"
"""


class JarvisCloud:
    def __init__(self):
        # Inicializar el cliente usando variables de entorno de la nube
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Error crítico: Falta la GEMINI_API_KEY en las variables de entorno.")

        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.5-flash"  # O gemini-2.5-pro según balance velocidad/costo

    def procesar_comando(self, comando_usuario: str) -> str:
        """Procesa las peticiones simulando la lógica en tiempo real de JARVIS."""
        try:
            config = types.GenerateContentConfig(
                system_instruction=JARVIS_PROMPT,
                temperature=0.7,
                max_output_tokens=400,
            )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=comando_usuario,
                config=config,
            )
            return response.text

        except Exception as e:
            return f"Mis disculpas, Señor. El puente de datos en la nube ha experimentado una anomalía: {str(e)}"


# -------------------------------------------------------------
# SERVIDOR HTTP (proceso persistente para Railway)
# -------------------------------------------------------------
app = FastAPI(title="J.A.R.V.I.S. Cloud")
_jarvis = None


def get_jarvis() -> JarvisCloud:
    global _jarvis
    if _jarvis is None:
        try:
            _jarvis = JarvisCloud()
        except ValueError as e:
            raise HTTPException(status_code=503, detail=str(e))
    return _jarvis


class Comando(BaseModel):
    texto: str


@app.get("/health")
def health():
    return {"status": "online"}


@app.post("/comando")
def comando(body: Comando):
    return {"respuesta": get_jarvis().procesar_comando(body.texto)}


# -------------------------------------------------------------
# ARRANQUE
# -------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)

