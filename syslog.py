#!/usr/bin/env python3
from pprint import pprint

import logging
from os import getpid
from socket import SOCK_STREAM, SOCK_DGRAM
from logging.handlers import RotatingFileHandler, SysLogHandler


class Syslog():
    def __init__(self, initmsg=None):
        self.logger = logging.getLogger(name)
        # self.logger.setLevel(logging.DEBUG)
        self.msgprefix = '{}[{}]: '.format(name, getpid())

        if initmsg is not None:
            self.info('{}'.format(initmsg))

    def info(self, msg):
        self.logger.info('{} {}'.format(self.msgprefix, msg))

    def warning(self, msg):
        self.logger.warning('{} {}'.format(self.msgprefix, msg))

    def error(self, msg):
        self.logger.error('{} {}'.format(self.msgprefix, msg))

    def debug(self, msg):
        self.logger.debug('{} {}'.format(self.msgprefix, msg))

if __name__ == '__main__':
    s = Syslog()
    s.info('SPAMTRAP:module:message goes here')
