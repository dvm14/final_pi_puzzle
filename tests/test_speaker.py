"""
test_speaker.py — Confirm Piper TTS and the speaker are working.

Run:  python test_speaker.py
You should hear three spoken phrases through the speaker.
If you get a device error, run `python -m sounddevice` to list available
devices and update the `device` index in speak() below.
"""

import numpy as np
import sounddevice as sd
from piper import PiperVoice

VOICE_MODEL  = "models/en_US-libritts-high.onnx"
VOICE_CONFIG = "models/en_US-libritts-high.onnx.json"


def load_piper():
    return PiperVoice.load(model_path=VOICE_MODEL, config_path=VOICE_CONFIG)


TARGET_RATE = 48000  # USB2.0 Device supports 48000 Hz

def speak(piper, text):
    print(f"  Speaking: \"{text}\"")
    try:
        audio_chunks = []
        for chunk in piper.synthesize(text):
            audio_chunks.append(chunk.audio_float_array)

        if audio_chunks:
            audio = np.concatenate(audio_chunks)

            # Resample from piper's native rate to 48000 Hz using linear interpolation
            src_rate = piper.config.sample_rate
            if src_rate != TARGET_RATE:
                target_len = int(len(audio) * TARGET_RATE / src_rate)
                audio = np.interp(
                    np.linspace(0, len(audio), target_len),
                    np.arange(len(audio)),
                    audio,
                )

            sd.play(audio, samplerate=TARGET_RATE, device=1)
            sd.wait()
    except Exception as e:
        print(f"  Speech error: {e}")


print("Loading Piper voice model...")
piper = load_piper()
print("Model loaded.\n")

phrases = [
    "Hello! The speaker is working.",
    "Are you ready to start the game?",
    "Round one. Show a happy face.",
]

for phrase in phrases:
    speak(piper, phrase)

print("\nDone.")
