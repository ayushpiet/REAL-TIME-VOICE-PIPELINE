"""
Processor mapping for Pipecat.
"""

from typing import Any

from app.pipeline.processors import ProcessorRole


class PipecatProcessorAdapter:
    """Wraps a Pipecat processor to track its execution."""
    
    def __init__(self, name: str, pipecat_processor: Any):
        self.name = name
        self.pipecat_processor = pipecat_processor
        
    def get_processor(self) -> Any:
        return self.pipecat_processor


# Mock implementations for testing since we don't have pipecat installed
class MockPipecatProcessor:
    def __init__(self, name: str):
        self.name = name

def create_pipecat_processor(role: ProcessorRole, metadata: dict[str, Any]) -> Any:
    """Factory to create the underlying Pipecat processor instance based on role."""
    # In a real implementation, this would instantiate actual pipecat classes
    # e.g., DeepgramSTTService, OpenAILLMService, ElevenLabsTTSService
    
    if role == ProcessorRole.STT:
        return MockPipecatProcessor("MockSTT")
    elif role == ProcessorRole.LLM:
        return MockPipecatProcessor("MockLLM")
    elif role == ProcessorRole.TTS:
        return MockPipecatProcessor("MockTTS")
    elif role in (ProcessorRole.TRANSPORT_INPUT, ProcessorRole.TRANSPORT_OUTPUT):
        # Transports are handled separately via transport.py usually, but mock them here
        return MockPipecatProcessor(f"MockTransport_{role.value}")
    else:
        return MockPipecatProcessor(f"MockCustom_{role.value}")
