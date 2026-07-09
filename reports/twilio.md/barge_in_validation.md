# Barge-in Validation

## Interruption Execution
**Status:** BLOCKED BY EXTERNAL DEPENDENCY

Simultaneously speaking over the TTS requires continuous VAD detection over Twilio's audio stream. Without physical testing of audio cancellation buffers, barge-in is fully blocked and untested in the wild.
