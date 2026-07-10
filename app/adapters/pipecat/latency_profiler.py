import time
from loguru import logger
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.frames.frames import (
    Frame,
    TranscriptionFrame,
    TextFrame,
    AudioRawFrame,
    LLMFullResponseStartFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
    LLMFullResponseEndFrame,
)
from app.main import global_timers

class LatencyProfiler(FrameProcessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transcription_count = 0
        self.text_frame_count = 0
        self.audio_chunk_count = 0

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        now = time.perf_counter()
        
        if isinstance(frame, TranscriptionFrame):
            if "first_partial_transcript" not in global_timers:
                global_timers["first_partial_transcript"] = now
                logger.info(f"[PROFILER] First Partial Transcript: {now}")
            # If we want final transcript, we need to wait until VADUserStoppedSpeakingFrame or we can track it by looking at frame.text?
            
        elif isinstance(frame, LLMFullResponseStartFrame):
            if "llm_first_token" not in global_timers:
                global_timers["llm_first_token"] = now
                logger.info(f"[PROFILER] LLM First Token: {now}")
                
        elif isinstance(frame, LLMFullResponseEndFrame):
            global_timers["llm_complete"] = now
            logger.info(f"[PROFILER] LLM Complete: {now}")
                
        elif isinstance(frame, TTSStartedFrame):
            global_timers["tts_first_byte"] = now
            logger.info(f"[PROFILER] TTS First Byte: {now}")
            
        elif isinstance(frame, TTSStoppedFrame):
            global_timers["tts_complete"] = now
            logger.info(f"[PROFILER] TTS Complete: {now}")
            
        elif isinstance(frame, AudioRawFrame):
            if "first_audio_playback" not in global_timers:
                global_timers["first_audio_playback"] = now
                logger.info(f"[PROFILER] First Audio Playback: {now}")

        await self.push_frame(frame, direction)
