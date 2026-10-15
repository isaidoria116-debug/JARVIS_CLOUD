import os
import time
from google import genai  # O tu proveedor de preferencia (OpenAI/Anthropic)
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
                max_output_tokens=400
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=comando_usuario,
                config=config
            )
            return response.text
            
        except Exception as e:
            return f"Mis disculpas, Señor. El puente de datos en la nube ha experimentado una anomalía: {str(e)}"

# -------------------------------------------------------------
# EJECUCIÓN (Para pruebas locales antes del despliegue en la nube)
# -------------------------------------------------------------
if __name__ == "__main__":
    # Simulación de arranque de sistemas
    print("[SYSTEM] Inicializando protocolos J.A.R.V.I.S. Cloud v2.6...")
    time.sleep(1)
    
    # Asegúrate de configurar export GEMINI_API_KEY="tu_clave" en tu terminal
    try:
        jarvis = JarvisCloud()
        print("[JARVIS]: Conexión satelital establecida de manera segura.\n")
        
        # Simulación de comandos del usuario
        test_prompt = "¿Cómo están los sistemas y qué planes tenemos para hoy?"
        print(f"Usuario: {test_prompt}")
        
        respuesta = jarvis.procesar_comando(test_prompt)
        print(f"JARVIS: {respuesta}")
        
    except ValueError as e:
        print(e)