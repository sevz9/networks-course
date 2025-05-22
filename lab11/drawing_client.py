import socket
import tkinter as tk
from tkinter import colorchooser, messagebox
import json
import sys
import threading

class DrawingClient:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.is_drawing = False
        self.last_x = 0
        self.last_y = 0
        self.color = "#000000" 
        self.brush_width = 2    
        self.connected = False
        
       
        self.root = tk.Tk()
        self.root.title("Удаленное рисование - Клиент")
        self.root.geometry("800x600")
        

        self.tools_frame = tk.Frame(self.root)
        self.tools_frame.pack(side=tk.TOP, fill=tk.X)
        

        self.color_button = tk.Button(self.tools_frame, text="Выбрать цвет", command=self.choose_color)
        self.color_button.pack(side=tk.LEFT, padx=5, pady=5)
        

        self.color_display = tk.Canvas(self.tools_frame, width=30, height=30, bg=self.color)
        self.color_display.pack(side=tk.LEFT, padx=5, pady=5)
        

        tk.Label(self.tools_frame, text="Толщина:").pack(side=tk.LEFT, padx=5)
        self.width_slider = tk.Scale(self.tools_frame, from_=1, to=10, orient=tk.HORIZONTAL, 
                                     command=self.change_width)
        self.width_slider.set(self.brush_width)
        self.width_slider.pack(side=tk.LEFT, padx=5)
        

        self.clear_button = tk.Button(self.tools_frame, text="Очистить холст", command=self.clear_canvas)
        self.clear_button.pack(side=tk.RIGHT, padx=5, pady=5)
        

        self.connect_button = tk.Button(self.tools_frame, text="Подключиться", command=self.connect_to_server)
        self.connect_button.pack(side=tk.RIGHT, padx=5, pady=5)
        

        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        

        self.status_label = tk.Label(self.root, text="Не подключен")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        

        self.canvas.bind("<Button-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)
        

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def connect_to_server(self):
        """Подключается к серверу"""
        try:

            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.connected = True
            self.status_label.config(text=f"Подключен к серверу {self.host}:{self.port}")
            self.connect_button.config(text="Переподключиться")
            
        except ConnectionRefusedError:
            self.status_label.config(text="Ошибка: Сервер не найден")
            messagebox.showerror("Ошибка подключения", 
                                "Не удалось подключиться к серверу. Убедитесь, что сервер запущен.")
        except Exception as e:
            self.status_label.config(text=f"Ошибка подключения: {e}")
            messagebox.showerror("Ошибка", f"Ошибка при подключении: {e}")
    
    def choose_color(self):
        """Открывает диалог выбора цвета"""
        color = colorchooser.askcolor(initialcolor=self.color)[1]
        if color:
            self.color = color
            self.color_display.config(bg=color)
    
    def change_width(self, value):
        """Изменяет толщину кисти"""
        self.brush_width = int(value)
    
    def start_drawing(self, event):
        """Начинает процесс рисования"""
        self.is_drawing = True
        self.last_x = event.x
        self.last_y = event.y
    
    def draw(self, event):
        """Рисует линию при движении мыши"""
        if self.is_drawing:

            self.canvas.create_line(
                self.last_x, self.last_y, event.x, event.y, 
                fill=self.color, width=self.brush_width, 
                smooth=True, capstyle=tk.ROUND
            )

            if self.connected:
                self.send_drawing_data('draw', self.last_x, self.last_y, event.x, event.y)
            

            self.last_x = event.x
            self.last_y = event.y
    
    def stop_drawing(self, event):
        """Останавливает процесс рисования"""
        self.is_drawing = False
    
    def clear_canvas(self):
        """Очищает холст"""
        self.canvas.delete("all")
        if self.connected:
            self.send_drawing_data('clear')
    
    def send_drawing_data(self, command, x1=0, y1=0, x2=0, y2=0):
        """Отправляет данные о рисовании на сервер"""
        if not self.connected:
            return
        
        try:

            data = {
                'command': command,
                'x1': x1,
                'y1': y1,
                'x2': x2,
                'y2': y2,
                'color': self.color,
                'width': self.brush_width
            }
            
   
            json_data = json.dumps(data)
            self.client_socket.send((json_data + "\n").encode('utf-8'))
            
        except ConnectionResetError:
            self.handle_disconnection()
        except BrokenPipeError:
            self.handle_disconnection()
        except Exception as e:
            print(f"Ошибка при отправке данных: {e}")
            self.status_label.config(text=f"Ошибка: {e}")
    
    def handle_disconnection(self):
        """Обрабатывает отключение от сервера"""
        self.connected = False
        self.status_label.config(text="Соединение с сервером потеряно")
        self.connect_button.config(text="Подключиться")
        messagebox.showwarning("Ошибка соединения", "Соединение с сервером потеряно")
    
    def on_closing(self):
        """Обработчик закрытия окна"""
        if self.connected:
            try:
                self.client_socket.close()
            except:
                pass
        self.root.destroy()
        sys.exit(0)
    
    def start(self):
        """Запускает главный цикл GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    
    client = DrawingClient(host, port)
    client.start()
