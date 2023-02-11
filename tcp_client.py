# simplest form of a tcp client
# assumptions with this code snippit:
# 1. connection will always succeed
# 2. server expects us to send data first (some expect data to flow other way around)
# 3. ther server will always return data to us in a timely fashion

import socket

target_host = "www.google.com"
target_port = 80

#create a socket object
client = socket.socket(socket.AF_INET. socket.SOCK_STREAM)

# connect the client 
client.connect((target_host,target_port))

# send some data
client.send(b"GET / HTTP/1.1\r\nHost: google.com\r\n\r\n")

# receive some data
response = client.recv(4096)

print(response.decode())
client.close()