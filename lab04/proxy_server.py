import socket
import threading
import re
import datetime

# Конфигурация
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 8080
LOG_FILE = 'proxy.log'
BUFFER_SIZE = 8192
TIMEOUT = 5  # секунды

def log_request(client_addr, method, url, status_code):
    """Записывает запрос в журнал"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {client_addr} - {method} {url} - Status: {status_code}\n"
    
    print(log_entry.strip())  # Вывод в консоль
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)

def extract_host_and_path(request_line):
    """Извлекает хост и путь из строки запроса"""
    parts = request_line.split()
    if len(parts) < 3:
        return None, None
    
    method, url, version = parts
    
    # Если URL содержит полный адрес
    if url.startswith('http://'):
        # Удаляем 'http://'
        url = url[7:]
        # Разделяем на хост и путь
        if '/' in url:
            host, path = url.split('/', 1)
            path = '/' + path
        else:
            host = url
            path = '/'
    else:
        # URL без схемы, ищем хост в заголовках
        host = None
        path = url
    
    return host, path

def forward_request(client_socket, client_addr):
    """Обрабатывает запрос клиента и пересылает его на целевой сервер"""
    try:
        # Получаем данные от клиента
        request_data = b''
        while True:
            chunk = client_socket.recv(BUFFER_SIZE)
            if not chunk:
                break
            request_data += chunk
            
            # Проверяем, получили ли мы полный HTTP-запрос
            if b'\r\n\r\n' in request_data:
                # Если это POST запрос, нужно проверить Content-Length
                headers_end = request_data.find(b'\r\n\r\n')
                headers = request_data[:headers_end].decode('utf-8', errors='ignore')
                
                # Проверяем, это POST запрос?
                if re.search(r'^POST', headers, re.MULTILINE):
                    # Ищем Content-Length
                    match = re.search(r'Content-Length: (\d+)', headers, re.MULTILINE)
                    if match:
                        content_length = int(match.group(1))
                        # Проверяем, получили ли мы все тело запроса
                        body_received = len(request_data) - headers_end - 4  # -4 для \r\n\r\n
                        if body_received >= content_length:
                            break
                else:
                    # Для GET запросов достаточно заголовков
                    break
        
        if not request_data:
            client_socket.close()
            return
        
        # Разбираем заголовки запроса
        headers_raw = request_data.split(b'\r\n\r\n')[0].decode('utf-8', errors='ignore')
        headers_lines = headers_raw.split('\r\n')
        
        # Извлекаем метод, URL и версию HTTP
        request_line = headers_lines[0]
        method = request_line.split()[0]
        
        # Находим Host в заголовках
        host_header = None
        for line in headers_lines[1:]:
            if line.lower().startswith('host:'):
                host_header = line.split(':', 1)[1].strip()
                break
        
        # Извлекаем хост и путь из строки запроса
        url_host, path = extract_host_and_path(request_line)
        
        # Используем хост из заголовка, если не найден в URL
        target_host = url_host or host_header
        
        # Если хост все еще не найден, нельзя продолжить
        if not target_host:
            response = b"HTTP/1.1 400 Bad Request\r\nContent-Length: 23\r\n\r\nMissing Host information"
            client_socket.sendall(response)
            log_request(client_addr, method, "Unknown", 400)
            client_socket.close()
            return
        
        # Проверяем, есть ли указание порта
        if ':' in target_host:
            target_host, target_port = target_host.split(':', 1)
            target_port = int(target_port)
        else:
            target_port = 80  # HTTP по умолчанию
        
        # Формируем новую строку запроса с абсолютным путем
        new_request_line = f"{method} {path} HTTP/1.1"
        
        # Собираем новые заголовки, убирая заголовки прокси
        new_headers = [new_request_line]
        for line in headers_lines[1:]:
            if not line.lower().startswith(('proxy-connection:', 'connection:')):
                new_headers.append(line)
        
        # Добавляем заголовок Connection: close
        new_headers.append("Connection: close")
        
        # Собираем новый запрос
        if b'\r\n\r\n' in request_data:
            request_body = request_data.split(b'\r\n\r\n', 1)[1]
            new_request = '\r\n'.join(new_headers).encode('utf-8') + b'\r\n\r\n' + request_body
        else:
            new_request = '\r\n'.join(new_headers).encode('utf-8') + b'\r\n\r\n'
        
        # Создаем сокет для связи с целевым сервером
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.settimeout(TIMEOUT)
        
        try:
            # Подключаемся к целевому серверу
            server_socket.connect((target_host, target_port))
            
            # Отправляем запрос на сервер
            server_socket.sendall(new_request)
            
            # Получаем ответ от сервера
            response_data = b''
            while True:
                try:
                    chunk = server_socket.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    response_data += chunk
                except socket.timeout:
                    break
            
            # Извлекаем код состояния для журнала
            status_code = "Unknown"
            status_match = re.search(rb'HTTP/\d\.\d (\d+)', response_data)
            if status_match:
                status_code = status_match.group(1).decode('utf-8')
            
            # Отправляем клиенту ответ от сервера
            client_socket.sendall(response_data)
            
            # Логируем запрос
            url = f"http://{target_host}{path}"
            log_request(client_addr, method, url, status_code)
            
        except socket.error as e:
            # Обработка ошибок сетевого соединения
            error_message = f"Error connecting to {target_host}:{target_port}: {str(e)}"
            response = f"HTTP/1.1 502 Bad Gateway\r\nContent-Length: {len(error_message)}\r\n\r\n{error_message}"
            client_socket.sendall(response.encode('utf-8'))
            
            # Логируем ошибку
            url = f"http://{target_host}{path}"
            log_request(client_addr, method, url, 502)
        
        finally:
            server_socket.close()
            
    except Exception as e:
        # Обработка любых других ошибок
        error_message = f"Proxy error: {str(e)}"
        try:
            response = f"HTTP/1.1 500 Internal Server Error\r\nContent-Length: {len(error_message)}\r\n\r\n{error_message}"
            client_socket.sendall(response.encode('utf-8'))
            log_request(client_addr, "Unknown", "Unknown", 500)
        except:
            pass
    
    finally:
        # Закрываем соединение с клиентом
        client_socket.close()

def start_proxy():
    """Запускает прокси-сервер"""
    # Создаем TCP сокет
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # Привязываем сокет к адресу и порту
        proxy_socket.bind((PROXY_HOST, PROXY_PORT))
        proxy_socket.listen(100)  # максимальное количество ожидающих соединений
        
        print(f"Прокси-сервер запущен на {PROXY_HOST}:{PROXY_PORT}")
        
        # Главный цикл обработки соединений
        while True:
            try:
                # Принимаем входящее соединение
                client_socket, client_addr = proxy_socket.accept()
                client_addr_str = f"{client_addr[0]}:{client_addr[1]}"
                
                # Обрабатываем соединение в отдельном потоке
                client_thread = threading.Thread(
                    target=forward_request,
                    args=(client_socket, client_addr_str)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error accepting connection: {e}")
    
    except KeyboardInterrupt:
        print("\nЗавершение работы прокси-сервера...")
    
    finally:
        proxy_socket.close()

if __name__ == "__main__":
    # Создаем пустой файл журнала (или очищаем существующий)
    with open(LOG_FILE, 'w') as f:
        f.write("")
    
    # Запускаем сервер
    start_proxy()
