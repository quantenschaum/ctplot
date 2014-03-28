#!/usr/bin/env python

# Have a look at https://pythonhosted.org/setuptools
# http://stackoverflow.com/questions/7522250/how-to-include-package-data-with-setuptools-distribute
# http://stackoverflow.com/questions/1231688/how-do-i-remove-packages-installed-with-pythons-easy-install

from ez_setup import use_setuptools
use_setuptools()

import os
from subprocess import check_output
from setuptools import setup, find_packages
from pkg_resources import resource_string, resource_filename


try:
    import dateutil
except:
    print """========================================================================
              !!! dateutil is not installed !!!
To install dateutil, follow the instructions at 
     http://labix.org/python-dateutil
This has to be done manually, because dateutil is not on the PyPI.
========================================================================
"""
    raise


# What is this? See
#   https://pythonhosted.org/setuptools/setuptools.html#non-package-data-files
#   http://peak.telecommunity.com/DevCenter/PythonEggs#accessing-package-resources

def readme(name):
    """Utility function to read the README file.
       Used for the long_description.  It's nice, because now
       1) we have a top level README file and
       2) it's easier to type in the README file than to put a raw string in below"""
    return resource_string(__name__, name)

def update_version():
    try:
        cwd = os.path.dirname(__file__)
        version = check_output('git describe --dirty=*', shell = True, cwd = cwd).strip()[1:]
        version_py = 'ctplot/__version__.py'
        with open(os.path.join(cwd, version_py), 'w') as f:
            f.write("__version__ = '{}'\n".format(version))
        print 'updated', version_py, 'to', version
    except:
        pass

update_version()

import ctplot

setup(
    name = ctplot.__name__,
    version = ctplot.__version__,
    author = ctplot.__author__,
    author_email = ctplot.__author_email__,
    description = ctplot.__description__,
    license = ctplot.__license__,
    url = ctplot.__url__,
    packages = find_packages(),
    long_description = readme('README.md'),
    install_requires = ['matplotlib >=1.1', 'numpy >=0.9', 'scipy >=0.12', 'pytz', 'tables >=2.2', 'numexpr >=1.4', 'pil >=1.1', 'basemap >=1.0'],
    entry_points = {'console_scripts':[
                        'rawdata=ctplot.rawdata:main',
                        'mergedata=ctplot.merge:main',
                        'ctplot=ctplot.plot:main'
                   ]},
    package_data = {
                    'ctplot':['web/*.*', 'web/*/*.*', 'web/*/*/*.*']
                   },
    zip_safe = True
)



