# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import numpy.ma as ma
from collections import OrderedDict, namedtuple
import os.path as path

def kformats():
    Kformat = namedtuple('Kformat', ['label', 'pos', 'na'])
    formats = {}
    for k in ('KF', 'KG', 'KL', 'KX'):
        p, n = path.split(path.abspath(__file__))
        f = open(path.join(p , '{}.txt'.format(k)))
        try:
            K = Kformat([], [], [])
            for i, line in enumerate(f, 1):
                line = line.strip()
                fields = line.split()
            #    print fields
            #    print fields[0:3], fields[3:-4], fields[-4:]
                ind, ke, label = fields[0:3]
                pos, ok, na = fields[-3:]
        #        print ind, ke, label, pos, ok, na
                if label != 'Q' and label in K.label:
                    raise ValueError('label {} defined twice'.format(label))
                K.label.append(label)
                K.pos.append(int(pos) - 1)
                K.na.append(na)

        except Exception as e:
            raise Exception('error in {}:{}'.format(f, i), e)
        f.close()

#        print K
        formats[k] = K
    return formats

#formats = kformats()
#print formats
#quit()
#
#f = open('../kl_10291_00_akt_txt.txt')
#for i, line in enumerate(f, 1):
#    line = line.strip()
##    if i > 3:        break
##    print line
#    fo = formats[line[0:2]]
#    data = OrderedDict()
#    for i in xrange(len(fo.pos) - 1):
#        l = fo.label[i]
#        if l == 'Q' or l == 'NULL': continue
#        p1 = fo.pos[i]
#        p2 = fo.pos[i + 1]
#        v = line[p1:p2].strip()
#        if v == fo.na[i]:
#            v = np.nan
#        data[l] = v
#    for k, v in data.iteritems():
#        print '{}={} '.format(k, v),
#    print
#
#
#f.close()


#import argparse
#
#parser = argparse.ArgumentParser(description = 'Process some integers.')
#parser.add_argument('integers', metavar = 'N', type = int, nargs = '+',
#                   help = 'an integer for the accumulator')
#parser.add_argument('--sum', dest = 'accumulate', action = 'store_const',
#                   const = sum, default = max,
#                   help = 'sum the integers (default: find the max)')
#
#args = parser.parse_args()
#print args.accumulate(args.integers)


import win32com.client as cl
import pythoncom

libad = cl.DispatchEx('LIBADX.LibadX.1')
print 'version', libad.GetVersion()
#libad.AboutBox()

lfx = libad.FileOpen('c:\\Users\\al\\Desktop\\samples\\5-signals.lfx')
print lfx
#print lfx.QueryInterface('{B11D9B41-3E5B-11D2-960B-006097B81D3E}')
lfx.Close()


