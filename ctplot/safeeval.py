# -*- coding: utf-8 -*-
#    pyplot - python based data plotting tools
#    created for DESY Zeuthen
#    Copyright (C) 2012  Adam Lucke  software@louisenhof2.de
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>. 
#
#    $Id$
#
from numpy import *
import dateutil.parser as dp

_safe_globals = {"__builtins__":None}
_safe_locals = {}

#add any needed builtins back in. 
for k in ['abs', 'all', 'any', 'bool', 'cmp', 'complex', 'float', 'int', 'len', 'max', 'min', 'pow', 'reduce', 'round',
          'sum', 'zip', 'True', 'False', 'range', 'xrange', 'arange', 'linspace', 'logspace', 'random',
          'power', 'log', 'log10', 'log2', 'exp', 'sin', 'cos', 'tan', 'floor', 'ceil']:
    _safe_locals[k] = eval(k)

def logbins(start, stop, count):
    return [exp(x) for x in linspace(log(start), log(stop), count)]

_safe_locals['logbins'] = logbins

def date(s):
    return (dp.parse(s) - dp.parse('2004-01-01 00:00 +01')).total_seconds()

_safe_locals['date'] = date

class safeeval:
    def __init__(self, safe_globals = _safe_globals, safe_locals = _safe_locals):
        self.globals = safe_globals.copy()
        self.globals.update(safe_locals)
        self.locals = {}

    def __setitem__(self, key, value):
        self.locals[key] = value

    def __getitem__(self, key):
        return self.locals[key]

    def __delitem__(self, key):
        del self.locals[key]

    def __call__(self, expr):
#        print 'safeval', expr
        return eval(expr, self.globals, self.locals)

if __name__ == '__main__':
    for k, v in _safe_locals.iteritems():
        print k, v

