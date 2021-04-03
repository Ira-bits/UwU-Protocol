from driver import *
serv = create_server_process()
serv.recv_proc.start()
print("server done")
client = create_client_process()
client.recv_proc.start()
client.send()
print("here")
