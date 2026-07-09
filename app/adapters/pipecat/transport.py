"""
Transport abstractions for Pipecat.

Contains:
- PipecatTransportAdapter  — abstract base class
- LiveKitTransportAdapter  — concrete implementation using LiveKit WebRTC
- MockWebSocketTransport   — mock for testing
- MockWebRTCTransport      — mock for testing
"""

import abc
from typing import Any


class PipecatTransportAdapter(abc.ABC):
    """Abstract interface for wrapping a Pipecat Transport."""

    @abc.abstractmethod
    def get_pipecat_transport(self) -> Any:
        """Return the underlying Pipecat transport instance."""
        pass


class LiveKitTransportAdapter(PipecatTransportAdapter):
    """Concrete transport adapter using LiveKit WebRTC.

    Wraps LiveKitTransport and exposes a PipecatTransportAdapter-compliant 
    interface to the rest of Pillar 1.

    Args:
        room_url:  LiveKit room URL. Falls back to LIVEKIT_URL env var.
    """

    def __init__(self, room_url: str | None = None) -> None:
        from app.config import LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_ROOM
        from pipecat.transports.livekit.transport import LiveKitTransport, LiveKitParams
        from pipecat.audio.vad.silero import SileroVADAnalyzer
        from pipecat.audio.vad.vad_analyzer import VADParams
        from livekit.api import AccessToken, VideoGrants

        resolved_room_url = room_url or LIVEKIT_URL

        if not resolved_room_url:
            raise ValueError(
                "LIVEKIT_URL is not set. "
                "Add it to your .env file or pass room_url to LiveKitTransportAdapter()."
            )

        token = AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
            .with_identity("cybernauts-bot") \
            .with_name("Cybernauts Agent") \
            .with_grants(VideoGrants(
                room_join=True,
                room=LIVEKIT_ROOM,
            )) \
            .to_jwt()

        self._transport = LiveKitTransport(
            url=resolved_room_url,
            token=token,
            room_name=LIVEKIT_ROOM,
            params=LiveKitParams(
                audio_out_enabled=True,
                audio_in_enabled=True,
                camera_out_enabled=False,
                vad_enabled=True,
                # VAD tuning
                vad_analyzer=SileroVADAnalyzer(
                    params=VADParams(
                        confidence=0.7,
                        start_secs=0.2,
                        stop_secs=0.5,
                        min_volume=0.6,
                    )
                ),
            ),
        )

    def get_pipecat_transport(self) -> Any:
        """Return the underlying LiveKitTransport instance."""
        return self._transport

    def register_events(self) -> None:
        """Attach connection lifecycle logging to the transport."""

        @self._transport.event_handler("on_joined")  # type: ignore
        async def on_joined(transport: Any, data: Any) -> None:
            from loguru import logger
            logger.info("LiveKit room joined")

        @self._transport.event_handler("on_participant_left")  # type: ignore
        async def on_participant_left(transport: Any, participant: Any, reason: Any) -> None:
            from loguru import logger
            logger.info("Participant left LiveKit room | reason={r}", r=reason)

        @self._transport.event_handler("on_error")  # type: ignore
        async def on_error(transport: Any, error: Any) -> None:
            from loguru import logger
            logger.error("LiveKit transport error: {e}", e=error)


class MockWebSocketTransport(PipecatTransportAdapter):
    """Mock implementation for testing."""
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs

    def get_pipecat_transport(self) -> Any:
        return {"type": "websocket", "config": self.kwargs}


class MockWebRTCTransport(PipecatTransportAdapter):
    """Mock implementation for testing."""
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs

    def get_pipecat_transport(self) -> Any:
        return {"type": "webrtc", "config": self.kwargs}

class TwilioTransportAdapter(PipecatTransportAdapter):
    """Concrete transport adapter using Twilio WebSockets (FastAPI)."""

    def __init__(self, websocket: Any, stream_sid: str) -> None:
        from pipecat.transports.websocket.fastapi import FastAPIWebsocketTransport, FastAPIWebsocketParams
        from pipecat.serializers.twilio import TwilioFrameSerializer
        from pipecat.audio.vad.silero import SileroVADAnalyzer
        from pipecat.audio.vad.vad_analyzer import VADParams

        self._transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                audio_in_enabled=True,
                audio_in_sample_rate=16000,
                audio_out_enabled=True,
                audio_out_sample_rate=16000,
                add_wav_header=False,
                serializer=TwilioFrameSerializer(stream_sid=stream_sid, params=TwilioFrameSerializer.InputParams(auto_hang_up=False)),
            ),
        )

    def get_pipecat_transport(self) -> Any:
        """Return the underlying FastAPIWebsocketTransport instance."""
        return self._transport
