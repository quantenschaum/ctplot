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
import math, numpy
from numpy import arange, linspace, logspace, random
import dateutil.parser as dp

_safe_globals = {"__builtins__":None}

# add safe symbols to locals (like math.*) 
_safe_locals = {}
for k, v in math.__dict__.iteritems():
    if not k.startswith('_'):
        _safe_locals[k] = v

#add any needed builtins back in. 
for k in ['abs', 'all', 'any', 'bool', 'cmp', 'complex', 'float', 'int', 'len', 'max', 'min', 'pow', 'reduce', 'round',
          'sum', 'zip', 'True', 'False', 'range', 'xrange', 'arange', 'linspace', 'logspace', 'random']:
    _safe_locals[k] = eval(k)

def logbins(start, stop, count):
    return [numpy.exp(x) for x in linspace(numpy.log(start), numpy.log(stop), count)]

_safe_locals['logbins'] = logbins

def date(s):
    return (dp.parse(s) - dp.parse('2004-01-01 00:00 +01')).total_seconds()

_safe_locals['date'] = date

class safeeval:
    def __init__(self, safe_globals = _safe_globals, safe_locals = _safe_locals):
        self.globals = safe_globals.copy()
        self.locals = safe_locals.copy()

    def __setitem__(self, key, value):
        self.locals[key] = value

    def __getitem__(self, key):
        return self.locals[key]

    def __delitem__(self, key):
        del self.locals[key]

    def __call__(self, expr):
#        print 'safeval', expr
        return eval(expr, self.globals, self.locals)

