"""
Transport abstractions for Pipecat.

Contains:
- PipecatTransportAdapter  — abstract base class
- DailyTransportAdapter    — concrete implementation using Daily.co WebRTC (Pillar 2)
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


class DailyTransportAdapter(PipecatTransportAdapter):
    """Concrete transport adapter using Daily.co WebRTC (Pillar 2).

    Wraps the get_daily_transport() helper from Pillar 2 and exposes
    a PipecatTransportAdapter-compliant interface to the rest of Pillar 1.

    Args:
        room_url:  Daily room URL. Falls back to DAILY_ROOM_URL env var.
        bot_name:  Display name the bot uses when joining the room.
    """

    def __init__(self, room_url: str | None = None, bot_name: str | None = None) -> None:
        from app.config import DAILY_ROOM_URL, BOT_NAME
        from pipecat.transports.services.daily import DailyTransport, DailyParams
        from pipecat.vad.silero import SileroVADAnalyzer
        from pipecat.vad.vad_analyzer import VADParams

        resolved_room_url = room_url or DAILY_ROOM_URL
        resolved_bot_name = bot_name or BOT_NAME

        if not resolved_room_url:
            raise ValueError(
                "DAILY_ROOM_URL is not set. "
                "Add it to your .env file or pass room_url to DailyTransportAdapter()."
            )

        self._transport = DailyTransport(
            resolved_room_url,
            None,           # meeting token — pass if room is private
            resolved_bot_name,
            DailyParams(
                audio_out_enabled=True,
                audio_in_enabled=True,
                camera_out_enabled=False,
                vad_enabled=True,
                # VAD tuning: identical to Pillar 2 for consistency
                vad_analyzer=SileroVADAnalyzer(
                    params=VADParams(
                        confidence=0.7,
                        start_secs=0.2,
                        stop_secs=0.5,
                        min_volume=0.6,
                    )
                ),
                transcription_enabled=False,  # Deepgram handles STT separately
            ),
        )

    def get_pipecat_transport(self) -> Any:
        """Return the underlying DailyTransport instance."""
        return self._transport

    def register_events(self) -> None:
        """Attach connection lifecycle logging to the transport."""

        @self._transport.event_handler("on_joined")
        async def on_joined(transport: Any, data: Any) -> None:
            from loguru import logger
            logger.info("Daily room joined | participants={p}", p=data.get("participants", ""))

        @self._transport.event_handler("on_participant_left")
        async def on_participant_left(transport: Any, participant: Any, reason: Any) -> None:
            from loguru import logger
            logger.info("Participant left Daily room | reason={r}", r=reason)

        @self._transport.event_handler("on_error")
        async def on_error(transport: Any, error: Any) -> None:
            from loguru import logger
            logger.error("Daily transport error: {e}", e=error)


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

    def __init__(self, websocket: Any) -> None:
        from pipecat.transports.network.fastapi_websocket import FastAPIWebsocketTransport, FastAPIWebsocketParams
        from pipecat.serializers.twilio import TwilioFrameSerializer
        from pipecat.vad.silero import SileroVADAnalyzer
        from pipecat.vad.vad_analyzer import VADParams

        self._transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                audio_out_enabled=True,
                add_wav_header=False,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(
                    params=VADParams(
                        confidence=0.7,
                        start_secs=0.2,
                        stop_secs=0.5,
                        min_volume=0.6,
                    )
                ),
                vad_audio_passthrough=True,
                serializer=TwilioFrameSerializer(stream_sid=""),
            ),
        )

    def get_pipecat_transport(self) -> Any:
        """Return the underlying FastAPIWebsocketTransport instance."""
        return self._transport
