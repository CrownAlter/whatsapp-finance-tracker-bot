# Ngrok Setup Guide for Finance Tracker Bot

## Prerequisites
- ✅ Ngrok installed
- ✅ FastAPI application ready
- 🔑 Ngrok auth token (get from https://dashboard.ngrok.com/get-started/your-authtoken)

## Step 1: Authenticate Ngrok (First Time Only)

If you haven't authenticated ngrok yet, run:

```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
```

Get your auth token from: https://dashboard.ngrok.com/get-started/your-authtoken

## Step 2: Start Your FastAPI Server

In your first terminal (with virtual environment activated):

```bash
uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

## Step 3: Start Ngrok Tunnel

In a **second terminal**, run:

```bash
ngrok http 8000
```

You'll see output like:

```
Session Status                online
Account                       your-account
Version                       3.20.0
Region                        United States (us)
Forwarding                    https://xxxx-xx-xx-xx-xx.ngrok-free.app -> http://localhost:8000
```

**Copy the `https://` URL** - this is your public webhook URL!

## Step 4: Configure Twilio Webhook

1. Go to Twilio Console: https://console.twilio.com/
2. Navigate to: **Messaging** → **Try it out** → **Send a WhatsApp message**
3. In the **Sandbox Settings**, find the **"When a message comes in"** webhook field
4. Enter your ngrok URL + webhook endpoint:
   ```
   https://YOUR-NGROK-URL.ngrok-free.app/api/v1/webhook
   ```
5. Set HTTP method to **POST**
6. Click **Save**

## Step 5: Test Your Bot

1. Join your WhatsApp Sandbox by sending the code shown in Twilio Console to the sandbox number
2. Send test messages:
   - `Spent 100 on food`
   - `Income 5000 salary`
   - `Show report`

## Troubleshooting

### Ngrok Authentication Required
If you see "authentication required", run:
```bash
ngrok config add-authtoken YOUR_TOKEN
```

### Port Already in Use
If port 8000 is busy, use a different port:
```bash
uvicorn app.main:app --reload --port 8001
ngrok http 8001
```

### Webhook Not Receiving Messages
- Check ngrok is running and showing "online"
- Verify the Twilio webhook URL includes `/api/v1/webhook`
- Check FastAPI logs for incoming requests
- Ensure your `.env` has correct Twilio credentials

## Keeping Ngrok Running

> **Note**: Free ngrok URLs change every time you restart ngrok. For a permanent URL, consider:
> - Ngrok paid plan (reserved domains)
> - Deploy to a cloud service (Render, Railway, Heroku)

## Quick Reference Commands

```bash
# Terminal 1: Start FastAPI
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start Ngrok
ngrok http 8000

# View ngrok web interface (shows request logs)
# Open in browser: http://127.0.0.1:4040
```
