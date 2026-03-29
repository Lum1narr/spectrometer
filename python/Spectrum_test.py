import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import serial
import time
import csv
import os
from datetime import datetime

# --- НАСТРОЙКИ ---
COM_PORT = 'COM8'    # ТВОЙ ПОРТ
BAUD_RATE = 9600
MAX_POINTS = 300     # Сколько точек показывать на экране одновременно
MAX_SAMPLES_TOTAL = 300 # Сколько всего измерений сделать до авто-стопа

class RealTimePlotter:
    def __init__(self, root):
        self.root = root
        self.root.title("Arduino Continuous Scanner")
        self.root.geometry("900x700")

        self.data_x = []
        self.data_y = []
        self.total_points = 0
        self.is_running = False 
        self.ser = None
        
        # Переменные для работы с CSV
        self.csv_file = None
        self.csv_writer = None

        self.connect_arduino()
        self.setup_gui()

        # График
        self.fig, self.ax = plt.subplots()
        self.fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.15)
        self.line, = self.ax.plot([], [], 'r-', lw=2)
        self.ax.set_title("Continuous Spectrum Scan")
        self.ax.set_xlabel("Sample Number")
        self.ax.set_ylabel("Intensity")
        self.ax.grid(True)
        self.ax.set_ylim(-200, 1000) 

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.ani = animation.FuncAnimation(self.fig, self.update_graph, interval=20, cache_frame_data=False)

    def connect_arduino(self):
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=0.1)
            print(f"Connected to {COM_PORT}. Waiting for reset...")
            time.sleep(2) 
            print("Ready.")
        except serial.SerialException:
            print("Connection Error!")
            self.ser = None

    def setup_gui(self):
        control_frame = ttk.Frame(self.root)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # Масштаб Y
        ttk.Label(control_frame, text="Min Y:").pack(side=tk.LEFT)
        self.entry_min = ttk.Entry(control_frame, width=8)
        self.entry_min.insert(0, "-200")
        self.entry_min.pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text="Max Y:").pack(side=tk.LEFT)
        self.entry_max = ttk.Entry(control_frame, width=8)
        self.entry_max.insert(0, "1000")
        self.entry_max.pack(side=tk.LEFT, padx=5)

        self.btn_scale = ttk.Button(control_frame, text="Set Scale", command=self.update_scale)
        self.btn_scale.pack(side=tk.LEFT, padx=10)

        # Кнопки
        self.btn_start = ttk.Button(control_frame, text="START", command=self.toggle_measurement)
        self.btn_start.pack(side=tk.RIGHT, padx=10)

        self.btn_clear = ttk.Button(control_frame, text="RESET SYSTEM", command=self.reset_system)
        self.btn_clear.pack(side=tk.RIGHT, padx=5)

    def reset_system(self):
        self.stop_measurement() # Обязательно закрываем файл перед сбросом
        self.data_x.clear()
        self.data_y.clear()
        self.total_points = 0
        self.connect_arduino() # Перезагрузка Arduino
        self.line.set_data([], [])
        self.canvas.draw()
        print("System Reset Done.")

    def stop_measurement(self):
        if self.ser and self.ser.is_open:
            self.ser.write(b'0')
            
        self.is_running = False
        self.btn_start.config(text="START")
        
        # Закрываем CSV файл при остановке
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None
            print("Data saved to CSV and measurement stopped.")

    def toggle_measurement(self):
        if not self.ser: return

        if not self.is_running:
            # --- СОЗДАНИЕ НОВОГО CSV ФАЙЛА ПРИ СТАРТЕ ---
            # Генерируем уникальное имя файла с датой и временем
            filename = datetime.now().strftime("spectrum_%Y%m%d_%H%M%S.csv")
            self.csv_file = open(filename, mode='w', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            # Записываем заголовки колонок
            self.csv_writer.writerow(["Step_Number", "Intensity"])
            
            self.ser.reset_input_buffer()
            self.ser.write(b'1')
            self.is_running = True
            self.btn_start.config(text="STOP")
            print(f"Started measurement... Logging to {filename}")
        else:
            self.stop_measurement()

    def update_scale(self):
        try:
            self.ax.set_ylim(float(self.entry_min.get()), float(self.entry_max.get()))
            self.canvas.draw()
        except ValueError: pass

    def update_graph(self, frame):
        if self.ser and self.ser.in_waiting:
            while self.ser.in_waiting > 0:
                try:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        val = float(line)
                        self.total_points += 1
                        
                        y_val = -val # Значение, которое идет на график и в файл
                        
                        # --- ЗАПИСЬ В CSV ---
                        if self.csv_writer:
                            self.csv_writer.writerow([self.total_points, y_val])
                        
                        # Авто-стоп по количеству измерений
                        if self.is_running and self.total_points >= MAX_SAMPLES_TOTAL:
                            self.stop_measurement()
                            break

                        self.data_x.append(self.total_points)
                        self.data_y.append(y_val)

                        if len(self.data_x) > MAX_POINTS:
                            self.data_x.pop(0)
                            self.data_y.pop(0)
                except ValueError: pass

            self.line.set_data(self.data_x, self.data_y)
            if self.data_x:
                last_x = self.data_x[-1]
                self.ax.set_xlim(last_x - MAX_POINTS if last_x > MAX_POINTS else 0, max(last_x, MAX_POINTS))

        return self.line,

    def on_close(self):
        self.stop_measurement() # Гарантируем закрытие файла при выходе
        if self.ser:
            self.ser.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = RealTimePlotter(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()