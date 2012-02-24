#!/usr/bin/python
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
import os, sys, re, json, tables, ticks
from collections import OrderedDict, namedtuple
import numpy as np
import numpy.ma as ma
import matplotlib as mpl
import matplotlib.pyplot as plt
from utils import get_args_from, isseq, set_defaults, number_mathformat
from itertools import product
from safeeval import safeeval

# override eval by safe version
eval = safeeval()


TableSpecs = namedtuple('TableSpecs', ('title', 'colnames', 'units', 'rows'))

def available_tables(d = os.path.dirname(__file__) + '/data'):
    files = os.listdir(d)
    files.sort()
    files = map(lambda f:os.path.join(d, f).replace('\\', '/'), files)
    files = filter(lambda f:os.path.isfile(f) and f.endswith('.h5'), files)

    tabs = OrderedDict()

    for f in files:
        h5 = tables.openFile(f, 'r')

        for n in h5.walkNodes(classname = 'Table'):
            tab = f + ':' + n._v_pathname
            tabs[tab] = TableSpecs(n._v_title, n.colnames, json.loads(n.attrs.units), int(n.nrows))

        h5.close()

    return tabs


def _get(d, k):
    v = d.get(k)
    if v:
        return v.strip() if isinstance(v, str) else v
    else:
        return

def get_binning(bins, data):
    if np.isscalar(bins):
        edges = np.linspace(np.nanmin(data), np.nanmax(data), bins + 1)
    elif isseq(bins) and len(bins) == 3:
        edges = np.linspace(bins[0], bins[1], bins[2] + 1)
    else:
        edges = np.array(bins)

    centers = (edges[1:] + edges[:-1]) / 2
    assert len(centers) == len(edges) - 1
    widths = np.diff(edges)
    return edges, centers, widths


def get_cumulative(bincontents, binerrors, cumulative = 0, binwidths = 1):
    cumulative = float(cumulative)
    if cumulative > 0:
        bincontents = np.cumsum(bincontents * binwidths)
        binerrors = np.sqrt(np.cumsum((binerrors * binwidths) ** 2))
    elif cumulative < 0:
        bincontents = np.sum(bincontents * binwidths) - np.cumsum(bincontents * binwidths)
        binerrors = np.sqrt(np.sum((binerrors * binwidths) ** 2) - np.cumsum((binerrors * binwidths) ** 2))

    return bincontents, binerrors


def get_density(bincontents, binerrors, binwidths):
    f = 1.0 / (np.sum(bincontents) * binwidths)
    bincontents = f * bincontents
    bincontents[np.logical_not(np.isfinite(bincontents))] = 0
    binerrors = f * binerrors
    return bincontents, binerrors


def get_density2d(bincontents, xwidths, ywidths):
    f = 1.0 / (np.sum(bincontents) * (xwidths * ywidths.reshape(len(ywidths), 1)))
    bincontents = f * bincontents
    bincontents[np.logical_not(np.isfinite(bincontents))] = 0
    return bincontents


def get_step_points(bincontents, binedges):
    assert len(bincontents) + 1 == len(binedges)
    x = np.zeros(2 * len(binedges), dtype = float)
    y = np.zeros(x.shape, dtype = float)
    x[::2] = binedges
    x[1::2] = binedges
    y[1:-1:2] = bincontents
    y[2:-1:2] = bincontents
    assert len(x) == len(y) == 2 * len(binedges)
    return x, y


def adjust_limits(xy, data, limits = None, marl = 0.05, maru = 0.05):
    assert xy in ('x', 'y')
    lim = getattr(plt, xy + 'lim')
    if limits is None:
        limits = lim()
    mi, ma = limits
    data = data[np.isfinite(data)]
    mind = np.min(data)
    maxd = np.max(data)
    span = maxd - mind
    lim(min(mi, min(data) - marl * span), max(ma, max(data) + maru * span))


