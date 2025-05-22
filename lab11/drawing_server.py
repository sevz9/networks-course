import socket
import tkinter as tk
import threading
import json
import sys

class DrawingServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.clients = []
        

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        

        self.root = tk.Tk()
        self.root.title("Удаленное рисование - Сервер")
        self.root.geometry("800x600")
        
   
        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        

        self.status_label = tk.Label(self.root, text=f"Сервер запущен на {self.host}:{self.port}")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        

        self.accept_thread = threading.Thread(target=self.accept_connections)
        self.accept_thread.daemon = True
        self.accept_thread.start()
        

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        print(f"Сервер запущен на {self.host}:{self.port}")
    
    def accept_connections(self):
        """Принимает подключения от клиентов"""
        try:
            while True:
                client_socket, address = self.server_socket.accept()
                print(f"Новое подключение от {address}")
                
             
                self.clients.append(client_socket)
                
               
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Подключен клиент: {address}. Всего клиентов: {len(self.clients)}"
                ))
                
               
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except Exception as e:
            print(f"Ошибка при приеме подключений: {e}")
    
    def handle_client(self, client_socket, address):
        """Обрабатывает сообщения от клиента"""
        try:
            buffer = ""
            while True:
              
                chunk = client_socket.recv(4096).decode('utf-8')
                if not chunk:
                    break
                
               
                buffer += chunk
                
              
                while True:
                    try:
                        
                        json_end = buffer.find("}\n")
                        if json_end == -1:
                            break
                        
                      
                        json_str = buffer[:json_end+1]
                        buffer = buffer[json_end+2:]  
                        
                
                        self.process_drawing_data(json_str)
                    except Exception as e:
                        print(f"Ошибка при обработке JSON: {e}")
            
                        buffer = ""
                        break
                
        except ConnectionResetError:
            print(f"Клиент {address} отключился")
        except Exception as e:
            print(f"Ошибка при обработке сообщений от клиента {address}: {e}")
        finally:
   
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            client_socket.close()
            

            self.root.after(0, lambda: self.status_label.config(
                text=f"Клиент {address} отключился. Всего клиентов: {len(self.clients)}"
            ))
    
    def process_drawing_data(self, data_str):
        """Обрабатывает данные о рисовании"""
        try:

            drawing_data = json.loads(data_str)
            command = drawing_data.get('command')
            
            if command == 'draw':
     
                x1 = drawing_data.get('x1')
                y1 = drawing_data.get('y1')
                x2 = drawing_data.get('x2')
                y2 = drawing_data.get('y2')
                color = drawing_data.get('color', '#000000')
                width = drawing_data.get('width', 2)
                

                self.root.after(0, lambda: self.draw_line(x1, y1, x2, y2, color, width))
            
            elif command == 'clear':
 
                self.root.after(0, lambda: self.canvas.delete("all"))
                
        except json.JSONDecodeError as e:
            print(f"Ошибка при декодировании JSON: {e}")
        except Exception as e:
            print(f"Ошибка при обработке данных о рисовании: {e}")
    
    def draw_line(self, x1, y1, x2, y2, color, width):
        """Рисует линию на холсте"""
        self.canvas.create_line(
            x1, y1, x2, y2, 
            fill=color, 
            width=width, 
            smooth=True, 
            capstyle=tk.ROUND
        )
    
    def on_closing(self):
        """Обработчик закрытия окна"""
        try:
        
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
            
        
            self.server_socket.close()
            
        except Exception as e:
            print(f"Ошибка при закрытии сервера: {e}")
        finally:
            self.root.destroy()
            sys.exit(0)
    
    def start(self):
        """Запускает главный цикл GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    server = DrawingServer(port=port)
    server.start()
