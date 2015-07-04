#!/usr/bin/env python3

from global_constants import *

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

def config_logger(name=__name__, log_file=None, replace_stdout = False, logLevel = TG_LOG_LEVEL):
    logger = logging.getLogger(name)

    if logLevel is None:
        logLevel = TG_LOG_LEVEL
    logger.setLevel(logLevel)
    
    if log_file is None:
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.handlers.TimedRotatingFileHandler(log_file, when="midnight", backupCount=3)
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    if replace_stdout:
        sys.stdout = STLogger(logger, logging.INFO)
        sys.stderr = STLogger(logger, logging.ERROR)
    return logger

