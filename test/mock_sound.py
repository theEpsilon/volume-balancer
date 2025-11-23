import io
import wave
import time
import winsound as ws

def get_wav_audio():
    frames = b"\x00\x00" * (8000 * 2)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(frames)

    return buf.getvalue()

wav_data = get_wav_audio()

while True:
    ws.PlaySound(wav_data, ws.SND_MEMORY)
    time.sleep(2)