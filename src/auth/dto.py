"""DTOs de las respuestas del módulo de autenticación."""
from pydantic import BaseModel


class AuthStatusResponse(BaseModel):
    authenticated: bool
    message: str


class MessageResponse(BaseModel):
    status: str
    message: str