class Plot():
    def __init__(self, **kwargs):
        print >> sys.stderr, json.dumps(kwargs)

        # configure plot according too kwargs
        for N in xrange(10):
            n = str(N)

            # x, y, z, cut, mode, source, name
            for v in 'xyzcmsn':
                self._append(v, _get(kwargs, v + n))

            # window, shift, condition
            for v in 'wsc':
                self._append('r' + v, _get(kwargs, 'r' + v + n))

            # bins
            for v, w in product('xy', 'b'):
                self._append(v + w, _get(kwargs, v + n + w))

            # plot options
            for k, v in kwargs.iteritems():
                if k.startswith('o' + n) and v:
                    a = 'o' + k[2:]
                    if not hasattr(self, a):
                        setattr(self, a, 10 * [None])
                    getattr(self, a)[N] = v.strip()

        # range, scale, label
        for v, w in product('xyz', 'rsl'):
            setattr(self, v + w, _get(kwargs, v + w))

        # title, fontsize, width, grid, legend
        for v in 'tfwgl':
            setattr(self, v, _get(kwargs, v))

        # source with rate averaging
        for i, s in enumerate(self.s):
            self._append('sr', '{}:{}:{}:{}'.format(s, self.rw[i], self.rs[i], self.rc[i]) if s else None)

        self.lines = 10 * [None]

#        for k in sorted(self.__dict__.keys()):
#            print >> sys.stderr, '*', k, self.__dict__[k]



    def _append(self, varname, value):
        'append value to self.varname'
        try:
            getattr(self, varname).append(value)
        except AttributeError:
            setattr(self, varname, [value])


    def _get(self, var, default = None):
        val = self.__dict__.get(var)
        if val is None:
            return default
        else:
            return val


    def _prepare_data(self):
        # create dict: source --> all expr for this source
        # prefilled with empty lists
        expr_data = {}
        joined_cuts = {} # OR of all cuts
        for n, s in enumerate(self.sr):
            if s:
                if s not in expr_data:
                    expr_data[s] = {}
                for v in 'xyzc':
                    expr = getattr(self, v)[n]
                    if expr:
                        expr_data[s][expr] = []
                    if v == 'c':
                        if s in joined_cuts:
                            joined_cuts[s] = '{} or ({})'.format(joined_cuts[s], expr)
                        else:
                            joined_cuts[s] = '({})'.format(expr)

                if '(None)' in joined_cuts[s]: del joined_cuts[s]

#        print >> sys.stderr, expr_data

        # loop over tables and fill data lists in expr_data
        units = {}
        self._get_data(expr_data, joined_cuts, units)
        print >> sys.stderr, units


        # assing data arrays to x/y/z/c-data fields
        for v in 'xyzc':
            setattr(self, v + 'data', [(expr_data[self.sr[i]][x] if x and self.sr[i] else None) for i, x in enumerate(getattr(self, v))])
            setattr(self, v + 'unit', [(units[self.sr[i]][x] if x and self.sr[i] else None) for i, x in enumerate(getattr(self, v))])

        print >> sys.stderr, 'source', self.s
        print >> sys.stderr, 'srcavg', self.sr
        for v in 'xyzc':
            print >> sys.stderr, ' ' + v + 'data', [len(x) if x is not None else None for x in getattr(self, v + 'data')]
            print >> sys.stderr, ' ' + v + 'unit', [x for x in getattr(self, v + 'unit')]



    def _get_data(self, expr_data, filters, units = {}):
        # compile and evaluate expressions for each source
        for s, exprs in expr_data.iteritems():
            print >> sys.stderr, 'processing source', s
            print >> sys.stderr, '      expressions', exprs.keys()
            print >> sys.stderr, '           filter', filters[s] if s in filters else None

            # source s has form 'filename:/path/to/table'
            # open HDF5 table
            ss = s.strip().split(':')
            h5 = tables.openFile(ss[0], 'r')
            table = h5.getNode(ss[1])

            window = float(eval(ss[2])) if ss[2] != 'None' else None
            shift = float(ss[3]) if ss[3] != 'None' else 1
            condition = ss[4] if ss[4] != 'None' else None
