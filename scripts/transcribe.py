#!/usr/bin/env python3
"""
Local voice transcription using faster-whisper.
Usage: transcribe.py <audio_file>
Prints transcript to stdout, errors to stderr.
"""
import sys
import os
import tempfile
import subprocess

def transcribe(audio_path: str) -> str:
    from faster_whisper import WhisperModel

    model_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'models', 'whisper')
    model = WhisperModel('tiny', device='cpu', compute_type='int8', download_root=model_dir)

    # Convert to wav if needed (faster-whisper handles most formats but wav is safest)
    wav_path = audio_path
    if not audio_path.endswith('.wav'):
        wav_path = audio_path + '.wav'
        subprocess.run(
            ['ffmpeg', '-y', '-i', audio_path, '-ar', '16000', '-ac', '1', wav_path],
            check=True, capture_output=True
        )

    segments, info = model.transcribe(wav_path, beam_size=5, language=None)
    transcript = ' '.join(seg.text.strip() for seg in segments).strip()

    if wav_path != audio_path and os.path.exists(wav_path):
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
