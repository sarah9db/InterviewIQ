from __future__ import annotations

from twilio.rest import Client

from interview_agents.config.settings import settings


class TwilioSMSClient:
    def __init__(self) -> None:
        self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

    def send(self, body: str) -> str:
        to, from_ = self._destination_pair()
        message = self.client.messages.create(
            to=to,
            from_=from_,
            body=body,
        )
        return message.sid

    @staticmethod
    def _destination_pair() -> tuple[str, str]:
        # Prefer WhatsApp when explicit WhatsApp numbers are configured.
        if settings.twilio_whatsapp_from and settings.twilio_whatsapp_to:
            return (
                TwilioSMSClient._ensure_whatsapp_prefix(settings.twilio_whatsapp_to),
                TwilioSMSClient._ensure_whatsapp_prefix(settings.twilio_whatsapp_from),
            )

        if settings.twilio_from_number and settings.twilio_to_number:
            return settings.twilio_to_number, settings.twilio_from_number

        raise ValueError(
            "Twilio destination not configured. Set TWILIO_WHATSAPP_FROM/TWILIO_WHATSAPP_TO "
            "for WhatsApp, or TWILIO_FROM_NUMBER/TWILIO_TO_NUMBER for SMS."
        )

    @staticmethod
    def _ensure_whatsapp_prefix(number: str) -> str:
        normalized = number.strip()
        if normalized.startswith("whatsapp:"):
            return normalized
        return f"whatsapp:{normalized}"
