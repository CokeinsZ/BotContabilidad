"""
Configuración centralizada del proyecto.

Este módulo carga las variables de entorno una sola vez al importarse
y las expone como constantes accesibles desde cualquier parte del proyecto.
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno una sola vez al importar el módulo
load_dotenv()

# Evolution API - WhatsApp
EVOLUTION_API_BASE_URL = os.getenv("EVOLUTION_API_BASE_URL", "http://evolution-api:8080")
EVOLUTION_API_INSTANCE_NAME = os.getenv("EVOLUTION_API_INSTANCE_NAME", "")
EVOLUTION_API_TOKEN = os.getenv("EVOLUTION_API_TOKEN", "")

# Ollama AI
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")

# Whisper
WHISPER_URL = os.getenv("WHISPER_URL", "")

# Google Drive - IDs de carpetas y templates
MASTER_FOLDER_ID = os.getenv("MASTER_FOLDER_ID", "")
PLANILLA_SHEETS_FOLDER_ID = os.getenv("PLANILLA_SHEETS_FOLDER_ID", "")
PLANILLA_TEMPLATE_ID = os.getenv("PLANILLA_TEMPLATE_ID", "")

ADMIN_NAME="Dairo Carvajal"
