import socket


def handle_request(req):
    if(req == b'ACK'):
        return -1
    return str.encode("I wanna be a cowboy, baby", encoding='ascii')


def handle_ACK():
    pass


bufSize = 1024

UDPserv = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPserv.bind(("127.0.0.1", 20001))

while(True):
    bytes_addr_pair = UDPserv.recvfrom(bufSize)  # recvfrom has IP address
    # todo, fork a process for each client
    req, address = bytes_addr_pair
    print(req)
    data = handle_request(req)
    print(data)
    if(data != -1):
        UDPserv.sendto(data, address)
    else:
        handle_ACK()
