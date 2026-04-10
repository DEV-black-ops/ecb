import socket
from datetime import datetime

HOST = "0.0.0.0"   # listen on all interfaces
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(5)

print("🚀 TCP Server Started... Waiting for ESP32")

while True:
    client_socket, addr = server.accept()
    print(f"\n📡 Connection from {addr}")

    data = client_socket.recv(1024).decode()

    if data:
        print("🔘 Button Pressed!")
        print("Data:", data)
        print("Time:", datetime.now())

    client_socket.close()