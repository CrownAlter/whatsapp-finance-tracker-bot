from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.db.session import get_db_with_logging
from app.services.message_processor import message_processor
from app.services.finance_engine import finance_engine
from app.services.twilio_client import twilio_client
from app.core.security import validate_twilio_request
from app.core.logging import get_logger
from app.core.monitoring import get_metrics_collector
from twilio.twiml.messaging_response import MessagingResponse
import time
import traceback

logger = get_logger(__name__)
router = APIRouter()

@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    db: Session = Depends(lambda: get_db_with_logging(getattr(request.state, 'request_id', None)))
):
    """
    Receives WhatsApp messages from Twilio with comprehensive logging and error handling.
    """
    request_id = getattr(request.state, 'request_id', 'unknown')
    start_time = time.time()
    
    logger.info(
        "WhatsApp webhook received",
        extra={
            "event_type": "webhook_start",
            "request_id": request_id,
            "from": From,
            "message_length": len(Body) if Body else 0,
            "user_agent": request.headers.get("user-agent")
        }
    )
    
    try:
        # 1. Validate Twilio request (security)
        if not validate_twilio_request(request):
            logger.warning(
                "Invalid Twilio request signature",
                extra={
                    "event_type": "security_violation",
                    "request_id": request_id,
                    "from": From,
                    "client_ip": request.client.host if request.client else None
                }
            )
            raise HTTPException(status_code=403, detail="Invalid request signature")
        
        # 2. Clean phone number (Twilio sends 'whatsapp:+1234567890')
        user_phone = From.replace("whatsapp:", "")
        
        logger.info(
            "Processing WhatsApp message",
            extra={
                "event_type": "message_processing_start",
                "request_id": request_id,
                "user_phone": user_phone,
                "message_preview": Body[:50] + "..." if len(Body) > 50 else Body
            }
        )
        
        # 3. Parse Message with error handling
        try:
            intent, data = message_processor.parse_message(Body)
            logger.info(
                "Message parsed successfully",
                extra={
                    "event_type": "message_parsed",
                    "request_id": request_id,
                    "intent": intent,
                    "data_type": type(data).__name__,
                    "data_summary": str(data)[:100] if data else None
                }
            )
        except Exception as parse_error:
            logger.error(
                f"Message parsing failed: {type(parse_error).__name__}: {str(parse_error)}",
                extra={
                    "event_type": "message_parse_error",
                    "request_id": request_id,
                    "error_type": type(parse_error).__name__,
                    "error_message": str(parse_error),
                    "original_message": Body[:200]
                }
            )
            # Return a helpful error response
            resp = MessagingResponse()
            resp.message("Sorry, I couldn't understand your message. Please try again or type 'help' for assistance.")
            return data_response(content=str(resp), media_type="application/xml")
        
        # 4. Handle Conversation via Manager with error handling
        try:
            from app.services.conversation_manager import conversation_manager
            response_text = conversation_manager.handle_message(db, user_phone, Body, intent, data)
            
            logger.info(
                "Conversation handled successfully",
                extra={
                    "event_type": "conversation_handled",
                    "request_id": request_id,
                    "user_phone": user_phone,
                    "response_length": len(response_text) if response_text else 0,
                    "response_preview": response_text[:50] + "..." if len(response_text) > 50 else response_text
                }
            )
            
        except Exception as conversation_error:
            logger.error(
                f"Conversation handling failed: {type(conversation_error).__name__}: {str(conversation_error)}",
                extra={
                    "event_type": "conversation_error",
                    "request_id": request_id,
                    "user_phone": user_phone,
                    "error_type": type(conversation_error).__name__,
                    "error_message": str(conversation_error),
                    "intent": intent
                }
            )
            # Return a generic error response
            resp = MessagingResponse()
            resp.message("Sorry, I encountered an error processing your request. Please try again later.")
            return data_response(content=str(resp), media_type="application/xml")
        
        # 5. Send Response (Twilio expects TwiML)
        try:
            resp = MessagingResponse()
            resp.message(response_text)
            
            process_time = time.time() - start_time
            
            logger.info(
                "WhatsApp webhook completed successfully",
                extra={
                    "event_type": "webhook_complete",
                    "request_id": request_id,
                    "user_phone": user_phone,
                    "process_time_seconds": process_time,
                    "response_length": len(response_text) if response_text else 0
                }
            )
            
            # Record metrics
            metrics = get_metrics_collector()
            metrics.record_request(
                method=request.method,
                path=str(request.url.path),
                status_code=200,
                duration=process_time
            )
            
            return data_response(content=str(resp), media_type="application/xml")
            
        except Exception as response_error:
            logger.error(
                f"Response generation failed: {type(response_error).__name__}: {str(response_error)}",
                extra={
                    "event_type": "response_error",
                    "request_id": request_id,
                    "user_phone": user_phone,
                    "error_type": type(response_error).__name__,
                    "error_message": str(response_error)
                }
            )
            raise HTTPException(status_code=500, detail="Failed to generate response")
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as webhook_error:
        process_time = time.time() - start_time
        logger.error(
            f"WhatsApp webhook failed: {type(webhook_error).__name__}: {str(webhook_error)}",
            extra={
                "event_type": "webhook_error",
                "request_id": request_id,
                "user_phone": From.replace("whatsapp:", "") if From else None,
                "error_type": type(webhook_error).__name__,
                "error_message": str(webhook_error),
                "traceback": traceback.format_exc(),
                "process_time_seconds": process_time
            }
        )
        
        # Record error metrics
        metrics = get_metrics_collector()
        metrics.record_request(
            method=request.method,
            path=str(request.url.path),
            status_code=500,
            duration=process_time
        )
        
        # Return a minimal error response
        resp = MessagingResponse()
        resp.message("Sorry, an error occurred. Please try again later.")
        return data_response(content=str(resp), media_type="application/xml")


