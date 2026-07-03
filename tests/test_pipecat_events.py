"""
Tests for Pipecat Events and Transports.
"""

from app.events import EventBus
from app.adapters.pipecat import (
    PipecatEventBridge,
    MockWebSocketTransport,
    MockWebRTCTransport
)


def test_pipecat_event_bridge() -> None:
    bus = EventBus()
    # We will test publishing doesn't crash. Since EventBus uses async subscriber logic for full handling,
    # publish_sync puts it in a queue. We just check no exceptions are raised.
    bridge = PipecatEventBridge(bus, "session1", "exec1")
    
    bridge.on_pipeline_started()
    bridge.on_processor_started("Proc1")
    bridge.on_processor_completed("Proc1")
    bridge.on_processor_error("Proc1", ValueError("Proc Error"))
    bridge.on_pipeline_failed(ValueError("Pipe Error"))
    bridge.on_pipeline_completed()
    
    assert bus._queue.qsize() == 6


def test_transports() -> None:
    ws = MockWebSocketTransport(host="localhost", port=8000)
    config = ws.get_pipecat_transport()
    assert config["type"] == "websocket"
    assert config["config"]["host"] == "localhost"
    
    webrtc = MockWebRTCTransport(room="test")
    config2 = webrtc.get_pipecat_transport()
    assert config2["type"] == "webrtc"
    assert config2["config"]["room"] == "test"
