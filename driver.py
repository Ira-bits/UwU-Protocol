from multiprocessing import multiprocessing
import server
import client
import config


def create_server_process():
    serv = None
    serv_proc = multiprocessing.Process(
        target=server.run_server(), args=(None, serv))
    serv.serv_proc = serv_proc
    config.app_server = serv
    return config.app_server


def create_client_process():
    cl = None
    client_proc = multiprocessing.Process(
        target=client.run_client, args=(None, cl))
    cl.client_proc = client_proc
    config.app_client = cl
    return config.app_client
