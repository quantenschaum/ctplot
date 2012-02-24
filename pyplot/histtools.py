# -*- coding: utf-8 -*-
'''
Created on 25.10.2011

@author: al
'''
import pylab as p
import numpy as n
import matplotlib as mpl
from dashi.infobox import InfoBox
from collections import OrderedDict
import dashi.histfuncs
from utils import get_args_from, set_defaults
import dashi.histogram
import dashi.scatterpoints
from math import log10, floor, ceil

def _get_bincontent(hist, cumulative = 0):
    cumulative = float(cumulative)
    if cumulative > 0:
        bincontent = n.cumsum(hist.bincontent)
        binerror = n.sqrt(n.cumsum(hist.binerror ** 2))
    elif cumulative < 0:
        bincontent = hist.bincontent.sum() - n.cumsum(hist.bincontent)
        binerror = n.sqrt((hist.binerror ** 2).sum() - n.cumsum(hist.binerror ** 2))
    else:
        bincontent = hist.bincontent
        binerror = hist.binerror

    return bincontent, binerror

def _get_step_points(bincontent, binedges):
    nbins = len(bincontent)
    xpoints = n.zeros(2 * (nbins + 1), dtype = float)
    ypoints = n.zeros(2 * (nbins + 1), dtype = float)

    for i in xrange(nbins):
        xpoints[1 + 2 * i] = binedges[i]
        xpoints[2 + 2 * i] = binedges[i + 1]
        ypoints[1 + 2 * i] = bincontent[i]
        ypoints[2 + 2 * i] = bincontent[i]

    xpoints[0] = binedges[0]
    ypoints[0] = 0
    xpoints[-1] = binedges[-1]
    ypoints[-1] = 0
    # TODO eventually add another point to close area?
    return xpoints, ypoints

def _adjust_limits(xy, data, limits = None, marl = 0.05, maru = 0.05):
    lim = getattr(p, xy + 'lim')
    if not limits:
        limits = lim()
    mi, ma = limits
    mind = min(data)
    maxd = max(data)
    span = maxd - mind
    lim(min(mi, min(data) - marl * span), max(ma, max(data) + maru * span))


def h1plot(self, **kwargs):
    o = get_args_from(kwargs, style = 'hsteps', log = False, cumulative = 0, xerr = None, yerr = None, capsize = None)

    bincontent, binerror = _get_bincontent(self, o.cumulative)

    if 'line' in o.style:
        xpoints = self.bincenters
        ypoints = bincontent
    else:
        xpoints, ypoints = _get_step_points(bincontent, self.binedges)

    if o.style.startswith('f'):
        line, = p.fill(xpoints, ypoints, **kwargs)
        c = line.get_ec()
    elif o.style.startswith('h'):
        line, = p.plot(xpoints, ypoints, **kwargs)
        c = line.get_c()
    elif o.style.startswith('s'):
        pargs = set_defaults(kwargs, linestyle = '', marker = '.')
        if o.capsize is None:
            o.capsize = 3
        if o.xerr is None:
            o.xerr = True
        if o.yerr is None:
            o.yerr = True
        line, = p.plot(self.bincenters, bincontent, **pargs)
        c = line.get_c()
    else:
        raise ValueError('unknown style: ' + o.style)

    if o.xerr or o.yerr:
        pargs = set_defaults(kwargs, capsize = o.capsize, ecolor = c)
        xerr = self.binwidths / 2 if o.xerr else None
        yerr = binerror if o.yerr else None
        p.errorbar(self.bincenters, bincontent, xerr = xerr, yerr = yerr, fmt = None, **pargs)

    if o.log:
        p.gca().set_yscale('log')

    _adjust_limits('x', self.binedges)
    _adjust_limits('y', bincontent + binerror, marl = 0)

def h2plot(self, **kwargs):
    o = get_args_from(kwargs, style = 'img', log = False, cbfrac = 0.04, cblabel = 'bincontent', levels = 10)
    filled = o.style.startswith('i') or ('fill' in o.style)
    o.update(get_args_from(kwargs, hidezero = o.log or filled, colorbar = filled, clabels = not filled))

    bincontent = self.bincontent.T.copy()
    if o.hidezero:
        bincontent[bincontent == 0] = n.nan # don't show empty bins

    if o.log:
        bincontent = n.log10(bincontent)
        o.cblabel = 'log10(' + o.cblabel + ')'

    if o.style.startswith('i'):
        pargs = set_defaults(kwargs, cmap = 'jet', aspect = 'auto', interpolation = 'nearest')
        p.imshow(bincontent, origin = "lower",
                 extent = (self.binedges[0][0], self.binedges[0][-1], self.binedges[1][0], self.binedges[1][-1]),
                 **pargs)
    else:
        pargs = set_defaults(kwargs, cmap = 'jet')
        if not isinstance(pargs['cmap'], mpl.colors.Colormap):
            pargs['cmap'] = mpl.cm.get_cmap(pargs['cmap'])

        if filled:
            cs = p.contourf(self.bincenters[0], self.bincenters[1], bincontent, o.levels, **pargs)
        else:
            cs = p.contour(self.bincenters[0], self.bincenters[1], bincontent, o.levels, **pargs)
            if o.clabels:
                p.clabel(cs, inline = 1)

    if o.colorbar:
        cb = p.colorbar(fraction = o.cbfrac, pad = 0.01, aspect = 40)
        cb.set_label(o.cblabel)


















_stats2view = OrderedDict([('nentries', 'N'), ('weightsum', 'W'), ('integral', 'I'), ('neffective', 'Neff'),
                           ('mean', 'mean'), ('var', 'var'), ('std', 'std'), ('median', 'med'), ('skewness', 'skew'),
                           ('kurtosis', 'kurt'), ('excess', 'exc'), ('underflow', 'uflow'), ('overflow', 'oflow')])


_view2stats = {}
for k, v in _stats2view.iteritems():
    _view2stats[v] = k

def statbox(self, title = None, loc = 2, fields = ('N', 'mean', 'std')):
    if fields is None or len(fields) == 0:
        return

    if 'all' in fields:
        fields = _stats2view.keys()

    stringdict = OrderedDict()
    for k in fields:
            v = getattr(self.stats, _view2stats.get(k, k))
            stringdict[_stats2view.get(k, k)] = number_format(v)

    for k in ('uflow', 'oflow'):
            v = getattr(self.stats, _view2stats.get(k, k))
            if not isinstance(v, tuple) and v > 0:
                stringdict[_stats2view.get(k, k)] = number_format(v)

    if not title:
        title = None   #empty string causes pylab crash

    infobox = InfoBox(stringdict, title = title)
    infobox.draw(p.gca(), loc)


def visual():
    # hist1d augmentations 
    dashi.histogram.hist1d.plot = h1plot
    dashi.histogram.hist1d.statbox = statbox

    # hist2d augmentations
    dashi.histogram.hist2d.plot = h2plot
    dashi.histogram.hist2d.statbox = statbox
#    dashi.histogram.hist2d.contour = dashi.histviews.h2contour
#    dashi.histogram.hist2d.stack1d = dashi.histviews.h2stack1d

    # scatterpoints augmentations
#    dashi.scatterpoints.points2d.scatter = dashi.histviews.p2dscatter
#    dashi.scatterpoints.grid2d.imshow = dashi.histviews.g2dimshow

    # other 
#    dashi.fitting.model.parbox = dashi.histviews.modparbox


