#!/usr/bin/env python3

import logging
import logging.handlers
import argparse
import sys

class STLogger(object):
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message.rstrip() != "":
            self.logger.log(self.level, message.rstrip())

    def flush(self):
        pass

def config_logger(name=__name__, log_file=None, replace_stdout = False, logLevel = logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if log_file is None:
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    if replace_stdout:
        sys.stdout = STLogger(logger, logging.INFO)
        sys.stderr = STLogger(logger, logging.ERROR)
    return logger

