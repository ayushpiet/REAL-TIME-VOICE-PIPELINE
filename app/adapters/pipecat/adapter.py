"""
Main Pipecat Adapter.
"""

import asyncio
from typing import Any, List, Optional

from loguru import logger

from app.events import EventBus
from app.pipeline.models import Pipeline
from .events import PipecatEventBridge
from .exceptions import PipecatAdapterError
from .lifecycle import PipecatLifecycleManager
from .mapper import PipecatPipelineMapper
from .transport import PipecatTransportAdapter


# Mock Pipecat Pipeline class for testing without dependencies
class MockPipecatPipelineTask:
    def __init__(self, processors: List[Any], event_handler: Any = None):
        self.processors = processors
        self.event_handler = event_handler
        self._running = False
        
    async def start(self) -> None:
        self._running = True
        if self.event_handler:
            self.event_handler.on_pipeline_started()
            
    async def wait(self) -> None:
        while self._running:
            await asyncio.sleep(0.1)
            
    async def stop(self) -> None:
        self._running = False
        if self.event_handler:
            self.event_handler.on_pipeline_completed()


class PipecatAdapter:
    """Executes a framework-independent Pipeline using the Pipecat runtime."""
    
    def __init__(
        self,
        pipeline: Pipeline,
        event_bus: EventBus,
        session_id: str,
        execution_id: str,
        transport: Optional[PipecatTransportAdapter] = None
    ):
        self.pipeline = pipeline
        self.event_bus = event_bus
        self.session_id = session_id
        self.execution_id = execution_id
        self.transport = transport
        
        self.bridge = PipecatEventBridge(event_bus, session_id, execution_id)
        self.task: Optional[MockPipecatPipelineTask] = None
        self.lifecycle: Optional[PipecatLifecycleManager] = None
        
        self._build_task()
        
    def _build_task(self) -> None:
        """Build the Pipecat pipeline task."""
        try:
            logger.bind(session_id=self.session_id, execution_id=self.execution_id).info("Building Pipecat adapter task")
            
            # 1. Map processors
            processor_adapters = PipecatPipelineMapper.map_pipeline(self.pipeline)
            pipecat_processors = [p.get_processor() for p in processor_adapters]
            
            # 2. Add transport if needed (often injected differently in pipecat, but here as example)
            if self.transport:
                pipecat_processors.insert(0, self.transport.get_pipecat_transport())
                
            # 3. Create the pipecat pipeline task (mocked here)
            self.task = MockPipecatPipelineTask(processors=pipecat_processors, event_handler=self.bridge)
            self.lifecycle = PipecatLifecycleManager(self.task, self.session_id)
            
        except Exception as e:
            self.bridge.on_pipeline_failed(e)
            raise PipecatAdapterError(f"Failed to build Pipecat adapter task: {e}") from e

    async def run(self) -> None:
        """Execute the pipeline using Pipecat."""
        if not self.lifecycle:
            raise PipecatAdapterError("Adapter not fully initialized")
            
        try:
            logger.bind(session_id=self.session_id, execution_id=self.execution_id).info("Running Pipecat adapter")
            
            await self.lifecycle.start()
            
            # In a real Pipecat setup, processors trigger events themselves. 
            # We mock that behavior here for testing since we don't have real callbacks running.
            for proc in self.task.processors: # type: ignore
                name = getattr(proc, "name", "unknown")
                self.bridge.on_processor_started(name)
                await asyncio.sleep(0.01) # Simulate work
                self.bridge.on_processor_completed(name)
            
            await self.lifecycle.stop() # Explicit stop for mock, normally it runs until transport closes
            await self.lifecycle.wait_until_done()
            
        except Exception as e:
            self.bridge.on_pipeline_failed(e)
            logger.bind(session_id=self.session_id).error(f"Pipecat adapter execution failed: {e}")
            raise PipecatAdapterError(f"Execution failed: {e}") from e
