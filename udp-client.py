import socket


def request_handler():
    return str.encode("hello there", encoding='ascii')


serverLoc = ('127.0.0.1', 20001)
bufSize = 1024

UDPclient = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

req = request_handler()

UDPclient.sendto(req, serverLoc)
message, _ = UDPclient.recvfrom(bufSize)
print(message.decode('utf-8'))
