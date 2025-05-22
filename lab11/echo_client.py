# echo_client.py
import socket
import sys

def send_message(message, host='::1', port=8888):
    """
    Отправляет сообщение на эхо-сервер по протоколу IPv6 через TCP
    и получает ответ от сервера.
    """
    try:

        client_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        

        client_socket.settimeout(5)
        

        print(f"Подключение к серверу [{host}]:{port}...")
        client_socket.connect((host, port))
        

        print(f"Отправка: {message}")
        client_socket.send(message.encode('utf-8'))
        
 
        response = client_socket.recv(1024).decode('utf-8')
        print(f"Ответ от сервера: {response}")
        
        return response
        
    except socket.timeout:
        print("Ошибка: превышено время ожидания")
    except ConnectionRefusedError:
        print("Ошибка: сервер не запущен или недоступен")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        if 'client_socket' in locals():
            client_socket.close()

if __name__ == "__main__":

    message = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else "Hello, IPv6 World!"
    

    send_message(message)
