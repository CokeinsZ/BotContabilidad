import os

import httpx
from dotenv import load_dotenv

class WhatsAppService:
    def __init__(self):
        load_dotenv()
        self.base_url = os.getenv("EVOLUTION_API_BASE_URL")
        self.instance_name = os.getenv("EVOLUTION_API_INSTANCE_NAME")
        self.token = os.getenv("EVOLUTION_API_TOKEN")
        self.client = httpx.AsyncClient()