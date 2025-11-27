import time
import unittest
import tkinter as tk
import re

from src.main import VolumeBalancer
from src.__version__ import __version__

def setup():
    root = tk.Tk()
    root.withdraw()
    app = VolumeBalancer(root)

    return root, app

def teardown(root):
    root.destroy()

def _get_python_processes(all_values):
    return [{"val": v, "pid": re.search(r"PID:\s*(\d+)", v).group(1)} for v in all_values if re.search(r"^python\.exe.*", v)]


class GUIBaseTest(unittest.TestCase):
    def setUp(self):
        self.root, self.app = setup()

    def tearDown(self):
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
        self.root.update()

        self.assertIsNotNone(self.app.process1)
        self.assertEqual(self.app.process1_label.cget("text"), "python.exe")

        p2 = _get_python_processes(self.app.process2_combo["values"])

        self.assertEqual(len(p2), initial_length_p2 - 1)
        self.assertNotIn(p1[0]["val"], [v["val"] for v in p2])

        # Select other value and check first combobox
        self.app.process2_combo.set(p2[0]["val"])
        self.app.process2_combo.event_generate("<<ComboboxSelected>>")
        self.root.update()

        self.assertIsNotNone(self.app.process2)
        self.assertEqual(self.app.process2_label.cget("text"), "python.exe")

        p1 = _get_python_processes(self.app.process1_combo["values"])

        self.assertEqual(len(p1), initial_length_p1 - 1)
        self.assertNotIn(p2[0]["val"], [v["val"] for v in p1])

        # Clear combobox 1 and check combobox 2 values
        self.app.unset1.invoke()
        self.root.update()
        self.assertEqual(self.app.process1_combo.get(), "")

        p2 = _get_python_processes(self.app.process2_combo["values"])

        self.assertEqual(initial_length_p2, len(p2))

        # Clear combobox 2 and check combobox 1 values
        self.app.unset2.invoke()
        self.root.update()
        self.assertEqual(self.app.process2_combo.get(), "")

        p1 = _get_python_processes(self.app.process1_combo["values"])

        self.assertEqual(initial_length_p1, len(p1))
        self.assertIsNone(self.app.process1)
        self.assertIsNone(self.app.process2)
        self.assertEqual(self.app.process1_label.cget("text"), "None selected")
        self.assertEqual(self.app.process2_label.cget("text"), "None selected")

    def test_balance_slider(self):
        p1 = _get_python_processes(self.app.process1_combo["values"])

        self.app.process1_combo.set(p1[0]["val"])
        self.app.process1_combo.event_generate("<<ComboboxSelected>>")
        self.app.balance_slider.set(-0.5)
        self.root.update()

        self.assertIsNotNone(self.app.process1)
        self.assertEqual(self.app.process1.get_volume(), 1)

        p2 = _get_python_processes(self.app.process2_combo["values"])

        self.app.process2_combo.set(p2[0]["val"])
        self.app.process2_combo.event_generate("<<ComboboxSelected>>")
        self.root.update()

        self.assertIsNotNone(self.app.process2)
        self.assertEqual(self.app.process2.get_volume(), 0.5)
        
        self.app.balance_slider.set(0.5)
        self.root.update()

        self.assertEqual(self.app.process1.get_volume(), 0.5)
        self.assertEqual(self.app.process2.get_volume(), 1)


    # Regular workflow
    # Only one source selected
    # Hotkeys
    # Unset
    # Refresh

if __name__ == "__main__":
    unittest.main()