"""
Factory for creating Pipecat Adapters.
"""

from typing import Optional

from app.events import EventBus
from app.pipeline.models import Pipeline
from .adapter import PipecatAdapter
from .transport import PipecatTransportAdapter


class PipecatFactory:
    """Factory to build configured Pipecat adapters."""
    
    @staticmethod
    def create_adapter(
        pipeline: Pipeline,
        event_bus: EventBus,
        session_id: str,
        execution_id: str,
        transport: Optional[PipecatTransportAdapter] = None
    ) -> PipecatAdapter:
        """Create and return a configured PipecatAdapter."""
        return PipecatAdapter(
            pipeline=pipeline,
            event_bus=event_bus,
            session_id=session_id,
            execution_id=execution_id,
            transport=transport
        )
