import os
import sys
import pytz
import utils

s = utils.get_scanner()

tzberlin = pytz.timezone('Europe/Berlin')
for p, ds, fs in os.walk('../zeuthen-weather'):
    for f in fs:
        fi = open(os.path.join(p, f))
        fo = open(os.path.join('.', f), 'w')
        out = fo
        print f
        lastdt = None
        n = 0
        for i, line in enumerate(fi, 1):
            try:
                line = line.strip()
                if line.startswith('#') or not line:
                    continue
                data = s.scan(line)[0]
    #            print data
                dt = data[0]
                dt = data[0] = tzberlin.localize(dt.replace(tzinfo = None))
                if lastdt:
                    if not lastdt < dt:
                        print >> sys.stderr, 'timestamp error in %s:%s' % (f, i)
                lastdt = dt
                if n:
                    assert len(data) == n
                else:
                    n = len(data)
                print >> out, '%-35s' % (dt.isoformat().replace('T', ' '),),
                data = tuple(data[1:])
                print >> out, '\t%6s' * len(data) % data
            except Exception as e:
                raise Exception('%s:%s: %s %s' % (f, i, e.args, data))
        fi.close()
        fo.close()
print 'DONE'
