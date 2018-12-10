# -*- config:utf-8 -*-

import socket
import select
import re
import logging
from io import BytesIO
from pprint import pprint

divider_pattern = re.compile(br'^(.*?)\r?\n(.*?)\r?\n\r?\n', re.DOTALL)
first_line_pattern = re.compile(br'^SPAMD/[^ ]+ 0 EX_OK$')


class SpamAssassin(object):
    def __init__(self, message, timeout=30):
        self.score = None
        self.symbols = None

        # Connecting
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(timeout)
        client.connect(('127.0.0.1', 783))

        # Sending
        client.sendall(self._build_message(message))
        client.shutdown(socket.SHUT_WR)

        # Reading
        resfp = BytesIO()
        while True:
            ready = select.select([client], [], [], timeout)
            if ready[0] is None:
                # Kill with Timeout!
                print('[SpamAssassin] - Timeout ({0}s)!'.format(str(timeout)))
                break

            data = client.recv(4096)
            if data == b'':
                break

            resfp.write(data)

        # Closing
        client.close()
        client = None

        self._parse_response(resfp.getvalue())

    def _build_message(self, message):
        reqfp = BytesIO()
        data_len = str(len(message)).encode()
        reqfp.write(b'SYMBOLS SPAMC/1.2\r\n')
        reqfp.write(b'Content-Length: ' + data_len + b'\r\n')
        reqfp.write(b'User: cx42\r\n\r\n')
        reqfp.write(message)
        return reqfp.getvalue()

    def _parse_response(self, response):
        if response == b'':
            logging.info("[SPAM ASSASSIN] Empty response")
            return None

        match = divider_pattern.match(response)
        if not match:
            logging.error("[SPAM ASSASSIN] Response error:")
            logging.error(response)
            return None

        first_line = match.group(1)
        headers = match.group(2)
        body = response[match.end(0):]

        # Checking response is good
        match = first_line_pattern.match(first_line)
        if not match:
            logging.error("[SPAM ASSASSIN] invalid response:")
            logging.error(first_line)
            return None

        self.symbols = [s.decode('ascii').strip()
                        for s in body.strip().split(b',')]

        headers = headers.replace(b' ', b'').replace(
                                  b':', b';').replace(b'/', b';').split(b';')
        self.score = float(headers[2])

    def get_score(self):
        return self.score

    def get_symbols(self):
        return self.symbols

    def is_spam(self, level=5):
        return self.score is None or self.score > level
