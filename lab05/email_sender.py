import smtplib
import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from getpass import getpass

def send_email(subject, message, message_format="txt"):
    """
    Отправляет электронное письмо получателю.
    
    Args:
        recipient_email: Email получателя
        subject: Тема письма
        message: Содержание письма
        message_format: Формат письма ('txt' или 'html')
        sender_email: Email отправителя
    """
    # Настройка сообщения
    recipient_email = "vsevolod9006@gmail.com"
    msg = MIMEMultipart('alternative')
    msg['From'] = "vsevolod9006@gmail.com"
    msg['To'] =  "vsevolod9006@gmail.com"
    msg['Subject'] = subject
    
    # Добавление содержимого в зависимости от формата
    if message_format.lower() == "html":
        msg.attach(MIMEText(message, 'html'))
    else:
        msg.attach(MIMEText(message, 'plain'))
    
    try:
        # Запрос пароля от почты отправителя
        password = ""
        sender_email = "vsevolod9006@gmail.com"
        
        # Соединение с SMTP-сервером (для Gmail)
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)
        
        print(f"Письмо успешно отправлено на {recipient_email}")
    except Exception as e:
        print(f"Ошибка при отправке письма: {e}")

def main():
    parser = argparse.ArgumentParser(description='Отправить электронное письмо.')
    parser.add_argument('recipient', help='Email адрес получателя')
    parser.add_argument('--subject', '-s', default='Тестовое письмо', help='Тема письма')
    parser.add_argument('--format', '-f', choices=['txt', 'html'], default='txt', 
                        help='Формат сообщения (txt или html)')
    parser.add_argument('--message', '-m', help='Текст сообщения')
    parser.add_argument('--sender', help='Email адрес отправителя (по умолчанию задан в коде)')
    
    args = parser.parse_args()
    
    # Если сообщение не указано в аргументах, запросить его у пользователя
    message = args.message
    if not message:
        if args.format == 'html':
            print("Введите HTML-сообщение (для завершения ввода нажмите Enter и Ctrl+D):")
            message_lines = []
            try:
                while True:
                    line = input()
                    message_lines.append(line)
            except EOFError:
                message = '\n'.join(message_lines)
        else:
            print("Введите текстовое сообщение (для завершения ввода нажмите Enter и Ctrl+D):")
            message_lines = []
            try:
                while True:
                    line = input()
                    message_lines.append(line)
            except EOFError:
                message = '\n'.join(message_lines)
    
    
    
    send_email(args.subject, message, args.format)

if __name__ == "__main__":
    main()
