import sys
import os
import gzip
import io
import socket
from threading import Thread

def handle_req(client_socket, directory=None):
    print("Client connected")

    req = client_socket.recv(1024).decode()
    req_lines = req.split(' ')

    print(req_lines)

    method = req_lines[0]
    accept_encoding = "gzip" if any(i in ["gzip,", "gzip\r\n\r\n"] for i in req_lines) else None

    print("Method is:", method)
    print("Accept-Encoding is:", accept_encoding)

    if req_lines[1] not in ["/", "/user-agent"]:
        response = "HTTP/1.1 404 Not Found\r\n\r\n"
    else:
        response = "HTTP/1.1 200 OK\r\n\r\n"

    if "/echo" in req_lines[1]:
        data = req_lines[1].split('/')[2]
        content_length = len(data)
        print(f"Data is: {data}, length: {content_length}")
        if accept_encoding:
            buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode='wb') as f:
                f.write(data.encode('utf-8'))
            compressed_data = buffer.getvalue()
            comp_content_length = len(compressed_data)
            print("Compressed data:", compressed_data)
            print("Compressed length is:", comp_content_length)
            response = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: text/plain\r\n"
                f"Content-Encoding: gzip\r\n"
                f"Content-Length: {comp_content_length}\r\n\r\n"
            ).encode() + compressed_data
        else:
            response = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: text/plain\r\n"
                f"Content-Length: {content_length}\r\n\r\n"
                f"{data}"
            )
    elif "/user-agent" in req_lines[1]:
        data = req_lines[-1].strip()
        content_length = len(data)
        print("User-Agent:", data)
        response = (
            f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: text/plain\r\n"
            f"Content-Length: {content_length}\r\n\r\n"
            f"{data}"
        )
    elif req_lines[1].startswith("/files/"):
        file_name = req_lines[1].split('/')[2]
        file_path = os.path.join(directory, file_name)

        if method == "POST":
            body = req.split('\r\n\r\n', 1)[-1]
            print("Body is:", body)
            with open(file_path, 'wb') as file:
                file.write(body.encode('utf-8'))
            response = "HTTP/1.1 201 Created\r\n\r\n"
        else:
            try:
                with open(file_path, "r") as f:
                    print("Opened file")
                    body = f.read()
                    response = (
                        f"HTTP/1.1 200 OK\r\n"
                        f"Content-Type: application/octet-stream\r\n"
                        f"Content-Length: {len(body)}\r\n\r\n"
                        f"{body}"
                    )
            except FileNotFoundError:
                print("File not found")
                response = "HTTP/1.1 404 Not Found\r\n\r\n"

    if accept_encoding:
        client_socket.send(response)
    else:
        client_socket.send(response.encode())

    client_socket.close()

def main():
    print("Logs from your program will appear here!")
    directory = None
    try:
        directory = sys.argv[2]
    except IndexError:
        print("No directory provided")

    server_socket = socket.create_server(("localhost", 4221))
    print("Server is started and running on port 4221")

    try:
        while True:
            print("Listening for connections")
            client_socket, addr = server_socket.accept()
            Thread(target=handle_req, args=(client_socket, directory)).start()
    except Exception as e:
        print(e)
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()
