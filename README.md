# REAL-TIME-VOICE-PIPELINE

## Transport Architecture

The real-time voice pipeline uses a Dual-Transport architecture to support both browser-based testing and production telephony:

- **Development Transport** → **LiveKit**: WebRTC transport used as the default for browser interaction and low-latency audio testing (`TRANSPORT_MODE=livekit`).
- **Production Transport** → **Twilio**: Telephony transport operating via FastAPI WebSockets for real phone calls (`TRANSPORT_MODE=twilio`).

## Configuration

Set the environment variable `TRANSPORT_MODE` in your `.env` file to select the active transport. 

For LiveKit:
```env
TRANSPORT_MODE=livekit
LIVEKIT_URL=wss://your-livekit-server.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
```

For Twilio:
```env
TRANSPORT_MODE=twilio
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
```

Run the application:
```bash
python -m app.main
```
