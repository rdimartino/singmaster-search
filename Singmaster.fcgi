#!/usr/bin/python
from flup.server.fcgi import WSGIServer
from app import app

import sys

fsock = open('errors.log', 'a')
sys.stderr = fsock
fsock.write('\n--------------------------------------------------\n')

if __name__ == '__main__':
    WSGIServer(app, bindAddress='/tmp/singmaster-fcgi.sock').run()
