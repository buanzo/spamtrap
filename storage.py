#!/usr/bin/env python3
import json

from pprint import pprint

from util import Util

import datetime


class StorageDecorators():
    def must_be_valid_database(f):
        def wrapper(*args, **kw):
            _self = args[0]
            if _self.db is not None:
                return f(*args, **kw)
            else:
                raise
        return(wrapper)


class Storage():
    def __init__(self):
        self.db = None
        self.FILEPATH = 'spamtrapdb.json'
        self.INITIALSTRUCTURE = {'spamtrap': {'config': {},
                                              'fromstats': {},
                                              'status': {},
                                              },
                                 }
        self.openDatabase()

    def openDatabase(self):
        try:
            with open(self.FILEPATH) as f:
                self.db = json.loads(f.read())
                print("[INFO:Storage] Database opened")
        except:
            print("[WARN:Storage] Initializing new database")
            self.db = self.INITIALSTRUCTURE

    @StorageDecorators.must_be_valid_database
    def saveDatabase(self):
        try:
            with open(self.FILEPATH, 'w') as f:
                f.write(json.dumps(self.db))
                print("[INFO:Storage] Database closed")
        except:
            print('[ERROR:Storage] Cannot write to database')

    @StorageDecorators.must_be_valid_database
    def closeDatabase(self):
        self.db = None

    @StorageDecorators.must_be_valid_database
    def increment_from(self, _from=None):
        if _from is None:
            return
        fs = self.db['spamtrap']['fromstats']
        if _from in fs:
            fs[_from] += 1
        else:
            fs[_from] = 1
        self.saveDatabase()

    @StorageDecorators.must_be_valid_database
    def updateExecutionTime(self):
        if 'status' not in self.db['spamtrap']:
            self.db['spamtrap']['status'] = {}
        fs = self.db['spamtrap']['status']
        fs['last_execution'] = str(datetime.datetime.now())
        self.saveDatabase()

    @StorageDecorators.must_be_valid_database
    def updateTrappedTime(self):
        if 'status' not in self.db['spamtrap']:
            self.db['spamtrap']['status'] = {}
        fs = self.db['spamtrap']['status']
        fs['last_trapped'] = str(datetime.datetime.now())
        self.saveDatabase()

    @StorageDecorators.must_be_valid_database
#    @StorageDecorators.must_have_contents_in('fromstats')
    def getSendersDict(self):
        if 'fromstats' not in self.db['spamtrap']:
            return(None)
        if isinstance(self.db['spamtrap']['fromstats'], dict):
            r = []
            for x in self.db['spamtrap']['fromstats']:
                try:
                    r.append(Util.extract_address(x))
                except:
                    continue
            return(r)
        return(None)

if __name__ == '__main__':
    db = Storage()
    db.updateExecutionTime()
    db.saveDatabase()
