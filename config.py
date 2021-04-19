from enum import Enum

# | syn | ack | fin |00000|
# |-----|-----|-----|-----|


SYN_FLAG = b"\x09"
ACK_FLAG = b"\x02"
SYNACK_FLAG = b"\x03"
FIN_FLAG = b"\x04"
FINACK_FLAG = b"\x06"
SOCKET_TIMEOUT = 0.5
# TIME_WAIT_TIMEOUT = 0.2
MAX_FAIL_COUNT = 30
PACKET_TIMEOUT = 0.1
PACKET_LENGTH = 900

# 1. no connection
# 2. syn happened
# 3. syn ack sent
# 4. ack received -> connected


class ConnState(Enum):
    NO_CONNECT = 0
    SYN = 1
    SYNACK = 2
    CONNECTED = 3
    FIN_WAIT = 4
    CLOSE_WAIT = 5
    CLOSED = 6


CONNECTED_STATES = [ConnState.CONNECTED, ConnState.FIN_WAIT, ConnState.CLOSE_WAIT]


class PacketState(Enum):
    NOT_SENT = 0
    SENT = 1
    ACKED = 2
    NACK = 3
