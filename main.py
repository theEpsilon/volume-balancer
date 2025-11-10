import tkinter as tk
from tkinter import ttk
from pycaw.pycaw import AudioUtilities


class VolumeBalancer:
    def __init__(self, root):
        self.root = root
        self.root.title("Volume Balancer")
        self.root.geometry("500x300")
        
        self.process1 = None
        self.process2 = None
        self.audio_sessions = {}

        self.balance_var = tk.DoubleVar(value=0.0)
        
        self.create_widgets()
        self.refresh_processes()
        
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
        
    def get_audio_processes(self):
        """Get list of processes with audio sessions"""
        processes = {}
        try:
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                if session.Process:
                    process_name = session.Process.name()
                    pid = session.Process.pid
                    key = f"{process_name} (PID: {pid})"
                    if key not in processes:
                        processes[key] = {
                            'name': process_name,
                            'pid': pid,
                            'session': session
                        }
        except Exception as e:
            print(f"Error getting audio processes: {e}")
        return processes
    
    def refresh_processes(self):
        """Refresh the process list in dropdowns"""
        processes = self.get_audio_processes()
        process_list = sorted(processes.keys())
        
        # Update comboboxes
        self.process1_combo['values'] = process_list
        self.process2_combo['values'] = process_list
        
        # Store audio sessions
        self.audio_sessions = processes
        
    def on_process1_selected(self, event=None):
        """Handle Process 1 selection"""
        selected = self.process1_var.get()
        if selected in self.audio_sessions:
            self.process1 = self.audio_sessions[selected]
            self.update_volumes()
    
    def on_process2_selected(self, event=None):
        """Handle Process 2 selection"""
        selected = self.process2_var.get()
        if selected in self.audio_sessions:
            self.process2 = self.audio_sessions[selected]
            self.update_volumes()

    def clear_process1(self):
        if self.process1:
            self.process1 = None
            self.update_volumes()

    def set_balance(self, value=None):
        if value is not None:
            try:
                float_value = float(value)
                self.balance_var.set(float_value)
            except (ValueError, TypeError):
                pass
        self.update_volumes()
    
    def update_volumes(self):
        """Update volumes based on balance slider"""
        balance = self.balance_var.get()
        
        try:

            if self.process1:
                session1 = self.process1['session']
                volume1 = session1.SimpleAudioVolume
                volume1.SetMasterVolume(1.0 - max(balance, 0), None)
            
            if self.process2:
                session2 = self.process2['session']
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

