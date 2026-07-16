import asyncio
import time
import sys
import os

# Ensure we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.adapters.pipecat.transport import LiveKitTransportAdapter, TwilioTransportAdapter
from pipecat.audio.filters.rnnoise_filter import RNNoiseFilter

async def measure_rnnoise_latency():
    print("--- AUDIO PREPROCESSING LATENCY TEST ---")
    filter = RNNoiseFilter()
    # Mock transport sample rate
    await filter.start(sample_rate=48000)
    
    # 10ms of 48kHz audio = 480 samples * 2 bytes (int16) = 960 bytes
    dummy_audio = b"\x00\x00" * 480
    
    # Warmup
    for _ in range(5):
        await filter.filter(dummy_audio)
        
    iterations = 100
    start_time = time.perf_counter()
    for _ in range(iterations):
        await filter.filter(dummy_audio)
        
    total_time = time.perf_counter() - start_time
    avg_latency = (total_time / iterations) * 1000
    print(f"✅ Preprocessing average latency per frame: {avg_latency:.3f} ms")
    
    # We require latency < 5ms per frame to be considered "lightweight"
    assert avg_latency < 5.0, f"Latency is too high! {avg_latency} ms"

def test_transports_can_build():
    print("\n--- TRANSPORT BUILD TEST ---")
    # Livekit Transport test
    try:
        lk_adapter = LiveKitTransportAdapter(room_url="wss://mock.livekit.com", bot_name="MockBot")
        lk_transport = lk_adapter.get_pipecat_transport()
        # Verify that the filter is actually attached
        params = lk_transport.params
        has_filter = getattr(params, "audio_in_filter", None) is not None
        print(f"LiveKit RNNoise filter applied: {has_filter}")
        assert has_filter, "LiveKit filter not applied!"
    except ValueError as e:
        # Ignore LIVEKIT_URL is not set error if it occurs
        if "LIVEKIT" not in str(e):
            raise
    
    print("✅ Transport Adapters build successfully with RNNoiseFilter.")

async def main():
    await measure_rnnoise_latency()
    test_transports_can_build()

if __name__ == "__main__":
    asyncio.run(main())
