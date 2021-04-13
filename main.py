from driver import *
import logging

serv = create_server_process()
serv.recv_proc.start()
logging.info("Server setup")

client = create_client_process()
client.recv_proc.start()
logging.info("Client setup")
client.connect_to()
client.send()
