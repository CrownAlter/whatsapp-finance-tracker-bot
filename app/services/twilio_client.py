from twilio.rest import Client
from app.core.config import settings

class TwilioClient:
    """
    Twilio WhatsApp API client wrapper.
    
    Provides simplified interface for sending WhatsApp messages
    through Twilio's programmable messaging API.
    """
    
    def __init__(self):
        """Initialize Twilio client with configured credentials."""
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
    def send_message(self, to: str, body: str):
        """
        Send a WhatsApp message through Twilio.
        
        Args:
            to: Recipient phone number (format: +1234567890)
            body: Message content to send
            
        Returns:
            Message SID for tracking
        """
        message = self.client.messages.create(
            from_=settings.TWILIO_PHONE_NUMBER,
            body=body,
            to=to
        )
        return message.sid

twilio_client = TwilioClient()
