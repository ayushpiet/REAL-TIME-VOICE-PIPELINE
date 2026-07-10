# Event Bootstrap Trace

## Telemetry
The implementation introduced the following strictly typed events into `app/events/event_types.py`:
- `AssistantGreetingStarted`
- `AssistantGreetingGenerated`
- `AssistantGreetingTTSStarted`
- `AssistantGreetingCompleted`
- `ConversationReady`

## Trace Capture
When `ENABLE_INITIAL_GREETING` is true, the `PipecatEventBridge` monitors state to ensure these events fire identically to, but distinguishably from, normal conversational turns. 

### Trace Sequence:
1. **Pipeline initialization:** The adapter instantly dispatches `AssistantGreetingStarted` during queue setup.
2. **LLM execution:** `GroqLLMService` interprets the internal prompt and `PipecatEventBridge.on_llm_response_ready` intercepts the generation payload to emit `AssistantGreetingGenerated`.
3. **TTS mapping:** `ElevenLabsTTSService` fires audio frames and the bridge maps `on_audio_started` to `AssistantGreetingTTSStarted`.
4. **Completion:** When TTS stops speaking, the bridge concludes the sequence by emitting `AssistantGreetingCompleted` followed synchronously by `ConversationReady`. At this precise moment, VAD un-mutes and the user can speak.
