import { downloadMediaMessage } from '@whiskeysockets/baileys';
import { WAMessage, WASocket } from '@whiskeysockets/baileys';
import { execFile } from 'child_process';
import { promisify } from 'util';
import fs from 'fs';
import os from 'os';
import path from 'path';
import { fileURLToPath } from 'url';

const execFileAsync = promisify(execFile);

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SCRIPTS_DIR = path.resolve(__dirname, '..', 'scripts');
const VENV_PYTHON = path.resolve(__dirname, '..', 'venv', 'bin', 'python3');
const TRANSCRIBE_SCRIPT = path.join(SCRIPTS_DIR, 'transcribe.py');
const TTS_SCRIPT = path.join(SCRIPTS_DIR, 'tts.py');

const FALLBACK_MESSAGE = '[Voice Message - transcription unavailable]';

// TTS trigger phrases (case-insensitive)
const TTS_TRIGGERS = [
  'отвечай голосом',
  'reply with voice',
  'голосовой ответ',
  'voice reply',
  'отвечай аудио',
];

export function isTTSTrigger(text: string): boolean {
  const lower = text.toLowerCase();
  return TTS_TRIGGERS.some((t) => lower.includes(t));
}

export async function transcribeWithLocalWhisper(
  audioBuffer: Buffer,
): Promise<string | null> {
  const tmpFile = path.join(os.tmpdir(), `voice_${Date.now()}.ogg`);
  try {
    fs.writeFileSync(tmpFile, audioBuffer);
    const { stdout } = await execFileAsync(VENV_PYTHON, [
      TRANSCRIBE_SCRIPT,
      tmpFile,
    ]);
    return stdout.trim() || null;
  } catch (err) {
    console.error('Local whisper transcription failed:', err);
    return null;
  } finally {
    if (fs.existsSync(tmpFile)) fs.unlinkSync(tmpFile);
  }
}

export async function transcribeAudioMessage(
  msg: WAMessage,
  sock: WASocket,
): Promise<string | null> {
  try {
    const buffer = (await downloadMediaMessage(
      msg,
      'buffer',
      {},
      {
        logger: console as any,
        reuploadRequest: sock.updateMediaMessage,
      },
    )) as Buffer;

    if (!buffer || buffer.length === 0) {
      console.error('Failed to download audio message');
      return FALLBACK_MESSAGE;
    }

    console.log(`Downloaded audio message: ${buffer.length} bytes`);

    const transcript = await transcribeWithLocalWhisper(buffer);
    if (!transcript) return FALLBACK_MESSAGE;
    return transcript;
  } catch (err) {
    console.error('Transcription error:', err);
    return FALLBACK_MESSAGE;
  }
}

export function isVoiceMessage(msg: WAMessage): boolean {
  return msg.message?.audioMessage?.ptt === true;
}

/**
 * Synthesize text to OGG opus voice message.
 * Returns path to the generated file, or null on failure.
 */
export async function synthesizeSpeech(text: string): Promise<string | null> {
  const outFile = path.join(os.tmpdir(), `tts_${Date.now()}.ogg`);
  try {
    await execFileAsync(VENV_PYTHON, [TTS_SCRIPT, outFile, text]);
    if (fs.existsSync(outFile) && fs.statSync(outFile).size > 0) {
      return outFile;
    }
    return null;
  } catch (err) {
    console.error('TTS synthesis failed:', err);
    return null;
  }
}
