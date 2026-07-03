"""
Event mapping from Pipecat to our Event Bus.
"""


from loguru import logger

from app.events import EventBus
from app.events.event_types import (
    PipelineStarted,
    PipelineFailed,
    ProcessorExecutionStarted,
    ProcessorExecutionCompleted,
    ProcessorExecutionFailed,
    PipelineCompleted,
)


class PipecatEventBridge:
    """Bridges Pipecat events into our internal Event Bus."""
    
    def __init__(self, event_bus: EventBus, session_id: str, execution_id: str):
        self._bus = event_bus
        self._session_id = session_id
        self._execution_id = execution_id

    def on_pipeline_started(self) -> None:
        self._bus.publish_sync(PipelineStarted(session_id=self._session_id, payload={"execution_id": self._execution_id}))

    def on_pipeline_completed(self) -> None:
        self._bus.publish_sync(PipelineCompleted(session_id=self._session_id, payload={"execution_id": self._execution_id}))

    def on_pipeline_failed(self, error: Exception) -> None:
        self._bus.publish_sync(PipelineFailed(session_id=self._session_id, payload={"execution_id": self._execution_id, "error": str(error)}))

    def on_processor_started(self, processor_name: str) -> None:
        self._bus.publish_sync(ProcessorExecutionStarted(session_id=self._session_id, payload={"processor_id": processor_name}))

    def on_processor_completed(self, processor_name: str) -> None:
        self._bus.publish_sync(ProcessorExecutionCompleted(session_id=self._session_id, payload={"processor_id": processor_name}))

    def on_processor_error(self, processor_name: str, error: Exception) -> None:
        self._bus.publish_sync(ProcessorExecutionFailed(session_id=self._session_id, payload={"processor_id": processor_name, "error": str(error)}))
        logger.bind(session_id=self._session_id).error(f"Pipecat processor {processor_name} error: {error}")
