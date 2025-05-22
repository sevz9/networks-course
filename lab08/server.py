# server.py
import socket
import os
import sys
from common import Packet, PACKET_TYPE_DATA, PACKET_TYPE_ACK, simulate_packet_loss

class StopAndWaitServer:
    def __init__(self, host='localhost', port=12345, loss_rate=0.3, output_dir='received_files'):
        self.host = host
        self.port = port
        self.loss_rate = loss_rate
        self.output_dir = output_dir
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((host, port))
        print(f"Сервер запущен на {host}:{port}")
    
    def send_ack(self, seq_num, addr):
        """Отправляет ACK-пакет"""
        ack_packet = Packet(PACKET_TYPE_ACK, seq_num)
        if not simulate_packet_loss(self.loss_rate):
            self.socket.sendto(ack_packet.to_bytes(), addr)
            print(f"Отправлен ACK {seq_num}")
        else:
            print(f"ACK {seq_num} потерян (симуляция)")
    
    def receive_file(self):
        """Принимает файл от клиента"""
        print("Ожидание файла...")
        
        expected_seq_num = 0
        file_data = bytearray()
        filename = None
        client_addr = None
        
        while True:
            try:
                data, addr = self.socket.recvfrom(2048)
                client_addr = addr
                
               
                if simulate_packet_loss(self.loss_rate):
                    print("Пакет потерян (симуляция)")
                    continue
                
                packet = Packet.from_bytes(data)
                
                if packet.packet_type == PACKET_TYPE_DATA:
                    print(f"Получен пакет {packet.seq_num}, ожидается {expected_seq_num}")
                    
                    
                    if packet.seq_num == expected_seq_num:
                        
                        if filename is None:
                            
                            name_size = packet.data[0]
                            filename = packet.data[1:name_size+1].decode('utf-8')
                            file_data.extend(packet.data[name_size+1:])
                            print(f"Получено имя файла: {filename}")
                        else:
                            
                            if len(packet.data) > 0 and packet.data[0] == 0xFF:
                               
                                if len(packet.data) > 1:  # Есть данные после маркера
                                    file_data.extend(packet.data[1:])
                                
                                
                                file_path = os.path.join(self.output_dir, filename)
                                with open(file_path, 'wb') as f:
                                    f.write(file_data)
                                print(f"Файл {filename} успешно получен и сохранен в {file_path}")
                                
                                
                                self.send_ack(expected_seq_num, addr)
                                return filename
                            else:
                                file_data.extend(packet.data)
                        
                       
                        expected_seq_num = 1 - expected_seq_num
                    
                    
                    self.send_ack(packet.seq_num, addr)
            
            except Exception as e:
                print(f"Ошибка при приеме данных: {e}")
                if client_addr:
                    # Отправляем последний ACK еще раз
                    self.send_ack(1 - expected_seq_num, client_addr)

    def close(self):
        self.socket.close()
        print("Сервер остановлен")

if __name__ == "__main__":
    try:
        server = StopAndWaitServer()
        filename = server.receive_file()
        print(f"Успешно получен файл: {filename}")
    except KeyboardInterrupt:
        print("\nСервер остановлен пользователем")
    except Exception as e:
        print(f"Ошибка сервера: {e}")
    finally:
        if 'server' in locals():
            server.close()
