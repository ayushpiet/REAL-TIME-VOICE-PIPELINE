import re
from loguru import logger
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.frames.frames import Frame, TranscriptionFrame, LLMMessagesAppendFrame

class LanguageRoutingProcessor(FrameProcessor):
    """
    Analyzes the user's transcribed text to detect language dynamically.
    Instead of changing the entire system prompt, it appends a strict language 
    instruction to the end of the user's message before the LLM processes it.
    """
    def __init__(self, shared_state=None, **kwargs):
        super().__init__(**kwargs)
        self.shared_state = shared_state or {}
        self.HINDI_INDICATORS = {
            'hai', 'mujhe', 'kya', 'kaise', 'chahiye', 'mera', 'namaste', 'nahi', 
            'haan', 'ko', 'se', 'mein', 'liye', 'karna', 'kar', 
            'rha', 'rhi', 'hu', 'tha', 'thi', 'sakte', 'bata', 'batao', 'koi'
        }

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        from pipecat.frames.frames import TranscriptionFrame
        
        # We only care about TranscriptionFrame containing user's speech text
        if isinstance(frame, TranscriptionFrame) and frame.text and not frame.user_id == "bot":
            text = frame.text.lower()
            
            # --- Check for Goodbye phrases ---
            clean_text = re.sub(r'[^\w\s]', '', text.strip())
            closing_phrases = ["bye", "goodbye", "good bye", "alvida", "thank you", "thanks", "that is all", "thats all", "bas itna hi", "theek hai"]
            
            if len(clean_text.split()) <= 8 and any(phrase in clean_text for phrase in closing_phrases):
                logger.info(f"LanguageRoutingProcessor: User said goodbye ('{frame.text}'). Will terminate after bot replies.")
                self.shared_state["hangup_requested"] = True
            
            # --- Language Detection ---
            # Check for explicit Devanagari script
            devanagari_count = len(re.findall(r'[\u0900-\u097F]', text))
            has_devanagari = devanagari_count > 10
            
            # Check for romanized Hindi words (Hinglish)
            words = set(re.findall(r'\b\w+\b', text))
            hindi_word_count = len(words.intersection(self.HINDI_INDICATORS))
            
            # Force language based on indicators
            if has_devanagari or hindi_word_count >= 1:
                logger.info(f"Language Detection: Hindi/Hinglish detected in '{frame.text}' (Devanagari: {devanagari_count}, Hinglish indicators: {hindi_word_count})")
                frame.text = f"{frame.text}\n[You MUST reply completely in natural Hindi]"
            else:
                logger.info(f"Language Detection: English detected in '{frame.text}'")
                frame.text = f"{frame.text}\n[You MUST reply completely in English]"
            
        await self.push_frame(frame, direction)


class CallTerminationProcessor(FrameProcessor):
    """
    Monitors the LLM output. If a hangup was requested by the LanguageRoutingProcessor,
    it gracefully pushes an EndFrame when the LLM finishes its response.
    """
    def __init__(self, shared_state=None, **kwargs):
        super().__init__(**kwargs)
        self.shared_state = shared_state or {}

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        from pipecat.frames.frames import LLMFullResponseEndFrame, EndFrame
        
        await self.push_frame(frame, direction)
        
        # When bot finishes its response, if hangup requested, queue EndFrame
        if isinstance(frame, LLMFullResponseEndFrame) and self.shared_state.get("hangup_requested"):
            logger.info("CallTerminationProcessor: Bot finished responding to goodbye. Pushing EndFrame to terminate the call.")
            await self.push_frame(EndFrame(), direction)
            self.shared_state["hangup_requested"] = False
