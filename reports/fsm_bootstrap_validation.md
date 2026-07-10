# FSM Bootstrap Validation

## Context
The `ConversationStateMachine` enforces rigorous constraints over which states the pipeline can legally enter, preventing concurrency glitches (e.g., trying to generate audio while currently playing audio).

## Changes Made
To accommodate an AI-initiated greeting, the FSM mapping was explicitly patched:
- `LISTENING` -> `THINKING` is now explicitly allowed. Normally, `THINKING` requires a prior `TRANSCRIBING` state (since STT leads to LLM generation). Because the assistant originates the greeting *without* an STT transcript, it must leap straight to `THINKING`.
- `THINKING` -> `GENERATING_AUDIO` is permitted if intermediate token tracing is not captured or if `GENERATING_RESPONSE` is skipped in rapid deployments.

## Validated State Pathway
```
[IDLE] 
  -> [LISTENING] (Transport connection established)
  -> [THINKING] (LLMMessagesAppendFrame triggers LLM)
  -> [GENERATING_RESPONSE] (LLM begins token generation)
  -> [GENERATING_AUDIO] (Sentence completed, TTS triggered)
  -> [SPEAKING] (Audio begins playing to the user)
  -> [LISTENING] (Greeting completed, VAD unmuted)
```
This pathway proved completely stable during test runs, and regression tests successfully pass with the extended transitions.
