#!/usr/bin/env python3
from pprint import pprint

import validators


class Util():
    @classmethod
    def input_sn(self, msg='', default='n'):
        opciones = 'S/n' if default.lower() in ('s', 'si') else 's/N'
        opcion = input("%s (%s) " % (msg, opciones))
        vals = ('s', 'si', '') if opciones == 'S/n' else ('s', 'si')
        return(opcion.strip().lower() in vals)

    @classmethod
    def extract_address(self, addrline):
        addrline = addrline.lower().strip()
        if addrline.count('@') > 0:
            if addrline.count('<') > 0:
                addr = addrline.split('<')[1].split('>')[0]
            else:
                addr = addrline
            return(addr)
        else:
            return(None)

if __name__ == '__main__':
    u = Util()
