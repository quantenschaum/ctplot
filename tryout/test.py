#!/opt/python/bin/python
#!/usr/bin/python
#!c:\Program Files (x86)\Python27\python.exe
# -*- coding: utf-8 -*-
'''
Created on 27.10.2011
@author: al
webinterface to plotting tools
'''
import os
import sys
import getpass

if __name__ == '__main__':
    print "Content-Type: text/plain;charset=utf-8"
    print

    print "Hallo!"
    print "Ich bin nur ein Text. "
    print 'pwd', os.path.abspath('.')
    print '~', os.path.expanduser("~")
    print 'user', getpass.getuser()
    for e in sys.path:
        print e

    for e in os.environ.iteritems():
        print e

    print sys.exc_info()



