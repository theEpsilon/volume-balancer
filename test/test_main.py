import unittest
import tkinter as tk
import subprocess
import time
import re

from pycaw.pycaw import AudioUtilities
from src.main import VolumeBalancer
from src.__version__ import __version__

def setup():
    root = tk.Tk()
    root.withdraw()
    app = VolumeBalancer(root)

    return root, app

def teardown(root):
    root.destroy()

def create_mock_audio_sessions():
    p1 = subprocess.Popen(["python", "test/mock_sound.py"])
    p2 = subprocess.Popen(["python", "test/mock_sound.py"])

    p1_ready = False
    p2_ready = False
    start_time = time.time()
    max_wait_time = 10

    while (not p1_ready and not p2_ready):
        time.sleep(1)

        if time.time() - start_time > max_wait_time:
            p1.kill()
            p2.kill()
            raise TimeoutError("Mock audio processes could not be detected in time.")

        for session in AudioUtilities.GetAllSessions():
            if session.Process:
                if session.Process.pid == p1.pid:
                    p1_ready = True
                elif session.Process.pid == p2.pid:
                    p2_ready = True

    return p1, p2

def terminate_audio_sessions(p1: subprocess, p2: subprocess):
    p1.terminate()
    p2.terminate()

    p1.wait()
    p2.wait()

def _get_python_processes(all_values):
    return [{"val": v, "pid": re.search(r"PID:\s*(\d+)", v).group(1)} for v in all_values if re.search(r"^python\.exe.*", v)]


class GUIBaseTest(unittest.TestCase):
    def setUp(self):
        self.p1, self.p2 = create_mock_audio_sessions()
        self.root, self.app = setup()

    def tearDown(self):
        terminate_audio_sessions(self.p1, self.p2)
        teardown(self.root)

    def test_title(self):
        self.assertEqual(self.root.title(), f"Volume Balancer v{__version__}")

    def test_process_selection(self):
        # Get initial values
        v1, v2 = self.app.process1_combo["values"], self.app.process2_combo["values"]
        p1, p2 = _get_python_processes(v1), _get_python_processes(v2)

        self.assertEqual(len(p1), len(p2))
        self.assertGreaterEqual(len(p1), 2)

        initial_length_p1 = len(p1)
        initial_length_p2 = len(p2)
        
        # Select one process and check other combobox values
        self.app.process1_combo.set(p1[0]["val"])
        self.app.process1_combo.event_generate("<<ComboboxSelected>>")

        p2 = _get_python_processes(self.app.process2_combo["values"])

        self.assertEqual(len(p2), initial_length_p2 - 1)
        self.assertNotIn(p1[0]["val"], [v["val"] for v in p2])

        # Select other value and check first combobox
        self.app.process2_combo.set(p2[0]["val"])
        self.app.process2_combo.event_generate("<<ComboboxSelected>>")

        p1 = _get_python_processes(self.app.process1_combo["values"])

        self.assertEqual(len(p1), initial_length_p1 - 1)
        self.assertNotIn(p2[0]["val"], [v["val"] for v in p1])

        # Clear combobox 1 and check combobox 2 values
        self.app.unset1.invoke()
        self.assertEqual(self.app.process1_combo.get(), "")

        p2 = _get_python_processes(self.app.process2_combo["values"])

        self.assertEqual(initial_length_p2, len(p2))

        # Clear combobox 2 and check combobox 1 values
        self.app.unset2.invoke()
        self.assertEqual(self.app.process2_combo.get(), "")

        p1 = _get_python_processes(self.app.process1_combo["values"])

        self.assertEqual(initial_length_p1, len(p1))


    # Regular workflow
    # Only one source selected
    # Hotkeys
    # Unset
    # Refresh

if __name__ == "__main__":
    unittest.main()