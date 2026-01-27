from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.message_processor import message_processor
from app.services.finance_engine import finance_engine
from app.services.twilio_client import twilio_client
from app.core.security import validate_twilio_request
from twilio.twiml.messaging_response import MessagingResponse

router = APIRouter()

@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Receives WhatsApp messages from Twilio.
    """
    # 1. Clean phone number (Twilio sends 'whatsapp:+1234567890')
    user_phone = From.replace("whatsapp:", "")
    
    # 2. Parse Message
    intent, data = message_processor.parse_message(Body)
    
    # 3. Handle Conversation via Manager
    from app.services.conversation_manager import conversation_manager
    response_text = conversation_manager.handle_message(db, user_phone, Body, intent, data)
    
    # 4. Send Response (Twilio expects TwiML)
    resp = MessagingResponse()
    resp.message(response_text)
    
# Return XML response
    return data_response(content=str(resp), media_type="application/xml")

# Helper to return XML
def data_response(content: str, media_type: str = "application/xml"):
    """Return XML response for Twilio webhook."""
    return Response(content=content, media_type=media_type)

@router.post("/verify/message")
async def verify_message(
    message: str = Form(...),
    phone: str = Form("1234567890"),
    db: Session = Depends(get_db)
):
    """
    Endpoint for testing message processing without Twilio/Ngrok.
    """
    from app.services.conversation_manager import conversation_manager
    from app.services.message_processor import message_processor
    
    intent, data = message_processor.parse_message(message)
    response = conversation_manager.handle_message(db, phone, message, intent, data)
    
    return {"response": response, "intent": intent, "data": str(data)}
