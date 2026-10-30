import sys
import os
import csv
import time
from datetime import datetime
import threading
import collections

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import serial
import serial.tools.list_ports

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class ConcreteTestApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("JABIASR - Concrete Compression System")
        self.geometry("1100x750")
        self.configure(bg="#f4f4f6")
        
        # --- Serial Communication State ---
        self.ser = None
        self.is_reading = False
        self.read_thread = None
        
        # --- Data Streams & Metrics Tracking ---
        self.is_testing = False
        self.time_data = collections.deque(maxlen=2000)
        self.load_data_lbf = collections.deque(maxlen=2000)
        self.start_time = 0.0
        
        self.peak_load_lbf = 0.0
        self.current_load_lbf = 0.0
        
        # Conversion Constant: 1 kN = 224.808943 lbf
        self.LBF_TO_KN = 1.0 / 224.808943
        
        # --- UI Build Layout ---
        self.create_styles()
        self.build_top_bar()
        
        # Main dynamic body split
        self.main_container = ttk.Frame(self, style="Main.TFrame")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        self.build_left_panel()
        self.build_right_panel()
        
        # Start scanning hardware loops
        self.refresh_com_ports()
        self.update_gui_loop()

    def create_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Main.TFrame", background="#f4f4f6")
        self.style.configure("Card.TFrame", background="#ffffff", relief="flat")
        self.style.configure("TLabel", background="#ffffff", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 11, "bold"), foreground="#2c3e50")
        self.style.configure("Display.TLabel", font=("Segoe UI", 24, "bold"), foreground="#16a085")
        self.style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=6)

    def build_top_bar(self):
        top_bar = tk.Frame(self, bg="#2c3e50", height=60)
        top_bar.pack(fill=tk.X, side=tk.TOP)
        top_bar.pack_propagate(False)
        
        title_lbl = tk.Label(top_bar, text="JABIASR  |  AUTOMATED COMPRESSION SYSTEM", 
                             fg="#ecf0f1", bg="#2c3e50", font=("Segoe UI", 14, "bold"))
        title_lbl.pack(side=tk.LEFT, padx=15, pady=15)
        
        self.conn_frame = tk.Frame(top_bar, bg="#2c3e50")
        self.conn_frame.pack(side=tk.RIGHT, padx=15)
        
        tk.Label(self.conn_frame, text="COM Port:", fg="#ecf0f1", bg="#2c3e50").pack(side=tk.LEFT, padx=5)
        self.com_cb = ttk.Combobox(self.conn_frame, width=10, state="readonly")
        self.com_cb.pack(side=tk.LEFT, padx=5)
        
        self.btn_connect = ttk.Button(self.conn_frame, text="Connect", command=self.toggle_connection, style="Action.TButton")
        self.btn_connect.pack(side=tk.LEFT, padx=5)
    def build_left_panel(self):
        left_panel = ttk.Frame(self.main_container, width=320, style="Main.TFrame")
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # 1. SAMPLE METADATA CARD
        meta_card = ttk.Frame(left_panel, style="Card.TFrame", padding=15)
        meta_card.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(meta_card, text="SAMPLE IDENTIFICATION", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0,10))
        
        ttk.Label(meta_card, text="Client Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.ent_client = ttk.Entry(meta_card, width=22)
        self.ent_client.grid(row=1, column=1, pady=5, sticky=tk.E)
        self.ent_client.insert(0, "General Client")
        
        ttk.Label(meta_card, text="Site / Location:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.ent_site = ttk.Entry(meta_card, width=22)
        self.ent_site.grid(row=2, column=1, pady=5, sticky=tk.E)
        self.ent_site.insert(0, "Site Alpha")
        
        ttk.Label(meta_card, text="Weight (kg):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.ent_weight = ttk.Entry(meta_card, width=22)
        self.ent_weight.grid(row=3, column=1, pady=5, sticky=tk.E)
        self.ent_weight.insert(0, "12.5")
        
        ttk.Label(meta_card, text="Batch Code:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.ent_batch = ttk.Entry(meta_card, width=22)
        self.ent_batch.grid(row=4, column=1, pady=5, sticky=tk.E)
        self.ent_batch.insert(0, "B-001")

        # 2. RUN CONTROLS CARD
        ctrl_card = ttk.Frame(left_panel, style="Card.TFrame", padding=15)
        ctrl_card.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(ctrl_card, text="TEST CONTROLS", style="Header.TLabel").pack(anchor=tk.W, pady=(0,10))
        
        unit_frame = ttk.Frame(ctrl_card, style="Card.TFrame")
        unit_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(unit_frame, text="Display Unit:").pack(side=tk.LEFT, padx=(0, 10))
        self.unit_cb = ttk.Combobox(unit_frame, values=["kn", "lbf"], width=8, state="readonly")
        self.unit_cb.pack(side=tk.LEFT)
        self.unit_cb.current(0) 
        self.unit_cb.bind("<<ComboboxSelected>>", lambda e: self.update_graph_labels())
        
        self.btn_start = ttk.Button(ctrl_card, text="START TEST RUN", command=self.send_start_command, state=tk.DISABLED, style="Action.TButton")
        self.btn_start.pack(fill=tk.X, pady=4)
        
        self.btn_stop = ttk.Button(ctrl_card, text="STOP / ABORT", command=self.send_stop_command, state=tk.DISABLED, style="Action.TButton")
        self.btn_stop.pack(fill=tk.X, pady=4)
        
        self.btn_tare = ttk.Button(ctrl_card, text="TARE SCALE", command=self.send_tare_command, state=tk.DISABLED, style="Action.TButton")
        self.btn_tare.pack(fill=tk.X, pady=4)

        # 3. LIVE MONITOR VALUE VIEWS
        val_card = ttk.Frame(left_panel, style="Card.TFrame", padding=15)
        val_card.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(val_card, text="LIVE SYSTEM METRICS", style="Header.TLabel").pack(anchor=tk.W, pady=(0,5))
        
        self.lbl_live_title = ttk.Label(val_card, text="Live Load:")
        self.lbl_live_title.pack(anchor=tk.W, pady=(5,0))
        self.lbl_live_load = ttk.Label(val_card, text="0.0", style="Display.TLabel")
        self.lbl_live_load.pack(anchor=tk.W, pady=(0,10))
        
        self.lbl_peak_title = ttk.Label(val_card, text="Peak Load Captured:")
        self.lbl_peak_title.pack(anchor=tk.W, pady=(5,0))
        self.lbl_peak_load = ttk.Label(val_card, text="0.0", font=("Segoe UI", 20, "bold"), foreground="#c0392b", background="#ffffff")
        self.lbl_peak_load.pack(anchor=tk.W)

    def build_right_panel(self):
        right_panel = ttk.Frame(self.main_container, style="Card.TFrame", padding=10)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Real-Time Load Analysis Profile")
        self.ax.set_xlabel("Elapsed Time (Seconds)")
        self.ax.set_ylabel("Applied Force (kn)")
        self.ax.grid(True, linestyle="--", alpha=0.6)
        
        self.line, = self.ax.plot([], [], color="#2980b9", linewidth=2.5, label="Load Curve")
        self.ax.legend(loc="upper left")
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_graph_labels(self):
        current_unit = self.unit_cb.get()
        self.ax.set_ylabel(f"Applied Force ({current_unit})")
        self.canvas.draw_idle()
    def refresh_com_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.com_cb["values"] = ports
        if ports:
            self.com_cb.current(0)
            
    def toggle_connection(self):
        if self.ser is None:
            selected_port = self.com_cb.get()
            if not selected_port:
                messagebox.showwarning("Port Error", "Please select a valid COM port connection.")
                return
            try:
                self.ser = serial.Serial(selected_port, 115200, timeout=1)
                self.btn_connect.config(text="Disconnect")
                self.btn_start.config(state=tk.NORMAL)
                self.btn_stop.config(state=tk.NORMAL)
                self.btn_tare.config(state=tk.NORMAL)
                
                self.is_reading = True
                self.read_thread = threading.Thread(target=self.serial_background_read, daemon=True)
                self.read_thread.start()
            except Exception as e:
                messagebox.showerror("Connection Failure", f"Could not connect to {selected_port}:\n{str(e)}")
                self.ser = None
        else:
            self.disconnect_serial()

    def disconnect_serial(self):
        self.is_reading = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.ser = None
        self.btn_connect.config(text="Connect")
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.DISABLED)
        self.btn_tare.config(state=tk.DISABLED)

    def send_start_command(self):
        if self.ser and self.ser.is_open:
            self.time_data.clear()
            self.load_data_lbf.clear()
            self.peak_load_lbf = 0.0
            self.start_time = time.time()
            self.is_testing = True
            self.ser.write(b"START\n")
            
    def send_stop_command(self):
        if self.ser and self.ser.is_open:
            self.ser.write(b"STOP\n")
            if self.is_testing:
                self.finalize_test_run()

    def send_tare_command(self):
        if self.ser and self.ser.is_open:
            self.ser.write(b"TARE\n")

    def serial_background_read(self):
        while self.is_reading:
            if self.ser and self.ser.in_waiting > 0:
                try:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line.startswith("DATA:"):
                        val_str = line.split(":")
                        val_flt = float(val_str[1])
                        self.current_load_lbf = val_flt
                        
                        if self.is_testing:
                            current_elapsed = time.time() - self.start_time
                            self.time_data.append(current_elapsed)
                            self.load_data_lbf.append(val_flt)
                            
                            if val_flt > self.peak_load_lbf:
                                self.peak_load_lbf = val_flt
                                
                            if len(self.load_data_lbf) > 10 and val_flt < (self.peak_load_lbf * 0.15) and self.peak_load_lbf > 10000:
                                self.is_testing = False
                                threading.Thread(target=self.finalize_test_run, daemon=True).start()
                except Exception:
                    pass
            else:
                time.sleep(0.01)

    def finalize_test_run(self):
        self.is_testing = False
        client = self.ent_client.get().strip() or "Unknown"
        site = self.ent_site.get().strip() or "Unknown"
        weight = self.ent_weight.get().strip() or "0"
        batch = self.ent_batch.get().strip() or "Unknown"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Fixed Target Destination: point explicitly to 'test results' folder
        log_dir = os.path.join(os.getcwd(), "test results")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        filename = f"Test_{timestamp}_{batch}.csv"
        full_save_path = os.path.join(log_dir, filename)
        
        peak_kn = self.peak_load_lbf * self.LBF_TO_KN
        try:
            with open(full_save_path, mode='w', newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["=== JABIASR COMPRESSION TEST RECORD ==="])
                writer.writerow(["Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                writer.writerow(["Client", client])
                writer.writerow(["Site / Location", site])
                writer.writerow(["Weight (kg)", weight])
                writer.writerow(["Batch Code", batch])
                writer.writerow(["Peak Load Captured (kn)", f"{peak_kn:.2f}"])
                writer.writerow(["Peak Load Captured (lbf)", f"{self.peak_load_lbf:.1f}"])
                writer.writerow([])
                writer.writerow(["Elapsed_Seconds", "Load_kn", "Load_lbf"])
                for t_val, lbf_val in zip(self.time_data, self.load_data_lbf):
                    kn_val = lbf_val * self.LBF_TO_KN
                    writer.writerow([f"{t_val:.3f}", f"{kn_val:.2f}", f"{lbf_val:.1f}"])
            messagebox.showinfo("Export Success", f"Test complete.\nData logged safely inside folder:\ntest results\\{filename}")
        except Exception as e:
            messagebox.showerror("IO Write Failure", f"Could not export log dataset:\n{str(e)}")

    def update_gui_loop(self):
        current_unit = self.unit_cb.get()
        if current_unit == "kn":
            live_display = self.current_load_lbf * self.LBF_TO_KN
            peak_display = self.peak_load_lbf * self.LBF_TO_KN
            self.lbl_live_title.config(text="Live Load (kn):")
            self.lbl_peak_title.config(text="Peak Load Captured (kn):")
            fmt = ",.2f"
        else:
            live_display = self.current_load_lbf
            peak_display = self.peak_load_lbf
            self.lbl_live_title.config(text="Live Load (lbf):")
            self.lbl_peak_title.config(text="Peak Load Captured (lbf):")
            fmt = ",.1f"
            
        self.lbl_live_load.config(text=format(live_display, fmt))
        self.lbl_peak_load.config(text=format(peak_display, fmt))
        
        if self.is_testing and len(self.time_data) > 0:
            t_list = list(self.time_data)
            if current_unit == "kn":
                y_list = [lbf * self.LBF_TO_KN for lbf in self.load_data_lbf]
                y_max_default = 1500.0
            else:
                y_list = list(self.load_data_lbf)
                y_max_default = 337213.4
            self.line.set_data(t_list, y_list)
            self.ax.set_xlim(0, max(10, max(t_list) * 1.1))
            self.ax.set_ylim(0, max(y_max_default * 0.05, max(y_list) * 1.1))
            self.canvas.draw_idle()
        self.after(50, self.update_gui_loop)

    def destroy(self):
        self.disconnect_serial()
        super().destroy()

if __name__ == "__main__":
    app = ConcreteTestApp()
    app.mainloop()
