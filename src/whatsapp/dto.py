"""DTOs del webhook de Evolution API (WhatsApp)."""
from pydantic import BaseModel, ConfigDict


class MessageKey(BaseModel):
    model_config = ConfigDict(extra="ignore")

    remote_jid: str = ""
    id: str = ""
    from_me: bool = False
    sender_pn: str = ""

    @classmethod
    def from_payload(cls, payload: dict) -> "MessageKey":
        key = payload.get("key", {}) or {}
        return cls(
            remote_jid=key.get("remoteJid", ""),
            id=key.get("id", ""),
            from_me=bool(key.get("fromMe", False)),
            # Evolution entrega el teléfono real aquí cuando el remoteJid
            # es un @lid (nuevo identificador privado de WhatsApp).
            sender_pn=key.get("senderPn", "") or "",
        )


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

        # Texto plano simple llega en `conversation`; con formato, emojis o
        # desde WhatsApp Web llega en `extendedTextMessage.text`.
        text = message.get("conversation")
        if not text:
            text = (message.get("extendedTextMessage") or {}).get("text")

        return cls(
            key=MessageKey.from_payload(data),
            message_type=data.get("messageType", ""),
            text=text,
        )

    @property
    def is_audio(self) -> bool:
        return self.message_type == "audioMessage"

    @property
    def phone_number(self) -> str:
        """Teléfono del remitente (solo dígitos).

        Prioriza `senderPn` (disponible cuando el remoteJid es @lid);
        de lo contrario lo extrae del remoteJid.
        """
        raw = self.key.sender_pn or self.key.remote_jid
        return "".join(filter(str.isdigit, raw.split("@")[0].split(":")[0]))

    @property
    def is_individual_chat(self) -> bool:
        """Solo chats individuales (no grupos, estados ni canales)."""
        return self.key.remote_jid.endswith(("@s.whatsapp.net", "@lid"))

    @property
    def ignore_reason(self) -> str | None:
        """Razón por la que el mensaje debe ignorarse, o None si procesa."""
        if self.key.from_me:
            return "mensaje propio (fromMe)"
        if not self.is_individual_chat:
            return f"no es chat individual (remoteJid={self.key.remote_jid})"
        if not self.is_audio and not self.text:
            return f"sin texto extraíble (messageType={self.message_type})"
        if self.is_audio and not self.key.id:
            return "audio sin id de mensaje"
        return None
