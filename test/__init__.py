import atexit
import os
import subprocess
import time

from pycaw.pycaw import AudioUtilities, AudioSession
from unittest.mock import patch, MagicMock

#########################################
# Setup audio mocking for CI runners
#########################################

class MockAudioSession:
    def __init__(self, name, pid):
        self.SimpleAudioVolume = self.MockVolume()
        self.Process = self.MockProcess(name, pid)

    class MockProcess:
        def __init__(self, name, pid):
            self._name = name
            self.pid = pid
        
        def name(self):
            return self._name

    class MockVolume:
        def __init__(self):
            self.volume = 1

        def SetMasterVolume(self, volume, x):
            self.volume = volume
        
        def GetMasterVolume(self):
            return self.volume;
    

def mock_audio_ci():
    patcher_sessions = patch(
        "pycaw.utils.AudioUtilities.GetAllSessions",
        return_value = [
            MockAudioSession("python.exe", 69420),
            MockAudioSession("python.exe", 6767)
        ]
    )
    patcher_sessions.start()

    patcher_mgr = patch(
        "pycaw.utils.AudioUtilities.GetAudioSessionManager",
        return_value=MagicMock()
    )
    patcher_mgr.start()

    patcher_speakers = patch(
        "pycaw.utils.AudioUtilities.GetSpeakers",
        return_value=MagicMock()
    )
    patcher_speakers.start()

    return [patcher_sessions, patcher_mgr, patcher_speakers]

#########################################
# Setup audio for local testing
#########################################

LOCAL_PROCESSES = []

def mock_audio_local():
    p1 = subprocess.Popen(["python", "test/mock_subprocess.py"])
    p2 = subprocess.Popen(["python", "test/mock_subprocess.py"])

    start_time = time.time()
    max_wait_time = 10

    while len(LOCAL_PROCESSES) < 2:
        time.sleep(1)

        if time.time() - start_time > max_wait_time:
            p1.kill()
            p2.kill()
            raise TimeoutError("COM audio processes could not be detected in time.")

        for session in AudioUtilities.GetAllSessions():
            if session.Process:
                if session.Process.pid == p1.pid:
                    LOCAL_PROCESSES.append(p1)
                elif session.Process.pid == p2.pid:
                    LOCAL_PROCESSES.append(p2)

    return p1, p2

def kill_local_processes():
    for process in LOCAL_PROCESSES:
        try:
            process.terminate()
            process.wait(timeout=5)
        except Exception:
            process.kill()

#########################################
# Main init
#########################################

atexit.register(kill_local_processes)

if os.environ.get("CI"):
    print("CI mode detected: Mocking Pycaw audio session functions")
    mock_audio_ci()
else:
    print("Local mode detected: Creating COM audio processes")
    mock_audio_local()