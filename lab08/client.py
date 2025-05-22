# client.py
import socket
import os
import sys
import time
from common import Packet, PACKET_TYPE_DATA, PACKET_TYPE_ACK, MAX_PACKET_SIZE, simulate_packet_loss

class StopAndWaitClient:
    def __init__(self, server_host='localhost', server_port=12345, timeout=1.0, loss_rate=0.3):
        self.server_addr = (server_host, server_port)
        self.timeout = timeout
        self.loss_rate = loss_rate
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(timeout)
        print(f"Клиент инициализирован, сервер: {server_host}:{server_port}, таймаут: {timeout}с")
    
    def send_packet(self, packet):
        """Отправляет пакет с учетом симуляции потери"""
        if not simulate_packet_loss(self.loss_rate):
            self.socket.sendto(packet.to_bytes(), self.server_addr)
            return True
        else:
            print(f"Пакет {packet.seq_num} потерян (симуляция)")
            return False
    
    def send_file(self, file_path):
        """Отправляет файл на сервер"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл {file_path} не найден")
        
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        
        print(f"Отправка файла: {filename} ({file_size} байт)")
        
        seq_num = 0
        total_bytes_sent = 0
        retransmissions = 0
        
        with open(file_path, 'rb') as f:
           
            name_bytes = filename.encode('utf-8')
            name_size = len(name_bytes)
            
           
            first_data = bytearray([name_size]) + name_bytes
            
           
            remaining_space = MAX_PACKET_SIZE - len(first_data)
            if remaining_space > 0:
                first_data.extend(f.read(remaining_space))
            
           
            first_packet = Packet(PACKET_TYPE_DATA, seq_num, first_data)
            
            if self.send_reliable_packet(first_packet):
                total_bytes_sent += len(first_data) - (name_size + 1) 
                seq_num = 1 - seq_num 
            
           
            while True:
                data = f.read(MAX_PACKET_SIZE)
                if not data:
                    break
                
                packet = Packet(PACKET_TYPE_DATA, seq_num, data)
                success, attempts = self.send_reliable_packet(packet)
                
                if success:
                    total_bytes_sent += len(data)
                    seq_num = 1 - seq_num  # Переключаем seq_num
                    retransmissions += attempts - 1
                else:
                    raise RuntimeError("Не удалось отправить пакет после нескольких попыток")
            
            
            end_marker = bytes([0xFF]) 
            last_packet = Packet(PACKET_TYPE_DATA, seq_num, end_marker)
            
            if self.send_reliable_packet(last_packet):
                seq_num = 1 - seq_num
            else:
                raise RuntimeError("Не удалось отправить финальный пакет")
        
        print(f"Файл успешно отправлен: {total_bytes_sent}/{file_size} байт")
        print(f"Повторных передач: {retransmissions}")
        return total_bytes_sent, retransmissions
    
    def send_reliable_packet(self, packet, max_attempts=10):
        """Отправляет пакет и ждет ACK, повторяет при необходимости"""
        attempts = 0
        
        while attempts < max_attempts:
            attempts += 1
            
            if attempts > 1:
                print(f"Повторная отправка пакета {packet.seq_num} (попытка {attempts})")
            else:
                print(f"Отправка пакета {packet.seq_num}")
            
           
            packet_sent = self.send_packet(packet)
            
            if not packet_sent:
                continue 
            
           
            try:
                data, _ = self.socket.recvfrom(2048)
                ack_packet = Packet.from_bytes(data)
                
                if ack_packet.packet_type == PACKET_TYPE_ACK and ack_packet.seq_num == packet.seq_num:
                    print(f"Получен ACK {ack_packet.seq_num}")
                    return True, attempts
                else:
                    print(f"Получен неверный ACK: {ack_packet.seq_num}, ожидался: {packet.seq_num}")
            
            except socket.timeout:
                print(f"Таймаут ожидания ACK для пакета {packet.seq_num}")
        
        return False, attempts
    
    def close(self):
        self.socket.close()
        print("Клиент остановлен")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python client.py <путь_к_файлу> [таймаут]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    
    try:
        client = StopAndWaitClient(timeout=timeout)
        start_time = time.time()
        total_bytes, retransmissions = client.send_file(file_path)
        elapsed_time = time.time() - start_time
        
        file_size = os.path.getsize(file_path)
        print(f"Передача завершена за {elapsed_time:.2f} секунд")
        print(f"Скорость передачи: {(total_bytes/elapsed_time)/1024:.2f} КБ/с")
        print(f"Эффективность: {(total_bytes/file_size)*100:.2f}%")
        
    except KeyboardInterrupt:
        print("\nКлиент остановлен пользователем")
    except Exception as e:
        print(f"Ошибка клиента: {e}")
    finally:
        if 'client' in locals():
            client.close()
