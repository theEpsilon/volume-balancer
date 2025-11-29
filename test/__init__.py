import atexit
import os

from test.audio_session_factory import AudioSessionFactory

#########################################
# Main init
#########################################
audio_session_factory = AudioSessionFactory()

if os.environ.get("CI"):
    print("CI mode detected: Mocking Pycaw audio session functions")
    audio_session_factory.set_mode("ci")
else:
    print("Local mode detected: Creating COM audio processes")
    audio_session_factory.set_mode("local")

audio_session_factory.init_processes()
atexit.register(audio_session_factory.kill_sessions)