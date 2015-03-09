# ctplot

ctplot is a tool to create various kinds plots from and to perform
statistical analysis on tabular data stored in HDF5 files. The plots
are created from the command line or via an interactive web interface.

Included is an extensible tool to convert raw data into HDF5 tables.

## installation
To install ctplot, download the ZIP, extract it and run `setup.py` or just do

    # pip install https://github.com/quantenschaum/ctplot/archive/master.zip
  
  
## use with apache
To use ctplot with an Apache webserver, put a `ctplot.wsgi` somewhere on your server.

    #!/usr/bin/env python

    from ctplot.wsgi import application

    # this allows the WSGI app to be run as CGI script
    if __name__ == '__main__':
        import wsgiref.handlers
        wsgiref.handlers.CGIHandler().run(application)

Set the following environment variables to configure the directories

    CTPLOT_BASEDIR=/data
    CTPLOT_DATADIR=/data/data
    CTPLOT_CACHEDIR=/data/cache
    CTPLOT_PLOTDIR=/data/plots
    CTPLOT_SESSIONDIR=/data/sessions

It's only neccessary to set `CTPLOT_BASEDIR`. The other paths are subdirectories of basedir, which can be overridden by setting them explicitly.

### run with mod_wsgi
Enable [mod_wsgi](https://code.google.com/p/modwsgi) and in your apache config set a `WSGIScriptAlias` like

    WSGIApplicationGroup %{GLOBAL}
    WSGIDaemonProcess ctplot processes=2 threads=20
    WSGIScriptAlias /ctplot /path/to/ctplot.wsgi
    
Set `processes` to the number of plot creating processes that are allowed to run in parallel (number of cores).

### run as cgi-script
To run ctplot as simple CGI script with [mod_wsgi](http://httpd.apache.org/docs/current/mod/mod_cgi.html), rename `ctplot.wsgi` to `ctplot.py` (or what ever you prefer), put it into your server tree and register it with a CGI handler. 

### run as stand alone app
Run `ctserver` (needs tornado) to run ctplot as standalone webserver, then open http://localhost:8080.

You may set `CTPLOT_PORT` to set a port different from 8080.

