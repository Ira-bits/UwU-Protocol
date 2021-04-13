import logging

HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKCYAN = '\033[96m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'


def setupLogging():
    """
    Set up formatting for logging
    """

    logging.basicConfig(
        level=logging.DEBUG, format=f'{BOLD}%(asctime)s.%(msecs)03d :{ENDC} %(message)s', datefmt='%H:%M:%S')


def logServer(msg: str):
    logging.debug(f"{OKGREEN}SERVER:{ENDC} {msg}")


def logClient(msg: str):
    logging.debug(f"{OKCYAN}CLIENT:{ENDC} {msg}")
