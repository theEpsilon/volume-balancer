import tkinter as tk
from tkinter import ttk
from pycaw.pycaw import AudioUtilities
import keyboard
import traceback

class AudioProcess:
    def __init__(self, session = None):
        self.session = session
        self.initial_vol = session.SimpleAudioVolume.GetMasterVolume()
    
    def get_session(self):
        return self.session

    def get_initial_volume(self):
        return self.initial_vol

    def reset_volume(self):
        try:
            self.session.SimpleAudioVolume.SetMasterVolume(self.initial_vol, None)
        except Exception:
            print(traceback.print_exc())



class VolumeBalancer:
    def __init__(self, root):
        self.root = root
        self.root.title("Volume Balancer")
        self.root.geometry("500x350")
        
        self.process1 = None
        self.process2 = None
        self.audio_sessions = {}

        self.balance_var = tk.DoubleVar(value=0.0)
        
        self.create_widgets()
        self.setup_hotkeys()
        self.refresh_processes()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        # Process 1 selection
        tk.Label(self.root, text="Audio Source 1:", font=("Arial", 10)).pack(pady=5)
        self.process1_var = tk.StringVar()
        self.process1_combo = ttk.Combobox(
            self.root, 
            textvariable=self.process1_var,
            width=40,
            state="readonly"
        )
        self.process1_combo.pack(pady=5)
        self.process1_combo.bind("<<ComboboxSelected>>", self.on_process1_selected)
        
        # Process 2 selection
        tk.Label(self.root, text="Audio Source 2:", font=("Arial", 10)).pack(pady=5)
        self.process2_var = tk.StringVar()
        self.process2_combo = ttk.Combobox(
            self.root, 
            textvariable=self.process2_var,
            width=40,
            state="readonly"
        )
        self.process2_combo.pack(pady=5)
        self.process2_combo.bind("<<ComboboxSelected>>", self.on_process2_selected)
        
        # Volume balance slider
        tk.Label(self.root, text="Volume Balance:", font=("Arial", 10)).pack(pady=10)
        
        # Create a frame to hold buttons and slider horizontally
        slider_frame = tk.Frame(self.root)
        slider_frame.pack(pady=5)
        
        tk.Label(slider_frame, text="v", font=("Arial", 10)).pack(side=tk.TOP)
        tk.Button(slider_frame, text="<<", command=lambda: self.set_balance(-1.0), height=1, width=2).pack(side=tk.LEFT, padx=5)
        self.balance_slider = tk.Scale(
            slider_frame,
            from_=-1.0,
            to=1.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.balance_var,
            command=self.set_balance,
            length=400,
            showvalue=False
        )
        self.balance_slider.pack(side=tk.LEFT, padx=5)
        tk.Button(slider_frame, text=">>", command=lambda: self.set_balance(1.0), height=1, width=2).pack(side=tk.LEFT, padx=5)
        
        # Balance labels
        balance_frame = tk.Frame(self.root)
        balance_frame.pack(pady=5)
        tk.Label(balance_frame, text="Process 1", font=("Arial", 8)).pack(side=tk.LEFT, padx=50)
        tk.Label(balance_frame, text="Balanced", font=("Arial", 8)).pack(side=tk.LEFT, padx=50)
        tk.Label(balance_frame, text="Process 2", font=("Arial", 8)).pack(side=tk.LEFT, padx=50)
        
        # Refresh button
        refresh_btn = tk.Button(
            self.root,
            text="Refresh Process List",
            command=self.refresh_processes,
            font=("Arial", 9)
        )
        refresh_btn.pack(pady=10)
        
        # Hotkey help label
        help_text = f"Global Hotkeys: Ctrl + Alt + Left/Right adjust balance | Ctrl + Shift + Left/Right/Up set extremes"

        tk.Label(self.root, text=help_text, font=("Arial", 7), fg="gray").pack(pady=5)
    
    def setup_hotkeys(self):
        keyboard.add_hotkey('ctrl+alt+left', lambda: self.set_balance(self.balance_var.get() - 0.1))
        keyboard.add_hotkey('ctrl+alt+right', lambda: self.set_balance(self.balance_var.get() + 0.1))
        keyboard.add_hotkey('ctrl+shift+left', lambda: self.set_balance(-1.0))
        keyboard.add_hotkey('ctrl+shift+right', lambda: self.set_balance(1.0))
        keyboard.add_hotkey('ctrl+shift+up', lambda: self.set_balance(0.0))
    
    def on_closing(self):
        try:
            keyboard.unhook_all()
        except:
            traceback.print_exc()
        
        if self.process1 is not None:
            self.process1.reset_volume()
        if self.process2 is not None:
            self.process2.reset_volume()

        self.root.destroy()
        
    def get_audio_processes(self):
        processes = {}
        try:
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                if session.Process:
                    audioProcess = AudioProcess(session)
                    key = self.get_readable_process_key(audioProcess)
                    if key not in processes:
                        processes[key] = audioProcess
        except Exception as e:
            print(f"Error getting audio processes: {e}")
        return processes
    
    def refresh_processes(self):
        self.audio_sessions = self.get_audio_processes()
        self.update_comboboxes()
        
    def update_comboboxes(self):
        process_list = self.audio_sessions.keys()

        self.process1_combo['values'] = [el for el in process_list if el != self.get_readable_process_key(self.process2)]
        self.process2_combo['values'] = [el for el in process_list if el != self.get_readable_process_key(self.process1)]

    def on_process1_selected(self, event=None):
        if self.process1 is not None:
            self.process1.reset_volume()

        selected = self.process1_var.get()
        if selected in self.audio_sessions:
            self.process1 = self.audio_sessions[selected]
            self.update_comboboxes()
            self.update_volumes()
    
    def on_process2_selected(self, event=None):
        selected = self.process2_var.get()

        if self.process2 is not None:
            self.process2.reset_volume()

        if selected in self.audio_sessions:
            self.process2 = self.audio_sessions[selected]
            self.update_comboboxes()
            self.update_volumes()

    def clear_process1(self):
        if self.process1:
            self.process1 = None
            self.update_volumes()

    def get_readable_process_key(self, audio_process=None):
        if audio_process is None:
            return ""
        return f"{audio_process.get_session().Process.name()} (PID: {audio_process.get_session().Process.pid})"

    def set_balance(self, value=None):
        def update():
            if value is not None:
                try:
                    float_value = max(-1.0, min(1.0, float(value)))
                    self.balance_var.set(float_value)
                except (ValueError, TypeError):
                    pass
            self.update_volumes()
        self.root.after(0, update)
    
    def update_volumes(self):
        balance = self.balance_var.get()
        
        try:
            if self.process1:
                session1 = self.process1.get_session()
                volume1 = session1.SimpleAudioVolume
                volume1.SetMasterVolume(1.0 - max(balance, 0), None)
            
            if self.process2:
                session2 = self.process2.get_session()
                volume2 = session2.SimpleAudioVolume
                volume2.SetMasterVolume(1.0 + min(balance, 0), None)
        except Exception as e:
            print(f"Error updating volumes: {e}")


def main():
    root = tk.Tk()
    app = VolumeBalancer(root)
    root.mainloop()


if __name__ == "__main__":
    main()

