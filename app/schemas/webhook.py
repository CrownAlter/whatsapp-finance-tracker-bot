from pydantic import BaseModel, ConfigDict
from copy import deepcopy

# Twilio sends data as form-encoded, but for Pydantic processing manually or via some helper, 
# we often represent it. 
# However, FastAPI's Request object is usually better for Form data.
# This schema might be used if we convert the form data to a dict.

class TwilioWebhook(BaseModel):
    MessageSid: str | None = None
    SmsSid: str | None = None
    AccountSid: str | None = None
    MessagingServiceSid: str | None = None
    From: str
    To: str
    Body: str
    NumMedia: int | None = 0
    
    model_config = ConfigDict(extra='ignore')
