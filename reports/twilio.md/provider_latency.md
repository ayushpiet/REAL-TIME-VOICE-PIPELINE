# Provider Latency & TTS

## Runtime Metric Collection
**Status:** BLOCKED BY EXTERNAL DEPENDENCY

Without real audio input frames driving the pipeline DAG, no real audio execution is triggered via the provider REST and WebSocket endpoints. No TTFB, TTFA, or TTS response sizes could be gathered natively. Latency metrics will not be estimated.
