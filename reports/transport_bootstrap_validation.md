# Transport Bootstrap Validation

## Uniform Execution
Because Pipecat abstracts the transport layer into `PipecatTransportAdapter`, the underlying `Twilio` and `LiveKit` implementations required **zero** custom code modifications to support the greeting bootstrap. 

## Twilio Verification
- Webhooks establish the media stream WebSocket.
- The `TwilioFrameSerializer` decodes the start frame.
- Pipecat runner receives `StartFrame` and pushes the LLM greeting.
- Twilio correctly plays the synthesized AI greeting before waiting for VAD inputs.

## LiveKit Verification
- LiveKit Room establishes `rtc` connection.
- `LiveKitTransport` handles `on_participant_connected`.
- Standard `PipecatAdapter.run()` invokes the exact same greeting logic queue.
- LiveKit participant hears the greeting before STT actively listens.

Conclusion: Independence from transports is strictly maintained as per Pillar 2 architectures.
