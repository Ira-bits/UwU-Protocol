import multiprocessing
import server
import client
import config


def create_server_process():
    serv = server.run_server()
    config.app_server = serv
    return config.app_server


def create_client_process():
    cli = client.run_client()
    config.app_client = cli
    return config.app_client
