#!/usr/bin/env python3
"""
Local voice transcription using faster-whisper.
Usage: transcribe.py <audio_file>
Prints transcript to stdout, errors to stderr.
"""
import sys
import os
import subprocess

# Find ffmpeg: prefer ~/.local/bin, then PATH
def _find_ffmpeg():
    candidates = [
        os.path.expanduser('~/.local/bin/ffmpeg'),
        '/usr/bin/ffmpeg',
        '/usr/local/bin/ffmpeg',
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return 'ffmpeg'  # fallback to PATH

FFMPEG = _find_ffmpeg()

def transcribe(audio_path: str) -> str:
    from faster_whisper import WhisperModel

    model_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'models', 'whisper')
    model = WhisperModel('tiny', device='cpu', compute_type='int8', download_root=model_dir)

    # Convert to wav (16kHz mono) for reliable transcription
    wav_path = audio_path + '.wav'
    subprocess.run(
        [FFMPEG, '-y', '-i', audio_path, '-ar', '16000', '-ac', '1', wav_path],
        check=True, capture_output=True
    )

    segments, info = model.transcribe(wav_path, beam_size=5, language=None)
    transcript = ' '.join(seg.text.strip() for seg in segments).strip()

    if os.path.exists(wav_path):
        os.unlink(wav_path)

    return transcript

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: transcribe.py <audio_file>', file=sys.stderr)
        sys.exit(1)

    audio_file = sys.argv[1]
    if not os.path.exists(audio_file):
        print(f'File not found: {audio_file}', file=sys.stderr)
        sys.exit(1)

    try:
        result = transcribe(audio_file)
        print(result, end='')
    except Exception as e:
        print(f'Transcription error: {e}', file=sys.stderr)
        sys.exit(1)
