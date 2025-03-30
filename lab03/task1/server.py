import socket
import os

def start_server(server_port):
   
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', server_port))
    server_socket.listen(1)
    print(f'Server started on port {server_port}...')

    while True:
        client_connection, client_address = server_socket.accept()
        request = client_connection.recv(1024).decode()
        
        
        request_lines = request.splitlines()
        if len(request_lines) > 0:
            request_line = request_lines[0]
            print(f'Request: {request_line}')
            file_name = request_line.split()[1]

            
            if file_name.startswith('/'):
                file_name = file_name[1:]

            
            if os.path.exists(file_name) and os.path.isfile(file_name):
                with open(file_name, 'rb') as f:
                    response_body = f.read()
                response_line = 'HTTP/1.1 200 OK\n'
            else:
                response_body = b'<html><body><h1>404 Not Found</h1></body></html>'
                response_line = 'HTTP/1.1 404 Not Found\n'

            
            response_headers = 'Content-Length: {}\nContent-Type: text/html\n\n'.format(len(response_body))
            response = response_line + response_headers
            client_connection.sendall(response.encode() + response_body)
        
        
        client_connection.close()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python server.py <server_port>")
        sys.exit(1)
    
    port = int(sys.argv[1])
    start_server(port)