def data_response(content: str, media_type: str = "application/xml"):
    """Return XML response for Twilio webhook."""
    return Response(content=content, media_type=media_type)


@router.post("/verify/message")
async def verify_message(
    request: Request,
    message: str = Form(...),
    phone: str = Form("1234567890"),
    db: Session = Depends(lambda: get_db_with_logging(getattr(request.state, 'request_id', None)))
):
    """
    Endpoint for testing message processing without Twilio/Ngrok.
    Enhanced with comprehensive logging and error handling.
    """
    request_id = getattr(request.state, 'request_id', 'unknown')
    start_time = time.time()
    
    logger.info(
        "Message verification endpoint called",
        extra={
            "event_type": "verify_start",
            "request_id": request_id,
            "phone": phone,
            "message_length": len(message) if message else 0,
            "message_preview": message[:50] + "..." if len(message) > 50 else message
        }
    )
    
    try:
        from app.services.conversation_manager import conversation_manager
        from app.services.message_processor import message_processor
        
        # Parse message with error handling
        try:
            intent, data = message_processor.parse_message(message)
        except Exception as parse_error:
            logger.error(
                f"Test message parsing failed: {type(parse_error).__name__}: {str(parse_error)}",
                extra={
                    "event_type": "verify_parse_error",
                    "request_id": request_id,
                    "error_type": type(parse_error).__name__,
                    "error_message": str(parse_error)
                }
            )
            raise HTTPException(status_code=400, detail=f"Message parsing failed: {str(parse_error)}")
        
        # Handle conversation with error handling
        try:
            response = conversation_manager.handle_message(db, phone, message, intent, data)
        except Exception as conversation_error:
            logger.error(
                f"Test conversation handling failed: {type(conversation_error).__name__}: {str(conversation_error)}",
                extra={
                    "event_type": "verify_conversation_error",
                    "request_id": request_id,
                    "error_type": type(conversation_error).__name__,
                    "error_message": str(conversation_error)
                }
            )
            raise HTTPException(status_code=500, detail=f"Conversation handling failed: {str(conversation_error)}")
        
        process_time = time.time() - start_time
        
        logger.info(
            "Message verification completed successfully",
            extra={
                "event_type": "verify_complete",
                "request_id": request_id,
                "phone": phone,
                "intent": intent,
                "response_length": len(response) if response else 0,
                "process_time_seconds": process_time
            }
        )
        
        # Record metrics
        metrics = get_metrics_collector()
        metrics.record_request(
            method=request.method,
            path=str(request.url.path),
            status_code=200,
            duration=process_time
        )
        
        return {
            "response": response,
            "intent": intent,
            "data": str(data),
            "request_id": request_id,
            "process_time_seconds": process_time
        }
    
    except HTTPException:
        raise
    
    except Exception as verify_error:
        process_time = time.time() - start_time
        logger.error(
            f"Message verification failed: {type(verify_error).__name__}: {str(verify_error)}",
            extra={
                "event_type": "verify_error",
                "request_id": request_id,
                "error_type": type(verify_error).__name__,
                "error_message": str(verify_error),
                "traceback": traceback.format_exc(),
                "process_time_seconds": process_time
            }
        )
        
        # Record error metrics
        metrics = get_metrics_collector()
        metrics.record_request(
            method=request.method,
            path=str(request.url.path),
            status_code=500,
            duration=process_time
        )
        
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(verify_error)}")
