
import struct
import random


HEADER_SIZE = 9 
PACKET_TYPE_DATA = 1
PACKET_TYPE_ACK = 2
MAX_PACKET_SIZE = 1024  

class Packet:
    def __init__(self, packet_type, seq_num, data=b''):
        self.packet_type = packet_type
        self.seq_num = seq_num
        self.data = data
    
    def to_bytes(self):
       
        header = struct.pack('!BII', self.packet_type, self.seq_num, len(self.data))
        return header + self.data
    
    @classmethod
    def from_bytes(cls, data):
        if len(data) < HEADER_SIZE:
            raise ValueError("Недостаточно данных для заголовка пакета")
        
        header = struct.unpack('!BII', data[:HEADER_SIZE])
        packet_type, seq_num, data_len = header
        
        if len(data) - HEADER_SIZE < data_len:
            raise ValueError("Неполный пакет")
        
        payload = data[HEADER_SIZE:HEADER_SIZE + data_len]
        return cls(packet_type, seq_num, payload)

def simulate_packet_loss(loss_rate=0.3):
    """Имитирует потерю пакета с заданной вероятностью"""
    return random.random() < loss_rate
