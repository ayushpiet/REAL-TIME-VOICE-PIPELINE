import asyncio
import wave
import os
from loguru import logger
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.frames.frames import (
    Frame, TranscriptionFrame, LLMFullResponseStartFrame,
    OutputAudioRawFrame, TTSStartedFrame, TTSStoppedFrame, TextFrame
)

class LatencyFillerProcessor(FrameProcessor):
    """
    Monitors transcription frames and plays a short filler audio 
    if the LLM response is delayed by more than a given threshold.
    """
    def __init__(self, filler_wav_path: str = "hmm.wav", delay_threshold_ms: int = 400, **kwargs):
        super().__init__(**kwargs)
        self.delay_threshold = delay_threshold_ms / 1000.0
        self._wait_task = None
        self._audio_frames = []
        
        # Preload the audio file
        try:
            if os.path.exists(filler_wav_path):
                with wave.open(filler_wav_path, "rb") as wf:
                    sample_rate = wf.getframerate()
                    num_channels = wf.getnchannels()
                    # Chunk size doesn't matter too much, just need to send it down
                    chunk_frames = int(sample_rate * 0.05) # 50ms chunks
                    while True:
                        data = wf.readframes(chunk_frames)
                        if not data:
                            break
                        self._audio_frames.append(OutputAudioRawFrame(
                            audio=data,
                            sample_rate=sample_rate,
                            num_channels=num_channels
                        ))
                logger.info(f"Loaded {len(self._audio_frames)} chunks from {filler_wav_path} for filler processor.")
            else:
                logger.warning(f"Filler audio {filler_wav_path} not found. Filler disabled.")
        except Exception as e:
            logger.error(f"Failed to load filler audio: {e}")

    async def _play_filler_if_delayed(self):
        """Task that waits for the threshold and pushes the audio."""
        if not self._audio_frames:
            return
            
        try:
            await asyncio.sleep(self.delay_threshold)
            logger.info(f"LLM response delayed > {self.delay_threshold}s. Playing filler audio...")
            
            # Use self.push_frame directly. Note: Pipecat processor queues handles concurrent push_frame safely.
            await self.push_frame(TTSStartedFrame(), FrameDirection.DOWNSTREAM)
            for frame in self._audio_frames:
                await self.push_frame(frame, FrameDirection.DOWNSTREAM)
                await asyncio.sleep(0.01) # Yield to event loop, simulate streaming
            await self.push_frame(TTSStoppedFrame(), FrameDirection.DOWNSTREAM)
            
        except asyncio.CancelledError:
            # Task was cancelled because LLM responded fast enough!
            logger.debug("Filler wait task cancelled, LLM responded fast.")

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        
        from pipecat.frames.frames import LLMMessagesAppendFrame
        
        # Intercept going DOWNSTREAM from user_agg to LLM
        if isinstance(frame, LLMMessagesAppendFrame):
            # Only trigger filler if it's a user message, not system message
            # LLMMessagesAppendFrame has 'messages' list
            is_user_msg = any(m.get("role") == "user" for m in frame.messages)
            if is_user_msg:
                if self._wait_task and not self._wait_task.done():
                    self._wait_task.cancel()
                self._wait_task = asyncio.create_task(self._play_filler_if_delayed())
                
        # Intercept when LLM starts generating or when TTS starts
        elif isinstance(frame, (LLMFullResponseStartFrame, TextFrame, TTSStartedFrame)):
            if self._wait_task and not self._wait_task.done():
                self._wait_task.cancel()
            self._wait_task = None
            
        await self.push_frame(frame, direction)
