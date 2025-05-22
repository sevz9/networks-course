#!/usr/bin/env python3
import socket
import struct
import time
import select
import sys
import statistics
from datetime import datetime

def calculate_checksum(data):
    """Рассчитывает контрольную сумму для ICMP пакета"""
    checksum = 0

    count_to = (len(data) // 2) * 2
    

    for count in range(0, count_to, 2):
        this_val = data[count + 1] * 256 + data[count]
        checksum += this_val
        checksum &= 0xffffffff  
    

    if count_to < len(data):
        checksum += data[count_to]
        checksum &= 0xffffffff  
    

    checksum = (checksum >> 16) + (checksum & 0xffff)
    checksum += (checksum >> 16)
    

    answer = ~checksum & 0xffff

    answer = ((answer >> 8) & 0xff) | ((answer & 0xff) << 8)
    
    return answer

def create_icmp_packet(id, seq_number, payload_size=56):
    """Создает ICMP пакет с заданными параметрами"""

    header = struct.pack('!BBHHH', 8, 0, 0, id, seq_number)
    

    timestamp = struct.pack('!d', time.time())
    data = timestamp + bytes(payload_size - len(timestamp))
    

    checksum = calculate_checksum(header[0:2] + b'\x00\x00' + header[4:] + data)
    

    header = struct.pack('!BBHHH', 8, 0, checksum, id, seq_number)
    
    return header + data

def parse_icmp_response(data, packet_id, expected_seq_number):
    """Разбирает ICMP ответ и проверяет, соответствует ли он нашему запросу"""
 
    ip_header_len = (data[0] & 0x0F) * 4
    

    icmp_header = data[ip_header_len:ip_header_len+8]
    
    type, code, checksum, id, seq_number = struct.unpack('!BBHHH', icmp_header)
    
   
    if type == 0 and id == packet_id and seq_number == expected_seq_number:

        timestamp = struct.unpack('!d', data[ip_header_len+8:ip_header_len+16])[0]
        return True, timestamp
    
    return False, 0

def ping(host, count=4, timeout=1, interval=1):
    """Пингует указанный хост и анализирует результаты"""
    try:

        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        sock.settimeout(timeout)
    except socket.error as e:
        if e.errno == 1:

            print("Требуются привилегии администратора (root)")
            return
        raise e
    

    try:
        dest_addr = socket.gethostbyname(host)
    except socket.gaierror:
        print(f"Ошибка: Хост {host} не найден")
        return
    
    print(f"PING {host} ({dest_addr})")
    

    sent_packets = 0
    received_packets = 0
    rtts = []
    

    packet_id = (id(host) & 0xFFFF) or 1
    
    for seq in range(1, count + 1):

        packet = create_icmp_packet(packet_id, seq)
        

        sock.sendto(packet, (dest_addr, 0))
        sent_packets += 1
        

        send_time = time.time()
        

        ready = select.select([sock], [], [], timeout)
        if ready[0]: 
            recv_packet, addr = sock.recvfrom(1024)
        
            recv_time = time.time()
            
  
            valid, timestamp = parse_icmp_response(recv_packet, packet_id, seq)
            
            if valid:
    
                rtt = (recv_time - timestamp) * 1000
                rtts.append(rtt)
                received_packets += 1
                
                print(f"64 bytes from {addr[0]}: icmp_seq={seq} time={rtt:.2f} ms")
            else:
                print(f"Received unexpected ICMP packet")
        else:
            print(f"Request timeout for icmp_seq {seq}")
        
  
        if seq < count:
            time.sleep(interval)
    

    loss_rate = 100.0 - (received_packets / sent_packets * 100) if sent_packets > 0 else 100.0
    print(f"\n--- {host} ping statistics ---")
    print(f"{sent_packets} packets transmitted, {received_packets} received, {loss_rate:.1f}% packet loss")
    
    if rtts:
        min_rtt = min(rtts)
        max_rtt = max(rtts)
        avg_rtt = sum(rtts) / len(rtts)
        mdev = statistics.stdev(rtts) if len(rtts) > 1 else 0
        
        print(f"round-trip min/avg/max/mdev = {min_rtt:.3f}/{avg_rtt:.3f}/{max_rtt:.3f}/{mdev:.3f} ms")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python ping.py <хост> [количество запросов]")
        sys.exit(1)
        
    host = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    
    ping(host, count)
