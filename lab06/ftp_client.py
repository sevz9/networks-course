import ftplib
import os
import sys

class FTPClient:
    def __init__(self):
        self.ftp = None
        self.is_connected = False
    
    def connect(self, host, username, password, port=21):
        """Подключение к FTP серверу"""
        try:
            self.ftp = ftplib.FTP()
            self.ftp.connect(host, port)
            self.ftp.login(username, password)
            self.is_connected = True
            print(f"Успешное подключение к {host}")
            print(self.ftp.getwelcome())
            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False
    
    def list_files(self):
        """Отображение списка файлов и директорий на сервере"""
        if not self.is_connected:
            print("Нет подключения к FTP серверу")
            return
        
        try:
            print("\nСодержимое директории:")
            print("-" * 50)
            
            
            files = []
            
            def process_line(line):
                parts = line.split()
                if len(parts) < 9:
                    return
                
                file_type = "📁" if line.startswith('d') else "📄"
                file_name = " ".join(parts[8:])
                file_size = parts[4]
                file_date = " ".join(parts[5:8])
                
                files.append((file_type, file_name, file_size, file_date))
            
            self.ftp.retrlines('LIST', process_line)
            
            
            files.sort(key=lambda x: x[0] == "📄")
            
            
            if not files:
                print("Директория пуста")
            else:
                print(f"{'Тип':<4}{'Имя':<30}{'Размер':<10}{'Дата':<20}")
                print("-" * 60)
                for file_type, file_name, file_size, file_date in files:
                    print(f"{file_type:<4}{file_name:<30}{file_size:<10}{file_date:<20}")
            
            print("-" * 50)
            
        except Exception as e:
            print(f"Ошибка при получении списка файлов: {e}")
    
    def upload_file(self, local_path):
        """Загрузка файла на сервер"""
        if not self.is_connected:
            print("Нет подключения к FTP серверу")
            return
        
        if not os.path.exists(local_path):
            print(f"Ошибка: файл {local_path} не найден")
            return
        
        try:
            
            filename = os.path.basename(local_path)
            filesize = os.path.getsize(local_path)
            
            print(f"Загрузка файла {filename} на сервер (размер: {filesize} байт)")
            
            
            uploaded = 0
            
            
            def upload_callback(data):
                nonlocal uploaded
                uploaded += len(data)
                percent = int(uploaded * 100 / filesize)
                sys.stdout.write(f"\rПрогресс: {percent}% [{uploaded}/{filesize} байт]")
                sys.stdout.flush()
            
            
            with open(local_path, 'rb') as file:
                self.ftp.storbinary(f'STOR {filename}', file, 1024, upload_callback)
            
            print("\nФайл успешно загружен на сервер")
            
        except Exception as e:
            print(f"\nОшибка при загрузке файла: {e}")
    
    def download_file(self, remote_filename, local_path=None):
        """Скачивание файла с сервера"""
        if not self.is_connected:
            print("Нет подключения к FTP серверу")
            return
        
        
        if local_path is None:
            local_path = remote_filename
        
        try:
            
            file_list = []
            self.ftp.retrlines('NLST', file_list.append)
            
            if remote_filename not in file_list:
                print(f"Ошибка: файл {remote_filename} не найден на сервере")
                return
            
            
            try:
                filesize = self.ftp.size(remote_filename)
            except:
                filesize = 0  # Если не удалось узнать размер
            
            print(f"Скачивание файла {remote_filename} с сервера")
            
            
            downloaded = 0
            
            
            def download_callback(data):
                nonlocal downloaded
                downloaded += len(data)
                if filesize > 0:
                    percent = int(downloaded * 100 / filesize)
                    sys.stdout.write(f"\rПрогресс: {percent}% [{downloaded}/{filesize} байт]")
                else:
                    sys.stdout.write(f"\rЗагружено {downloaded} байт")
                sys.stdout.flush()
                return data
            
            
            with open(local_path, 'wb') as file:
                def write_to_file(data):
                    file.write(data)
                    download_callback(data)
                
                self.ftp.retrbinary(f'RETR {remote_filename}', write_to_file)
            
            print(f"\nФайл успешно скачан и сохранен как {local_path}")
            
        except Exception as e:
            print(f"\nОшибка при скачивании файла: {e}")
    
    def disconnect(self):
        """Отключение от FTP сервера"""
        if self.is_connected:
            try:
                self.ftp.quit()
                print("Отключено от FTP сервера")
            except:
                self.ftp.close()
                print("Соединение с FTP сервером закрыто")
            finally:
                self.is_connected = False

def main():
    """Основная функция программы"""
    client = FTPClient()
    
    print("=" * 50)
    print("FTP клиент для работы с dlptest.com")
    print("=" * 50)
    
    
    host = "ftp.dlptest.com"
    username = "dlpuser"
    password = "rNrKYTX9g7z3RgJRmxWuGHbeu"
    
    
    if not client.connect(host, username, password):
        print("Не удалось подключиться к серверу. Программа завершена.")
        return
    
    while True:
        print("\nМеню:")
        print("1. Показать список файлов и директорий")
        print("2. Загрузить файл на сервер")
        print("3. Скачать файл с сервера")
        print("4. Выход")
        
        choice = input("\nВыберите действие (1-4): ")
        
        if choice == '1':
            client.list_files()
        
        elif choice == '2':
            local_path = input("Введите путь к файлу для загрузки: ")
            client.upload_file(local_path)
        
        elif choice == '3':
            print("Доступные файлы на сервере:")
            files = []
            try:
                client.ftp.retrlines('NLST', files.append)
                if not files:
                    print("На сервере нет файлов")
                    continue
                    
                for i, filename in enumerate(files, 1):
                    print(f"{i}. {filename}")
                
                selection = input("Введите номер файла для скачивания или имя файла: ")
                
                
                if selection.isdigit() and 1 <= int(selection) <= len(files):
                    remote_filename = files[int(selection) - 1]
                else:
                    remote_filename = selection
                
                local_path = input(f"Введите путь для сохранения (пустой ввод для сохранения как {remote_filename}): ")
                if not local_path:
                    local_path = remote_filename
                
                client.download_file(remote_filename, local_path)
                
            except Exception as e:
                print(f"Ошибка при попытке скачать файл: {e}")
        
        elif choice == '4':
            print("Завершение работы...")
            client.disconnect()
            break
        
        else:
            print("Некорректный ввод. Пожалуйста, выберите число от 1 до 4.")

if __name__ == "__main__":
    main()
