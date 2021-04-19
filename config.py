from enum import Enum

# | syn | ack | fin |00000|
# |-----|-----|-----|-----|


SYN_FLAG = b"\x80"
ACK_FLAG = b"\x40"
SYNACK_FLAG = b"\xc0"
FIN_FLAG = b"\x20"
FINACK_FLAG = b"\x60"
SOCKET_TIMEOUT = 0.5
# TIME_WAIT_TIMEOUT = 0.2
MAX_FAIL_COUNT = 1000
PACKET_TIMEOUT = 0.5

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
