# ctplot

ctplot is a tool to create various kinds plots from and to perform
statistical analysis on tabular data stored in HDF5 files. The plots
are created from the command line or via an interactive web interface.

Included is an extensible tool to convert raw data into HDF5 tables.

## installation
To install ctplot, download the ZIP, extract it and run `setup.py` or

    # easy_install https://github.com/quantenschaum/ctplot/archive/master.zip
  
  
## use with apache
To use ctplot with an Apache webserver, copy `ctplot.wsgi` somewhere on your server.
Edit `ctplot.wsgi` and set the paths to something like

    os.environ['ctplot_basedir'] = '/basedir'
    # os.environ['ctplot_datadir'] = '/basedir/data'
    # os.environ['ctplot_cachedir'] = '/basedir/cache'
    # os.environ['ctplot_sessionsdir'] = '/basedir/sessions'
    # os.environ['ctplot_plotsdir'] = '/basedir/plots'

It's only neccessary to set `ctplot_basedir`. The other paths are subdirectories of basedir, which can be overridden by setting them explicitly.

### run with mod_wsgi
Enable mod_wsgi and in your apache config set a WSGIScriptAlias like

    WSGIApplicationGroup %{GLOBAL}
    WSGIDaemonProcess ctplot processes=2 threads=20
    WSGIScriptAlias /ctplot /path/to/ctplot.wsgi
    
Set `processes` to the number of plot creating processes that are allowed to run in parallel (number of cores).

### run as cgi-script
To run ctplot as simple CGI script (bad performance!), rename `ctplot.wsgi` to `ctplot.py` (or what ever you prefer), put it into your server tree and register it with a CGI handler. (see http://httpd.apache.org/docs/current/mod/mod_cgi.html)

### run as stand alone app
Run `webserver.py` (needs tornado) to run ctplot as standalone webserver, then open http://localhost:8080.

