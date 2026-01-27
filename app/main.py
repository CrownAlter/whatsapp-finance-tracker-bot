from fastapi import FastAPI, Request
from app.api.api import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from twilio.twiml.messaging_response import MessagingResponse

# Create tables on startup (for simple apps/dev)
# In production, use Alembic migrations
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    incoming_msg = form.get("Body")
    sender = form.get("From")

    response = MessagingResponse()
    msg = response.message()

    msg.body(f"You said: {incoming_msg}")

    return str(response)