import subprocess
import time
from typing import Literal

from pycaw.pycaw import AudioUtilities
from unittest.mock import patch, MagicMock

class AudioSessionFactory:

    MODE = Literal["local", "ci"]

    def __init__(self, run_mode: MODE = "ci"):
        self.mode = run_mode
        self._PROCESSES = []

    def set_mode(self, run_mode: MODE):
        self.mode = run_mode

    def init_processes(self):
        if self.mode == "local":
            for _ in range(2):
                p = self._spawn_subprocess()
                self._PROCESSES.append(p)
        else:
            self._PROCESSES = [
                self.MockAudioSession("python.exe", 69420),
                self.MockAudioSession("python.exe", 6767)
            ]
            self._init_ci_mock()
        
        return self._PROCESSES

    def spawn_session(self, name = "python.exe", pid = 1000):
        if self.mode == "local":
            p = self._spawn_subprocess()
        else:
            p = self.MockAudioSession(name, pid)

        self._PROCESSES.append(p)
        return p
            

    def kill_sessions(self):
        if self.mode == "local":
            for process in self._PROCESSES:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except Exception:
                    process.kill()


    #########################################
    # audio mocking for CI runners
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
        

    def _init_ci_mock(self):
        patch(
            "pycaw.utils.AudioUtilities.GetAllSessions",
            return_value = self._PROCESSES
        ).start()

        patch(
            "pycaw.utils.AudioUtilities.GetAudioSessionManager",
            return_value=MagicMock()
        ).start()

        patch(
            "pycaw.utils.AudioUtilities.GetSpeakers",
            return_value=MagicMock()
        ).start()

    def add_audio_process_ci(self, name = "python.exe", pid = 1000):
        self._MOCK_PROCESSES.append(self.MockAudioSession(name, pid))
        patcher_sessions = patch(
            "pycaw.utils.AudioUtilities.GetAllSessions",
            return_value = self._MOCK_PROCESSES
        )
        patcher_sessions.start()

        return patcher_sessions

    #########################################
    # audio for local testing
    #########################################

    def _spawn_subprocess(self):
        p = subprocess.Popen(["python", "test/mock_subprocess.py"])

        start_time = time.time()
        max_wait_time = 10
        has_process_started = False

        while not has_process_started:
            time.sleep(1)

            if time.time() - start_time > max_wait_time:
                p.kill()
                raise TimeoutError("COM audio processe could not be detected in time.")

            for session in AudioUtilities.GetAllSessions():
                if session.Process:
                    if session.Process.pid == p.pid:
                        has_process_started = True
        return p