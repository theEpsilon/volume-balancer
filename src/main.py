import tkinter as tk
import keyboard
import traceback

from tkinter import ttk
from pycaw.pycaw import AudioUtilities
from src.__version__ import __version__


class AudioProcess:
    def __init__(self, session = None):
        self.session = session
        self.initial_vol = session.SimpleAudioVolume.GetMasterVolume()
    
    def get_session(self):
        return self.session

    def get_initial_volume(self):
        return self.initial_vol

    def set_volume(self, volume):
        try:
            self.session.SimpleAudioVolume.SetMasterVolume(volume, None)
        except Exception:
            print(traceback.print_exc())

    def reset_volume(self):
        self.set_volume(self.initial_vol)

    def get_session_name(self):
        return self.session.Process.name()

    def get_session_pid(self):
        return self.session.Process.pid

    def get_readable_process_key(self):
        return f"{self.get_session_name()} (PID: {self.get_session_pid()})"



class VolumeBalancer:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Volume Balancer v{__version__}")
        self.root.geometry("500x325")
        self.root.minsize(500, 325)
        
        self.process1 = None
        self.process2 = None
        self.audio_sessions = {}

        self.balance_var = tk.DoubleVar(value=0.0)
        
        self._create_widgets()
        self.setup_hotkeys()
        self.refresh_processes()
        self.update_balance_labels()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_widgets(self):
        # Process 1 selection
        process1_frame = tk.Frame(self.root)
        process1_frame.pack(pady=(10, 5))

        tk.Label(process1_frame, text="Audio Source 1:", font=("Arial", 10)).grid(row=0, column=0, columnspan=2)

        self.process1_var = tk.StringVar()
        self.process1_combo = ttk.Combobox(
            process1_frame,
            textvariable=self.process1_var,
            width=40,
            state="readonly"
        )
        self.process1_combo.bind("<<ComboboxSelected>>", self.on_process1_selected)
        self.process1_combo.grid(row=1, column=0)
        
        self.unset1 = tk.Button(process1_frame, text="unset", command=lambda: self.clear_process1())
        self.unset1.grid(row=1, column=1, padx=(10, 0))
        
        # Process 2 selection
        process2_frame = tk.Frame(self.root)
        process2_frame.pack(pady=5)

        tk.Label(process2_frame, text="Audio Source 2:", font=("Arial", 10)).grid(row=0, column=0, columnspan=2)

        self.process2_var = tk.StringVar()
        self.process2_combo = ttk.Combobox(
            process2_frame, 
            textvariable=self.process2_var,
            width=40,
            state="readonly"
        )
        self.process2_combo.grid(row=1, column=0)
        self.process2_combo.bind("<<ComboboxSelected>>", self.on_process2_selected)

        self.unset2 = tk.Button(process2_frame, text="unset", command=lambda: self.clear_process2())
        self.unset2.grid(row=1, column=1, padx=(10, 0))
        
        # Volume Balancer
        balancer_frame = tk.Frame(self.root)
        balancer_frame.pack(pady=(20, 0))

        tk.Label(balancer_frame, text="Volume Balance:", font=("Arial", 10)).pack()
        
        ## Balance slider
        slider_frame = tk.Frame(balancer_frame)
        slider_frame.pack()
        
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
        
        ## Balance labels
        balance_label_frame = tk.Frame(balancer_frame)
        balance_label_frame.pack(fill=tk.X, expand=True, padx=40)
        
        self.process1_label = tk.Label(balance_label_frame, text="Process 1", font=("Arial", 8))
        self.process1_label.pack(side=tk.LEFT)
        
        tk.Label(balance_label_frame, text="Balanced", font=("Arial", 8)).place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        self.process2_label = tk.Label(balance_label_frame, text="Process 2", font=("Arial", 8))
        self.process2_label.pack(side=tk.RIGHT)
        
        # Refresh button
        refresh_btn = tk.Button(
            self.root,
            text="Refresh Process List",
            command=self.refresh_processes,
            font=("Arial", 9)
        )
        refresh_btn.pack(pady=(25, 5))
        
        # Hotkey help label
        help_text = f"Hotkeys: Ctrl + Alt + Left/Right adjust balance | Ctrl + Shift + Left/Right/Down set extremes"
        tk.Label(self.root, text=help_text, font=("Arial", 7), fg="gray").pack(pady=5)
    
    def setup_hotkeys(self):
        keyboard.add_hotkey('ctrl+alt+left', lambda: self.set_balance(self.balance_var.get() - 0.1))
        keyboard.add_hotkey('ctrl+alt+right', lambda: self.set_balance(self.balance_var.get() + 0.1))
        keyboard.add_hotkey('ctrl+shift+left', lambda: self.set_balance(-1.0))
        keyboard.add_hotkey('ctrl+shift+right', lambda: self.set_balance(1.0))
        keyboard.add_hotkey('ctrl+shift+down', lambda: self.set_balance(0.0))
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
                    key = audioProcess.get_readable_process_key()
                    if key not in processes:
                        processes[key] = audioProcess
        except Exception as e:
            print(f"Error getting audio processes: {e}")
        return processes
    
    def refresh_processes(self):
        self.audio_sessions = self.get_audio_processes()
        self.update_combobox_values()
        
    def update_combobox_values(self):
        process_list = self.audio_sessions.keys()
        key1, key2 = "", ""

        if self.process1:
            key1 = self.process1.get_readable_process_key()
        if self.process2:
            key2 = self.process2.get_readable_process_key()

        self.process1_combo['values'] = [el for el in process_list if el != key2]
        self.process2_combo['values'] = [el for el in process_list if el != key1]
    
    def update_balance_labels(self):
        process1_name = self.process1.get_session_name() if self.process1 else "None selected"
        process2_name = self.process2.get_session_name() if self.process2 else "None selected"

        if len(process1_name) > 20:
            process1_name = f"{process1_name[:20]}..."

        if len(process2_name) > 20:
            process2_name = f"{process2_name[:20]}..."

        self.process1_label.config(text=process1_name)
        self.process2_label.config(text=process2_name)

    def on_process1_selected(self, event=None):
        if self.process1 is not None:
            self.process1.reset_volume()

        selected = self.process1_var.get()
        if selected in self.audio_sessions:
            self.process1 = self.audio_sessions[selected]
            self.update_combobox_values()
            self.update_balance_labels()
            self.update_volumes()
    
    def on_process2_selected(self, event=None):
        selected = self.process2_var.get()

        if self.process2 is not None:
            self.process2.reset_volume()

        if selected in self.audio_sessions:
            self.process2 = self.audio_sessions[selected]
            self.update_combobox_values()
            self.update_balance_labels()
            self.update_volumes()

    def clear_process1(self):
        if self.process1:
            self.process1_var.set("")
            self.process1.reset_volume()
            self.process1 = None
            self.update_balance_labels()
            self.update_combobox_values()

    def clear_process2(self):
        if self.process2:
            self.process2_var.set("")
            self.process2.reset_volume()
            self.process2 = None
            self.update_balance_labels()
            self.update_combobox_values()

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

        if self.process1:
            self.process1.set_volume(1.0 - max(balance, 0))
        
        if self.process2:
            self.process2.set_volume(1.0 + min(balance, 0))

def main():
    root = tk.Tk()
    VolumeBalancer(root)
    root.iconbitmap("./app.ico")
    root.mainloop()


if __name__ == "__main__":
    main()

