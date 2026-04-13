#!/usr/bin/env python3
"""
Local text-to-speech using piper-tts.
Usage: tts.py <output_file> [text...]
       echo "text" | tts.py <output_file>
Writes OGG opus audio to output_file (suitable for WhatsApp/Telegram voice messages).
"""
import sys
import os
import subprocess
import tempfile

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'models', 'piper')
VOICE_MODEL = os.path.join(MODELS_DIR, 'ru_RU-irina-medium.onnx')

def synthesize(text: str, output_path: str) -> None:
    from piper import PiperVoice

    if not os.path.exists(VOICE_MODEL):
        raise FileNotFoundError(f'Voice model not found: {VOICE_MODEL}')

    voice = PiperVoice.load(VOICE_MODEL)

    # Write raw PCM to temp wav file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_wav:
        wav_path = tmp_wav.name

    try:
        import wave
        with wave.open(wav_path, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(voice.config.sample_rate)
            voice.synthesize(text, wav_file)

        # Convert to OGG opus for WhatsApp/Telegram voice messages
        subprocess.run(
            ['ffmpeg', '-y', '-i', wav_path, '-c:a', 'libopus', '-b:a', '32k', output_path],
            check=True, capture_output=True
        )
    finally:
        if os.path.exists(wav_path):
            os.unlink(wav_path)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: tts.py <output_file> [text]', file=sys.stderr)
        sys.exit(1)

    output_file = sys.argv[1]

    if len(sys.argv) > 2:
        text = ' '.join(sys.argv[2:])
    else:
        text = sys.stdin.read().strip()

    if not text:
        print('No text provided', file=sys.stderr)
        sys.exit(1)

    try:
        synthesize(text, output_file)
        print(f'TTS written to {output_file}', file=sys.stderr)
    except Exception as e:
        print(f'TTS error: {e}', file=sys.stderr)
        sys.exit(1)
