import logging

logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)


def info(msg):
    logging.info(msg)


def warn(msg):
    logging.warning(msg)

def error(msg):
    logging.error(msg)
