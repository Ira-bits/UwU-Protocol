import multiprocessing
import server
import client
import config
import lib
from header import Packet, Header
from sortedcontainers import SortedSet


def create_server_process():
    lib.setupLogging()
    serv = server.run_server()
    config.app_server = serv
    return config.app_server


def create_client_process():
    lib.setupLogging()
    cli = client.run_client()
    config.app_client = cli
    return config.app_client


def keySort(l: Packet):
    return l.header.SEQ_NO


a = Header()
b = Header()
c = Packet(a)
d = Packet(b)
e = SortedSet(key=keySort)
e.add(c)
e.add(d)
print(e)
