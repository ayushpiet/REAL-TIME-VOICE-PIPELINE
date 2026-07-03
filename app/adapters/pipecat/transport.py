"""
Transport abstractions for Pipecat.
"""

import abc
from typing import Any



class PipecatTransportAdapter(abc.ABC):
    """Abstract interface for wrapping a Pipecat Transport."""
    
    @abc.abstractmethod
    def get_pipecat_transport(self) -> Any:
        """Return the underlying Pipecat transport instance."""
        pass


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
