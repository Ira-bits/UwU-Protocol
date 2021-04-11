import logging

OKBLUE = '\033[94m'
ENDC = '\033[0m'


def setupLogging():
    """
    Set up formatting for logging
    """

    logging.basicConfig(
        level=logging.DEBUG, format=f'{OKBLUE}%(asctime)s.%(msecs)03d %(levelname)s:{ENDC} %(message)s', datefmt='%H:%M:%S')
