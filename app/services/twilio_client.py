from twilio.rest import Client
from app.core.config import settings

class TwilioClient:
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
    def send_message(self, to: str, body: str):
        message = self.client.messages.create(
            from_=settings.TWILIO_PHONE_NUMBER,
            body=body,
            to=to
        )
        return message.sid

twilio_client = TwilioClient()