#            print 'wsc', window, shift, condition

            table_units = tuple(json.loads(table.attrs.units))

            def unit(var):
                try:
                    return table_units[table.colnames.index(var.strip())]
                except:
                    return '?'

            units[s] = dict([(e, unit(e)) for e in exprs.keys()])



            # restricted eval, allowing only safe operations


            def compile_function(x):
                fields = set(table.colnames)
                fields.add('rate')
                fields.add('count')
                for v in fields: # map T_a --> row['T_a'], etc.
                    x = re.sub('(?<!\\w)' + re.escape(v) + '(?!\\w)',
                                'row["' + v + '"]', x)
#                print >> sys.stderr, 'expression: ', x
                return eval('lambda row: ' + x)

            # compile the expressions
            exprs = dict([(compile_function(e), d) for e, d in exprs.iteritems()])

            def average(data):
                assert 0 < shift <= 1
                av = dict.fromkeys(table.colnames, 0)
                it = table.colnames.index('time') # index of time column
                ta = table[0][it] # window left edge
                tb = ta + window # window right edge
                wd = [] # window data
                if condition:
                    cc = compile_function(condition)
                for row in data:
                    if not condition or cc(row):
                        if row[it] < tb: # add row if in window
                            wd.append(row[:])
                        else: # calculate av and shift window
                            n = len(wd)
                            if n > 0:
                                for i, c in enumerate(table.colnames):
                                    a = 0
                                    for d in wd:
                                        a += d[i]
                                    av[c] = a / float(n)
                                av['time'] = (ta + tb) * 0.5
                                av['count'] = n
                                av['rate'] = n / window
                                yield av

                            ta += shift * window # shift window
                            tb = ta + window
                            if row[it] >= tb:
                                ta = row[it] # shift window
                                tb = ta + window
                            wd.append(row[:])
                            wd = filter(lambda x:ta <= x[it] < tb, wd) # remove data left outside window


            def prefilter(data, filterexpr):
                filterexpr = compile_function(filterexpr)
                for row in data:
                    if filterexpr(row):
                        yield row


            # iterator over table rows, apply filter if present
            tableiter = table.iterrows()

            if window:
                tableiter = average(tableiter)

            if s in filters:
                tableiter = prefilter(tableiter, filters[s])

            for row in tableiter:
                for expr, data in exprs.iteritems():
                    data.append(expr(row))

            h5.close()

            # convert data lists to numpy arrays
            d = expr_data[s]
            for k in d.keys():
                d[k] = np.array(d[k])



    def _configure_pre(self):
        # configure plotlib
        self.f = float(self._get('f', 10))
        plt.rc('font', **{'family':'sans-serif', 'sans-serif':['Dejavu Sans'], 'size':self.f})
        plt.rc('axes', grid = True)
        plt.rc('lines', markeredgewidth = 0)
        ticks.set_extended_locator(1)
        w = self.w = float(self._get(self.w, 10))
        plt.gcf().set_size_inches((w, w / np.sqrt(2)));
        f = 0.09
        plt.gca().set_position([f, f, 1 - 2 * f, 1 - 2 * f])

        #set scales        
        if self.xs:
            plt.gca().set_xscale(self.xs)

        if self.ys:
            plt.gca().set_yscale(self.ys)


    def _configure_post(self):
        # title
        if self.t: plt.title(self.t, fontsize = 1.4 * self.f)

        # labels
        plt.xlabel(self.alabel('x'))
        plt.ylabel(self.alabel('y'))

        # ranges
        if self.xr: plt.xlim(eval(self.xr))
        if self.yr: plt.ylim(eval(self.yr))

        # grid
        if self.g: plt.grid(eval(self.g))

        # legend
        self.l = int(self.l) if self.l else 0
        lines, names = [], []
        for i, l in enumerate(self.lines):
            if l:
                lines.append(l)
                names.append(self.llabel(i))
        if len(lines) > 0 and 'map' not in self.m :
            plt.legend(tuple(lines), tuple(names), loc = self.l)





    def data(self, i):
        x, y, z, c = self.xdata[i], self.ydata[i], self.zdata[i], self.cdata[i]
        if c is not None:
            if x is not None: x = x[c]
            if y is not None: y = y[c]
            if z is not None: z = z[c]
        return x, y, z


    def opts(self, i):
        o = {}
        for k, v in self.__dict__.iteritems():
            if k.startswith('o') and v[i] is not None:
                try:
                    o[k[1:]] = eval(v[i])
                except:
                    o[k[1:]] = v[i]
        return o


    def bins(self, i, a):
        try:
            b = getattr(self, a + 'b')[i]
            if b: return eval(b)
            else: raise
        except:
            return 10



    def llabel(self, i):
        l = self.n[i]
        if l: return l
        l = ''
        for v in 'xyzc':
            w = getattr(self, v)[i]
            if w: l += ':' + w
        return l[1:]


    def alabel(self, a):
        l = getattr(self, a + 'l')
        if l: return l
        l = ''
        for x, u in zip(getattr(self, a), getattr(self, a + 'unit')):
            if x and x not in l: l += u', {} [{}]'.format(x, u)
        return l[2:]



    def plot(self):
        self._prepare_data()
        self._configure_pre()
        for i, m in enumerate(self.m):
            if m:
                if m == 'xy':
                    self._xy(i)
                elif m == 'h1':
                    self._hist1d(i)
                elif m == 'h2':
                    self._hist2d(i)
                elif m == 'p':
                    self._profile(i)
                elif m == 'map':
                    self._map(i)
                else:
                    raise RuntimeError('unknow mode ' + m)
        self._configure_post()

        print >> sys.stderr, self.n
        print >> sys.stderr, self.lines


    def show(self):
        if not any(self.lines):
            self.plot()
        plt.show()


    def save(self, name = 'fig', extensions = ('png', 'pdf', 'svg')):
        plt.ioff()
        if not any(self.lines):
            self.plot()
        names = []
        for ext in extensions:
            n = name + '.' + ext
            plt.savefig(n, bbox_inches = 'tight')
            names.append(n)

        return dict(zip(extensions, names))




    def _xy(self, i):
        print >> sys.stderr, 'xy plot of', i, [getattr(self, v)[i] for v in 'sxyzc']
        kwargs = self.opts(i)
        x, y, z = self.data(i)

        if x is not None:
            args = (x, y)
        else:
            args = (y,)

        if z is None:
            self.lines[i], = plt.plot(*args, **kwargs)
        else:
            o = get_args_from(kwargs, markersize = 2, cbfrac = 0.04, cblabel = self.z[i])
            self.lines[i] = plt.scatter(x, y, c = z, s = o.markersize ** 2, edgecolor = 'none', **kwargs)

            m = 6.0
            dmin, dmax = np.nanmin(z), np.nanmax(z)
            cticks = ticks.get_ticks(dmin, dmax, m, only_inside = 1)
            formatter = mpl.ticker.FuncFormatter(func = lambda x, i:number_mathformat(x))
            cb = plt.colorbar(fraction = o.cbfrac, pad = 0.01, aspect = 40, ticks = cticks, format = formatter)
            cb.set_label(o.cblabel)


    def _hist1d(self, i):
        self.plotted_lines = []
        print >> sys.stderr, '1D histogram of', i, [getattr(self, v)[i] for v in 'sxyzc']
        kwargs = self.opts(i)
        x, y, z = self.data(i)

        o = get_args_from(kwargs, density = False, cumulative = 0)
        o.update(get_args_from(kwargs, style = 'histline' if o.density else 'hist'))
        err = 0 #o.style.startswith('s')
        o.update(get_args_from(kwargs, xerr = err, yerr = err, capsize = 3 if err else 0))

        binedges, bincenters, binwidths = get_binning(self.bins(i, 'x'), x)

        bincontents, _d1 = np.histogram(x, binedges)
        assert np.all(binedges == _d1)
        binerrors = np.sqrt(bincontents)

        if o.density:
            bincontents, binerrors = get_density(bincontents, binerrors, binwidths)

        if o.cumulative:
            bincontents, binerrors = get_cumulative(bincontents, binerrors, o.cumulative, binwidths if o.density else 1)

        if 'line' in o.style:
            x = bincenters
            y = bincontents
        else:
            x, y = get_step_points(bincontents, binedges)

        if 'fill' in o.style:
            line, = plt.fill(x, y, **kwargs)

        elif 'hist' in o.style:
            line, = plt.plot(x, y, **kwargs)

        elif 'scat' in o.style:
            pargs = set_defaults(kwargs, linestyle = '', marker = '.')
            line, = plt.plot(bincenters, bincontents, **pargs)

        else:
            raise ValueError('unknown style: ' + o.style)

        if o.xerr or o.yerr:
            pargs = set_defaults(kwargs, capsize = o.capsize, ecolor = line.get_c())
            xerr = 0.5 * binwidths if o.xerr else None
            yerr = binerrors if o.yerr else None
            plt.errorbar(bincenters, bincontents, yerr, xerr, fmt = None, **pargs)


        adjust_limits('x', binedges)
        adjust_limits('y', bincontents + binerrors, marl = 0)

        self.lines[i] = line



    def _hist2d(self, i):
        print >> sys.stderr, '2D histogram of', i, [getattr(self, v)[i] for v in 'sxyzc']
        kwargs = self.opts(i)
        x, y, z = self.data(i)
        o = get_args_from(kwargs, style = 'color', density = False, log = False, cbfrac = 0.04, cblabel = 'bincontent', levels = 10)
        filled = 'color' in o.style or ('fill' in o.style)
        o.update(get_args_from(kwargs, hidezero = o.log or filled, colorbar = filled, clabels = not filled))

        # make binnings
        xedges, xcenters, xwidths = get_binning(self.bins(i, 'x'), x)
        yedges, ycenters, ywidths = get_binning(self.bins(i, 'y'), y)

        bincontents, _d1, _d2 = np.histogram2d(x, y, [xedges, yedges])
        bincontents = np.transpose(bincontents)
        assert np.all(_d1 == xedges)
        assert np.all(_d2 == yedges)

        if o.density:
            bincontents = get_density2d(bincontents, xwidths, ywidths)

        if o.hidezero:
            bincontents[bincontents == 0] = np.nan

        if o.log:
            bincontents = np.log10(bincontents)
            formatter = mpl.ticker.FuncFormatter(func = lambda x, i:number_mathformat(np.power(10, x)))
        else:
            formatter = mpl.ticker.FuncFormatter(func = lambda x, i:number_mathformat(x))

        if 'color' in o.style:
            pargs = set_defaults(kwargs, cmap = 'jet', edgecolor = 'none')
            plt.pcolor(xedges, yedges, ma.array(bincontents, mask = np.isnan(bincontents)), **kwargs)

        elif 'box' in o.style:
            pargs = set_defaults(kwargs, color = (1, 1, 1, 0), marker = 's', edgecolor = 'k')
            n = bincontents.size
            s = bincontents.reshape(n)
            s = s / np.nanmax(s) * (72. / 2. * self.plotwidth / max(len(xcenters), len(ycenters))) ** 2
            xcenters, ycenters = np.meshgrid(xcenters, ycenters)
            plt.scatter(xcenters.reshape(n), ycenters.reshape(n), s = s, **pargs)

        elif 'contour' in o.style:
            pargs = set_defaults(kwargs, cmap = 'jet')
            if not isinstance(pargs['cmap'], mpl.colors.Colormap):
                pargs['cmap'] = mpl.cm.get_cmap(pargs['cmap'])

            if filled:
                cs = plt.contourf(xcenters, ycenters, bincontents, o.levels, **pargs)
            else:
                cs = plt.contour(xcenters, ycenters, bincontents, o.levels, **pargs)
                if o.clabels:
                    plt.clabel(cs, inline = 1)

        else:
            raise ValueError('unknown style ' + o.style)

        if o.colorbar:
            m = 6.0
            dmin, dmax = np.nanmin(bincontents), np.nanmax(bincontents)
            if o.log:
                dmin, dmax = np.ceil(dmin), np.floor(dmax) + 1
                step = max(1, np.floor((dmax - dmin) / m))
                cticks = np.arange(dmin, dmax, step)
            else:
                cticks = ticks.get_ticks(dmin, dmax, m, only_inside = 1)

            cb = plt.colorbar(fraction = o.cbfrac, pad = 0.01, aspect = 40, ticks = cticks, format = formatter)
            cb.set_label(o.cblabel)


    def _profile(self, i):
        print >> sys.stderr, 'profile of', i, [getattr(self, v)[i] for v in 'sxyzc']
        kwargs = self.opts(i)
        x, y, z = self.data(i)
        o = get_args_from(kwargs, xerr = 0, yerr = 0)

        # make x binning
        xedges, xcenters, xwidths = get_binning(self.bins(i, 'x'), x)

        # compute avg and std for each x bin
        xx = xcenters
        xerr = 0.5 * xwidths if o.xerr else None
        yy = []
        yerr = []
        for l, u in zip(xedges[:-1], xedges[1:]):
            bindata = y[(l <= x) & (x < u)]
            yy.append(np.mean(bindata))
            yerr.append(np.std(bindata))
        if not o.yerr:
            yerr = None

        pargs = set_defaults(kwargs, capsize = 3, marker = '.')
        self.lines[i], _d, _d = plt.errorbar(xx, yy, yerr, xerr, **pargs)


    def _map(self, i):
        import maps
        print >> sys.stderr, 'map of', i, [getattr(self, v)[i] for v in 'sxyzc']
        kwargs = self.opts(i)
        x, y, z = self.data(i)
        o = get_args_from(kwargs, margin = 0.05, width = 10e6, height = None, boundarylat = 50, projection = 'cyl',
                          drawcoastline = 1, drawgrid = 1, drawspecgrid = 1, drawcountries = 0, bluemarble = 0, nightshade = None)

        m = maps.drawmap(y, x, **o)
        x, y = m(x, y)

        if z is None:
            self.lines[i], = plt.plot(x, y, **kwargs)
        else:
            o = get_args_from(kwargs, markersize = 6, cbfrac = 0.04, cblabel = self.alabel('z'))
            p = set_defaults(kwargs, zorder = 100)
            self.lines[i] = plt.scatter(x, y, c = z, s = o.markersize ** 2, edgecolor = 'none', **p)

            m = 6.0
            dmin, dmax = np.nanmin(z), np.nanmax(z)
            cticks = ticks.get_ticks(dmin, dmax, m, only_inside = 1)
            formatter = mpl.ticker.FuncFormatter(func = lambda x, i:number_mathformat(x))
            cb = plt.colorbar(fraction = o.cbfrac, pad = 0.01, aspect = 40, ticks = cticks, format = formatter)
            cb.set_label(o.cblabel)


if __name__ == '__main__':



    p = Plot(
    #         m0 = 'map', x0 = 'lon', y0 = 'lat', z0 = 'time', x0b = '40', y0b = '40', c0 = '', s0 = 'data/polarstern.h5:/raw/polarstern_events',
             m1 = 'p', x1 = 'time', y1 = 'rate', o1yerr = '1', rw1 = '4000*2', x1b = '100', c1 = '', s1 = 'data/ct-2011.h5:/merged/CT_events'
             )

    #p.save()
    p.show()
