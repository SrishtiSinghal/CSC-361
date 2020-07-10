from socket import *
import sys

host_ip = sys.argv[1]
port_number = int(sys.argv[2])
file_name = sys.argv[3]

s = socket(AF_INET, SOCK_STREAM)

s.connect((host_ip, port_number))

message = "GET /"+filename+" HTTP/1.1\r\n\r\n"

s.send(message.encode())

data = s.recv(4096) 

print(data)

s.close()
