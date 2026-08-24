"""DTOs del webhook de Evolution API (WhatsApp)."""
from pydantic import BaseModel, ConfigDict


class MessageKey(BaseModel):
    model_config = ConfigDict(extra="ignore")

    remote_jid: str = ""
    id: str = ""

    @classmethod
    def from_payload(cls, payload: dict) -> "MessageKey":
        key = payload.get("key", {}) or {}
        return cls(remote_jid=key.get("remoteJid", ""), id=key.get("id", ""))


class IncomingMessage(BaseModel):
    """Vista mínima de un mensaje entrante del webhook messages-upsert."""

    model_config = ConfigDict(extra="ignore")

    key: MessageKey
    message_type: str
    text: str | None

    @classmethod
    def from_webhook(cls, body: dict) -> "IncomingMessage":
        data = body.get("data", {}) or {}
        message = data.get("message", {}) or {}
        return cls(
            key=MessageKey.from_payload(data),
            message_type=data.get("messageType", ""),
            text=message.get("conversation"),
        )

    @property
    def is_audio(self) -> bool:
        return self.message_type == "audioMessage"

    @property
    def phone_number(self) -> str:
        """Extrae el teléfono del remitente desde el remoteJid."""
        return self.key.remote_jid.split("@")[0].split(":")[0]

    @property
    def is_individual_chat(self) -> bool:
        return self.key.remote_jid.endswith("@s.whatsapp.net")
