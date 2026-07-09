# Barge-in Validation

**Status:** BLOCKED BY EXTERNAL DEPENDENCY

Voice Activity Detection (VAD) requires continuous PCM audio streams. Without a real Twilio Media Stream injecting `UserStartedSpeakingFrame`, the interrupt signal and `InterruptionFrame` lifecycle cannot be proven in a runtime context.
