import subprocess
import threading
from datetime import datetime
import re
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time
import queue

DEBUG_LOG = "stm32_programmer_debug.log"
startup_flags = 0
IMPORTANT_LINES = {
    "Memory Programming ...": "Memory Programming",
    "Erasing memory corresponding to sector": "Erasing Memory",
    "Download in Progress:": "Flashing",
    "File download complete": "Flashing Completed",
    "Time elapsed during download operation": "",
    "Verifying ...": "Verifying",
    "Download verified successfully": "Verified Successfully"
}
device_widgets = {
    'refresh_btn': None
}
flashing_stlinks = set()
start_times = {}

def log_debug(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DEBUG_LOG, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def detect_stlinks():
    global startup_flags
    log_debug("Starting ST-Link detection")
    try:
        result = subprocess.run(
            ["STM32_Programmer_CLI", "-l"],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=startup_flags
        )
        log_debug(f"Detection output:\n{result.stdout}")

        detected = {}
        current_probe = {}
        lines = result.stdout.splitlines()

        for line in lines:
            if "ST-Link Probe" in line:
                if "sn" in current_probe:
                    detected[current_probe["sn"]] = current_probe
                current_probe = {"status": "Disconnected", "device": "No target detected"}
            elif "ST-LINK SN" in line:
                current_probe["sn"] = line.split(":")[1].strip()
            elif "Access Port Number" in line:
                current_probe["ap"] = line.split(":")[1].strip()

        if "sn" in current_probe:
            detected[current_probe["sn"]] = current_probe

        for sn, probe in detected.items():
            if sn in flashing_stlinks:
                probe["status"] = "Flashing"
                continue
            try:
                check_cmd = ["STM32_Programmer_CLI", "-c", "port=SWD", f"sn={sn}", "-ob", "displ"]
                result = subprocess.run(
                    check_cmd,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=startup_flags
                )
                if "Device ID" in result.stdout:
                    probe["status"] = "Connected"
                    device_id = re.search(r"Device ID\s*:\s*(0x[0-9A-Fa-f]+)", result.stdout)
                    if device_id:
                        probe["device_id"] = device_id.group(1)
            except Exception as e:
                log_debug(f"Connection check failed for {sn}: {str(e)}")

        return list(detected.values())
    except Exception as e:
        log_debug(f"Detection failed: {str(e)}")
        return []

def program_device_gui(stlink, firmware_path, loader_path, status_queue):
    sn = stlink["sn"]
    flashing_stlinks.add(sn)
    start_times[sn] = datetime.now()
    log_debug(f"Starting programming for {sn}")
    
    time_update_thread = threading.Thread(
        target=update_time_continuously,
        args=(sn, status_queue),
        daemon=True
    )
    time_update_thread.start()
    
    try:
        cmd = [
            "STM32_Programmer_CLI",
            "-c", "port=SWD",
            "freq=4000",
            f"sn={sn}",
            "mode=Normal",
            "ap=1",
            "speed=Reliable",
            "-w", firmware_path,
            "-v",
            "-el", loader_path,
            "-rst"
        ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=startup_flags
        )

        for line in process.stdout:
            log_debug(f"{sn[-4:]}: {line.strip()}")
            for key, label in IMPORTANT_LINES.items():
                if key in line and label:
                    status_queue.put((sn, label))
                    break

        process.wait()
        if process.returncode == 0:
            status_queue.put((sn, "✅ Completed"))
        else:
            status_queue.put((sn, "❌ Failed"))

    except Exception as e:
        status_queue.put((sn, f"❌ Error: {str(e)}"))
    finally:
        flashing_stlinks.discard(sn)

def update_time_continuously(sn, status_queue):
    while sn in flashing_stlinks:
        elapsed = (datetime.now() - start_times[sn]).total_seconds()
        status_queue.put((sn, f"TIME_UPDATE:{elapsed:.1f}"))
        time.sleep(0.2)

def launch_gui():
    root = tk.Tk()
    root.title("STM32 Flasher Wizard")
    root.geometry("660x500")

    status_queue = queue.Queue()
    device_widgets = {}

    firmware_path = tk.StringVar()
    firmware_display = tk.StringVar(value="No file selected")
    loader_path = tk.StringVar()
    loader_display = tk.StringVar(value="No file selected")

    frame_firmware = ttk.Frame(root)
    frame_device = ttk.Frame(root)

    def browse_firmware():
        path = filedialog.askopenfilename(filetypes=[("HEX files", "*.hex"), ("All files", "*.*")])
        if path:
            firmware_path.set(path)
            firmware_display.set(os.path.basename(path))

    def browse_loader():
        path = filedialog.askopenfilename(filetypes=[("Loader files", "*.stldr"), ("All files", "*.*")])
        if path:
            loader_path.set(path)
            loader_display.set(os.path.basename(path))

    def show_device_page():
        if not firmware_path.get():
            messagebox.showwarning("Warning", "Please select a firmware file")
            return
        if not loader_path.get():
            messagebox.showwarning("Warning", "Please select a loader file")
            return
            
        frame_firmware.pack_forget()
        frame_device.pack(fill='both', expand=True)
        refresh_devices()

    def refresh_devices():
        try:
            for widget in device_frame.winfo_children():
                widget.destroy()

            top_frame = ttk.Frame(device_frame)
            top_frame.grid(row=0, column=0, columnspan=5, sticky='ew', pady=5)

            ttk.Label(top_frame, 
                    text=f"Firmware: {firmware_display.get()}", 
                    font=('TkDefaultFont', 10)).pack(side='left', padx=5)

            refresh_btn = ttk.Button(top_frame, text="Refresh ST-Links", command=refresh_devices)
            refresh_btn.pack(side='right', padx=5)
            device_widgets['refresh_btn'] = refresh_btn

            for col in range(5):
                device_frame.grid_columnconfigure(col, weight=1)

            headers = ["ST-Link Serial", "Device ID", "Status", "Time", "Action"]
            for col, text in enumerate(headers):
                ttk.Label(device_frame, text=text, font=('TkDefaultFont', 10, 'bold'))\
                .grid(row=1, column=col, padx=15, pady=5, sticky='ew') 

            devices = detect_stlinks()
            
            for row, dev in enumerate(devices, start=2):
                sn = dev.get('sn', 'N/A')
                device_id = dev.get('device_id', 'No target')
                
                ttk.Label(device_frame, text=sn).grid(row=row, column=0, sticky='ew', padx=15)
                ttk.Label(device_frame, text=device_id).grid(row=row, column=1, sticky='ew', padx=15)
                
                status_var = tk.StringVar()
                time_var = tk.StringVar()
                
                if sn in flashing_stlinks:
                    status = "Flashing..."
                    color = "blue"
                    btn_state = "disabled"
                elif dev['status'] == "Connected":
                    status = "Ready"
                    color = "green"
                    btn_state = "normal"
                else:
                    status = "Not Connected"
                    color = "gray"
                    btn_state = "disabled"
                
                status_var.set(status)
                time_var.set("0:00" if status == "Flashing..." else "--:--")
                
                status_label = ttk.Label(device_frame, textvariable=status_var, foreground=color)
                status_label.grid(row=row, column=2, sticky='ew', padx=15)
                
                ttk.Label(device_frame, textvariable=time_var).grid(row=row, column=3, sticky='ew', padx=15)
                
                btn = ttk.Button(device_frame, text="Upload", state=btn_state,
                            command=lambda d=dev: upload_device(d))
                btn.grid(row=row, column=4, sticky='ew', padx=15)
                
                device_widgets[sn] = {
                    'var': status_var,
                    'label': status_label,
                    'btn': btn,
                    'dev': dev,
                    'time_var': time_var
                }

        except Exception as e:
            log_debug(f"Error in refresh_devices: {str(e)}")
            messagebox.showerror("Error", f"Failed to refresh devices: {str(e)}")

    def upload_device(dev):
        try:
            sn = dev['sn']
            if not firmware_path.get() or sn in flashing_stlinks:
                return
            
            if sn not in device_widgets:
                log_debug(f"Device {sn} not found in device_widgets")
                return
                
            widgets = device_widgets[sn]
            
            if device_widgets.get('refresh_btn'):
                device_widgets['refresh_btn'].config(state='disabled')
                
            widgets['var'].set("Flashing...")
            widgets['time_var'].set("0:00")
            widgets['label'].config(foreground="blue")
            widgets['btn'].config(state="disabled")
            
            threading.Thread(
                target=program_device_gui, 
                args=(dev, firmware_path.get(), loader_path.get(), status_queue),
                daemon=True
            ).start()
            
        except Exception as e:
            log_debug(f"Error in upload_device: {str(e)}")
            messagebox.showerror("Error", f"Upload failed: {str(e)}")

    def update_gui():
        try:
            while True:
                sn, update = status_queue.get_nowait()
                if sn in device_widgets:
                    widgets = device_widgets[sn]
                    
                    if update.startswith("TIME_UPDATE:"):
                        widgets['time_var'].set(update.split(":")[1] + "s")
                    else:
                        widgets['var'].set(update)
                        if "✅" in update or "❌" in update:
                            color = "green" if "✅" in update else "red"
                            widgets['label'].config(foreground=color)
                            widgets['btn'].config(state="normal")
                            
                            if not flashing_stlinks and device_widgets.get('refresh_btn'):
                                device_widgets['refresh_btn'].config(state='normal')
                        else:
                            widgets['label'].config(foreground="blue")
        except queue.Empty:
            pass
        root.after(200, update_gui)

    frame_firmware.pack(fill='both', expand=True, padx=20, pady=20)
    
    firmware_box = ttk.LabelFrame(frame_firmware, text="Firmware Selection", padding=10)
    firmware_box.pack(fill='x', padx=5, pady=5)
    
    ttk.Label(firmware_box, text="Select HEX File:").pack(pady=5)
    ttk.Button(firmware_box, text="Browse", command=browse_firmware).pack(pady=5)
    ttk.Label(firmware_box, textvariable=firmware_display, wraplength=400).pack(pady=5)
    
    loader_box = ttk.LabelFrame(frame_firmware, text="Loader Selection", padding=10)
    loader_box.pack(fill='x', padx=5, pady=5)
    
    ttk.Label(loader_box, text="Select Loader File:").pack(pady=5)
    ttk.Button(loader_box, text="Browse", command=browse_loader).pack(pady=5)
    ttk.Label(loader_box, textvariable=loader_display, wraplength=400).pack(pady=5)
    
    ttk.Button(frame_firmware, text="Next ➡", command=show_device_page).pack(pady=20)

    device_frame = ttk.Frame(frame_device)
    device_frame.pack(fill='both', expand=True, padx=20, pady=10)

    update_gui()
    root.mainloop()

if __name__ == '__main__':
    if os.name == 'nt':
        startup_flags = subprocess.CREATE_NO_WINDOW 
    with open(DEBUG_LOG, "w") as f:
        f.write(f"STM32 Programmer Debug Log - {datetime.now()}\n\n")
    launch_gui()
