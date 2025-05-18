import socket
import ssl
import base64
import argparse
import getpass
import sys

def send_mail_via_socket(sender, recipient, subject, message, smtp_server, smtp_port=587):
    """
    Отправляет электронное письмо через SMTP используя сокеты.
    
    Args:
        sender: Email отправителя
        recipient: Email получателя
        subject: Тема письма
        message: Текст письма
        smtp_server: Адрес SMTP сервера
        smtp_port: Порт SMTP сервера (по умолчанию 587 для TLS)
    """
    
   
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        print(f"Соединение с {smtp_server}:{smtp_port}...")
        
        sock.connect((smtp_server, smtp_port))
        
        
        response = sock.recv(1024).decode()
        print(f"Сервер: {response}")
        if not response.startswith('220'):
            print("Ошибка подключения к серверу")
            return
        
       
        ehlo_command = f"EHLO {socket.gethostname()}\r\n"
        print(f"Клиент: {ehlo_command.strip()}")
        sock.send(ehlo_command.encode())
        
        response = sock.recv(1024).decode()
        print(f"Сервер: {response}")
        if not response.startswith('250'):
            print("Ошибка в команде EHLO")
            return
        
        
        print("Клиент: STARTTLS")
        sock.send("STARTTLS\r\n".encode())
        
        response = sock.recv(1024).decode()
        print(f"Сервер: {response}")
        if not response.startswith('220'):
            print("Ошибка при старте TLS")
            return
        
       
        ssl_sock = ssl.wrap_socket(sock, ssl_version=ssl.PROTOCOL_TLS)
        
        
        ehlo_command = f"EHLO {socket.gethostname()}\r\n"
        print(f"Клиент: {ehlo_command.strip()}")
        ssl_sock.send(ehlo_command.encode())
        
        response = ssl_sock.recv(1024).decode()
        print(f"Сервер: {response}")
        
       
        print("Клиент: AUTH LOGIN")
        ssl_sock.send("AUTH LOGIN\r\n".encode())
        
        response = ssl_sock.recv(1024).decode()
        print(f"Сервер: {response}")
        
        
        username_b64 = base64.b64encode(sender.encode()).decode()
        print(f"Клиент: {username_b64}")
        ssl_sock.send(f"{username_b64}\r\n".encode())
        
        response = ssl_sock.recv(1024).decode()
        print(f"Сервер: {response}")
        
       
        password = ""
        password_b64 = base64.b64encode(password.encode()).decode()
        print("Клиент: *********") 
        ssl_sock.send(f"{password_b64}\r\n".encode())
        
        response = ssl_sock.recv(1024).decode()
        print(f"Сервер: {response}")
        if not response.startswith('235'):
            print("Ошибка аутентификации. Проверьте логин и пароль.")
            return
        
        
        mail_from = f"MAIL FROM:<{sender}>\r\n"
        print(f"Клиент: {mail_from.strip()}")
        ssl_sock.send(mail_from.encode())
        
        response = ssl_sock.recv(1024).decode()
        print(f"Сервер: {response}")
        
       
        rcpt_to = f"RCPT TO:<{recipient}>\r\n"
        print(f"Клиент: {rcpt_to.strip()}")
        ssl_sock.send(rcpt_to.encode())
        
        response = ssl_sock.recv(1024).decode()
        print(f"Сервер: {response}")
        
        
        print("Клиент: DATA")
        ssl_sock.send("DATA\r\n".encode())
        
        response = ssl_sock.recv(1024).decode()
        print(f"Сервер: {response}")
        
       
        email_data = f"From: {sender}\r\n"
        email_data += f"To: {recipient}\r\n"
        email_data += f"Subject: {subject}\r\n"
        email_data += "MIME-Version: 1.0\r\n"
        email_data += "Content-Type: text/plain; charset=utf-8\r\n"
        email_data += "\r\n"  
        email_data += message + "\r\n"
        email_data += ".\r\n"  
        
        print("Клиент: <Данные письма>")
        ssl_sock.send(email_data.encode())
        
        response = ssl_sock.recv(1024).decode()
        print(f"Сервер: {response}")
        
   
        print("Клиент: QUIT")
        ssl_sock.send("QUIT\r\n".encode())
        
        response = ssl_sock.recv(1024).decode()
        print(f"Сервер: {response}")
        
        print("Письмо успешно отправлено!")
        
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:

        try:
            ssl_sock.close()
        except:
            sock.close()

def main():
    parser = argparse.ArgumentParser(description='Отправить электронное письмо через SMTP используя сокеты.')
    parser.add_argument('--sender', '-s', required=True, help='Email адрес отправителя')
    parser.add_argument('--recipient', '-r', required=True, help='Email адрес получателя')
    parser.add_argument('--subject', '-j', default='Тестовое письмо', help='Тема письма')
    parser.add_argument('--message', '-m', help='Текст сообщения')
    parser.add_argument('--server', default='smtp.gmail.com', help='SMTP сервер (по умолчанию gmail)')
    parser.add_argument('--port', type=int, default=587, help='SMTP порт (по умолчанию 587)')
    
    args = parser.parse_args()
    

    message = args.message
    if not message:
        print("Введите текст сообщения (для завершения ввода нажмите Enter и Ctrl+D в Unix или Ctrl+Z в Windows):")
        message_lines = []
        
        try:
            while True:
                line = input()
                message_lines.append(line)
        except (EOFError, KeyboardInterrupt):
            pass
        
        message = '\n'.join(message_lines)
    
  
    
    send_mail_via_socket(args.sender, args.recipient, args.subject, message, args.server, args.port)

if __name__ == "__main__":
    main()
