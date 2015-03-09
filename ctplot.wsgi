#!/usr/bin/env python

from ctplot.wsgi import application

# environment variables
# CTPLOT_BASEDIR=/ctplot
# CTPLOT_DATADIR=/ctplot/data
# CTPLOT_CACHEDIR=/ctplot/cache
# CTPLOT_PLOTDIR=/ctplot/plots
# CTPLOT_SESSIONDIR=/ctplot/sessions
# CTPLOT_BASEDIR defaults to CWD.
# It's only neccessary to set `CTPLOT_BASEDIR`. The other paths are subdirectories of basedir, which can be overridden by setting them explicitly.

# this allows the WSGI app to be run as CGI script
if __name__ == '__main__':
    import wsgiref.handlers
    wsgiref.handlers.CGIHandler().run(application)
