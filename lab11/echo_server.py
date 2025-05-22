# echo_server.py
import socket
import sys

def start_server(host='::1', port=8888):
    """
    Запускает эхо-сервер, работающий по протоколу IPv6 через TCP.
    Принимает сообщения от клиентов и отправляет их обратно в верхнем регистре.
    """
    try:

        server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        

        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        

        server_socket.bind((host, port))
        

        server_socket.listen(5)
        
        print(f"Сервер запущен на [{host}]:{port}")
        
        while True:

            client_socket, client_address = server_socket.accept()
            print(f"Подключен клиент: {client_address}")
            
            try:
                while True:
  
                    data = client_socket.recv(1024)
                    
                    if not data:
                
                        print(f"Клиент {client_address} отключился")
                        break
               
                    received_message = data.decode('utf-8')
                    print(f"Получено сообщение: {received_message}")
                    
            
                    response = received_message.upper()
                    
         
                    client_socket.send(response.encode('utf-8'))
                    print(f"Отправлен ответ: {response}")
                    
            except Exception as e:
                print(f"Ошибка обработки запроса от клиента {client_address}: {e}")
            finally:
           
                client_socket.close()
                
    except Exception as e:
        print(f"Ошибка сервера: {e}")
    finally:
        if 'server_socket' in locals():
            server_socket.close()
            print("Сервер остановлен")

if __name__ == "__main__":

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    start_server(port=port)
