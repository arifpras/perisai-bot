# WhatsApp Integration Guide

Use this guide to add WhatsApp as a channel for the bond price/yield personas (Kei/Kin/Both) alongside the existing FastAPI `/chat` flow.

## 1) Choose a provider
- **Meta WhatsApp Cloud API (recommended):** Free sandbox, direct Meta hosting, needs a WhatsApp-capable number not registered in the consumer/business app. Requires webhook verify token + app secret for signatures.
- **Twilio WhatsApp:** Uses a Twilio WhatsApp-enabled number. Easier setup if you already use Twilio; otherwise you must migrate or buy a Twilio number.

## 2) Prerequisites
- FastAPI app running (the `/chat` endpoint already produces `text`, `analysis`, and `image_base64`).
- Public HTTPS URL for webhooks (ngrok/Cloudflare Tunnel for local; Render/Heroku/etc. for prod).
- Python env loaded with project deps (`pip install -r requirements.txt`).

## 3) Environment variables
Set via `.env` or platform config. Suggested keys:

Common
- `WA_PROVIDER` = `meta` | `twilio`
- `API_BASE_URL` = FastAPI base (e.g., `http://127.0.0.1:8000`)

Meta (Cloud API)
- `WA_ACCESS_TOKEN` = permanent token or short-lived user token
- `WA_PHONE_NUMBER_ID` = phone number ID from WhatsApp Manager
- `WA_VERIFY_TOKEN` = your chosen webhook verify string (used on GET verify)
- `WA_APP_SECRET` = app secret for `X-Hub-Signature-256` verification (recommended)

Twilio
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_FROM` = `whatsapp:+1XXXXXXXXXX` (Twilio sender)
- `TWILIO_WHATSAPP_TO` (optional default recipient for tests)

## 4) Webhook endpoints (to add in FastAPI)
- `GET /whatsapp/webhook` (Meta only): echo back `hub.challenge` when `hub.verify_token` matches `WA_VERIFY_TOKEN`.
- `POST /whatsapp/webhook`: receive messages. For Meta, verify `X-Hub-Signature-256` using `WA_APP_SECRET`; for Twilio, verify `X-Twilio-Signature` using `TWILIO_AUTH_TOKEN`.
- Parse inbound text, map persona (Kei/Kin/Both, or default), detect plot keywords, and call `/chat` for plot flows. Send back text and optional image.

## 5) Sending messages

Meta
- Endpoint: `https://graph.facebook.com/v18.0/{WA_PHONE_NUMBER_ID}/messages`
- Auth: Bearer `WA_ACCESS_TOKEN`
- Payloads:
  - Text: `{ "messaging_product": "whatsapp", "to": "<user_phone>", "type": "text", "text": { "body": "..." } }`
  - Image: upload via media API or send `image` with `link` to a CDN/temporary URL. If using base64 from `/chat`, host or use data URL via Twilio only.

Twilio
- Endpoint: `https://api.twilio.com/2010-04-01/Accounts/{SID}/Messages.json`
- Auth: Basic (SID + Auth Token)
- Payload: `From=whatsapp:+1...&To=whatsapp:+...&Body=...` and `MediaUrl` for images (host the PNG and pass the URL).

## 6) Local testing (Meta example)
1) Run FastAPI: `uvicorn app_fastapi:app --reload --port 8000`
2) Expose: `ngrok http 8000` → note the `https` URL.
3) In WhatsApp Manager, set webhook callback to `https://<ngrok>/whatsapp/webhook`, verify with `WA_VERIFY_TOKEN`, subscribe to messages.
4) Send a WA message to your configured number; watch server logs for webhook hits.

## 7) Persona routing suggestions
- Default persona: Kei. Allow prefixes like `kei:`, `kin:`, `both:` to switch.
- Plot detection: keywords `["plot", "chart", "graph", "show", "visualize"]` → call `/chat` with `plot=True` and return `text` + `image_base64` (host image or upload before sending).
- Non-plot: call persona handlers (`ask_kei`, `ask_kin`, `ask_kei_then_kin`) and send the text result.

## 8) Deployment notes
- Keep `WA_ACCESS_TOKEN` or Twilio auth secret; rotate periodically.
- For Meta, long-lived access tokens are preferred; reissue before expiry.
- Ensure HTTPS endpoint is stable; update webhook URL after redeploys if it changes.
- Add health check (e.g., `/healthz`) for your platform and configure autoscaling probes.

## 9) Next steps to implement
- Add the FastAPI webhook routes and signature verification.
- Implement provider-specific send helpers (text + image via hosted URL).
- Wire persona routing and plot keyword detection for WA messages.
- Document `.env.example` entries and update main README with a short WA section.
