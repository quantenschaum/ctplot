#!/opt/python/bin/python
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
import sys
import utils
import datetime as dt
import dateutil.parser as dp
import os
import os.path as path
from collections import OrderedDict
import pytz
import re
import tables as t
from progressbar import ProgressBar, Bar, Percentage, ETA
import math
from utils import set_attrs

__version__ = '$Rev$'.replace('$', '').replace('Rev:', '').strip()
__date__ = '$Date$'.replace('$', '').replace('Date:', '').strip()


def filescaniter(filename, validator = None):
    'returns iterator yielding tuples with data from each line'
    datafile = open(filename)

    try:
        scanner = utils.get_scanner()
        line_counter = 0
        for line in datafile:
            line_counter += 1
            line = line.strip()
            if line.startswith("#") or line == '':
                continue

            t = tuple(scanner.scan(line)[0])

            if validator is not None:
                validator(t)

            yield t

    except:
        print >> sys.stderr, "Error parsing line", line_counter, "in", datafile
        raise

    finally:
        datafile.close()

def fileiter(filename, linehandler, skip_on_assert = False, print_failures = True):
    'returns iterator yielding objects created by linehandler from each line'
    datafile = open(filename)

    try:
        for i, line in enumerate(datafile, 1):
            try:
                data = linehandler(line)
                if data is not None:
                    yield data

            except AssertionError as e:
                if not skip_on_assert:
                    raise
                else:
                    if print_failures:
                        print "%s:%d '%s'" % (filename, i, e)

    except Exception as e:
        raise RuntimeError("Error parsing line %d in %s" % (i, filename), e)

    finally:
        datafile.close()







#                          yyyy          mm                        dd          HH    MM    SS    .ss      TZname       TZoffset
datetime_re = re.compile(r"\d{4}[-./]?([A-Z][a-z]{2,}|\d{2})[-./]?\d{2}(\s+|T)\d{2}:\d{2}(:\d{2}(\.\d+)?)?(\s+[A-Z]{3,})?([+-]\d{1,2}:?(\d{2})?)?")
tz_re = re.compile('([A-Z]{3,})([+-]\d+)')
def repl(match):
    return match.group(1) + ' ' + match.group(2)

class LineHandler:
    description = '(description of the file format)'
    col_descriptor = property(lambda self: self._col_descriptor())
    col_units = property(lambda self: tuple(self.cols_and_units.values()))
    col_names = property(lambda self: tuple(self.cols_and_units.keys()))
    table_title = '(unnamed table)'

    def __init__(self):
        self.lastdt = None

    def _parse_time(self, line):
        'find a datetime stamp at the beginning of line, return (time as datetime, line with timestamp removed)'
        # find datetime stamp 
        match = re.match(datetime_re, line)
        assert match
        dt = match.group(0)
        dt = re.sub(tz_re, repl, dt)
        time = dp.parse(dt, fuzzy = True)
        # remove datetime from beginning
        line = line[len(dt):]
        return (time, line)


    def __call__(self, line):
        'parse line and return tuple with data or None if line was skipped (comment/empty)'
        line = line.strip()
        # skip comments or empty lines
        if line.startswith('#') or line == '':
            return

        # extract the datetime stamp from line and put
        # it into time as datetime and return the rest of the line
        # with the datetime stamp removed
        time, line = self._parse_time(line)

        # list containing data from line, starting with datetime stamp
        data = [time]

        # add the remaining data as floats
        parts = line.split()
        for x in parts:
            try:
                data.append(float(x))
            except: # skip everything that is not parsable as float
                pass

        self.sanitize(data) # modify data (perform cleanup, transformations, etc.)
        data = tuple(data) # freeze data (tuples are immutable)

        self.verify(data) # verify that data fulfills certain criteria
        return data

    def _verify_time(self, time):
        'verify that time > last timestamp, i.e. that the records in the datafile are in ascending time order'
        if self.lastdt is not None:
            if not time > self.lastdt:
                raise AssertionError('time <= last time: %s <= %s' % (time.isoformat(), self.lastdt.isoformat()))
        if not time.tzinfo:
                raise AssertionError('time has no tzinfo: %s' % (time.isoformat(),))
        self.lastdt = time

    def sanitize(self, data):
        pass

    def verify(self, data):
        pass

nan = float('nan')
inf = float('inf')

def verifyrange(name, value, lower = -inf, upper = +inf, can_be_nan = False):
    if not (lower <= value <= upper or (can_be_nan and math.isnan(value))):
        raise AssertionError('%s out of range: %s' % (name, value))



class WeatherHandler(LineHandler):
    description = 'Zeuthen weather data [example: 2011-01-01 07:00:00+01:00 16.6 1.5 0.0 33 90 0.7 22.5 NNE -1.0 1.5 0.0 1006.9]'
    table_name = 'zeuthen_weather'
    table_title = 'Zeuthen weather data'
    cols_and_units = OrderedDict([('time', 's'), ('T_i', 'C°'), ('T_a', 'C°'), ('T_dew', 'C°'),
                                  ('H_i', '%'), ('H_a', '%'), ('v_wind', 'm/s'), ('d_wind', '°'),
                                  ('gust', '?'), ('chill', '?'), ('rain', 'mm'), ('p', 'hPa'), ('clouds', '?')])

    start06 = dp.parse('2006-01-01 00:00:00 +0100')

    def sanitize(self, data):
        time = data[0]
        data.append(nan) # clouds, only present in pre 2006 weather data

        # replace -1 by nan, -1 means 'no data'
        for i in [4, 5, 6, 7, 8, 9, 10, 11]:
            if data[i] == -1.0:
                data[i] = nan

        # check for T_a < 0 in summer
        if 4 < time.month < 10 and data[2] == -1.0:
            data[2] = nan

        # check for invalid T_dew
        if not data[3] < data[2] and data[3] == -1.0:
            data[3] = nan

        # transform data in pre 2006 weather
        if time < WeatherHandler.start06:
            # replace -1 by nan, -1 means 'no data'
            for i in [1, 3]:
                if data[i] == -1.0:
                    data[i] = nan
            data[12] = data[5] # set clouds if < 2006
            data[4] = data[5] = nan # clear humidity

    def verify(self, data):
        # 0    1    2     3     4    5      6       7     8      9     10   11   12
        time, T_i, T_a, T_dew, H_i, H_a, v_wind, d_wind, gust, chill, rain, p, clouds = data
        self._verify_time(time)

        # there may be nan values in pre 2006 weather
        allow_nan = time < WeatherHandler.start06

        verifyrange('T_i', T_i, -50 , 50, allow_nan)
        verifyrange('T_a', T_a, -50 , 50)
        verifyrange('T_dew', T_dew, -50 , T_a - 1e-15, allow_nan)
        verifyrange('H_i', H_i, 0 , 100, True)
        verifyrange('H_a', H_a, 0 , 100, True)
        verifyrange('v_wind', v_wind, 0 , 60, True)
        verifyrange('d_wind', d_wind , 0, 360, True)
        verifyrange('gust', gust, 0 , 120, True)
        verifyrange('rain', rain, 0, can_be_nan = True)
        verifyrange('p', p , 800, 1200)
        verifyrange('clouds', clouds, 1 , 6, True)


    def _col_descriptor(self):
        return OrderedDict([(k, t.FloatCol(dflt = nan, pos = i)) for i, k in enumerate(self.col_names)])



class CTEventHandler(LineHandler):
    description = 'Cosmic Trigger event data [example: 2004-05-22 00:00:25.92+02:00   0 1 0 0   0 1 0 0   1 0 0 0]'
    table_name = 'CT_events'
    table_title = 'Cosmic Trigger events'
    cols_and_units = OrderedDict([('time', 's'), ('a1', ''), ('a2', ''), ('a3', ''), ('a4', ''),
                                  ('b1', ''), ('b2', ''), ('b3', ''), ('b4', ''),
                                  ('c1', ''), ('c2', ''), ('c3', ''), ('c4', '')])

    def verify(self, data):
        time = data[0]
        self._verify_time(time)
        triggered = data[1:]
        verifyrange('number of detector segments', len(triggered), 12 , 12)
        verifyrange('multiplicity', sum(triggered) , 3 , 12)
        verifyrange('multiplicity in level a', sum(triggered[0:4]) , 1 , 4)
        verifyrange('multiplicity in level b', sum(triggered[4:8]) , 1 , 4)
        verifyrange('multiplicity in level c', sum(triggered[8:12]) , 1 , 4)

    def _col_descriptor(self):
        descriptor = OrderedDict([(k, t.BoolCol(dflt = False, pos = i)) for i, k in enumerate(self.col_names)])
        descriptor['time'] = t.FloatCol(dflt = nan, pos = self.col_names.index('time'))
        return descriptor



class ITTEventHandler(LineHandler):
    description = 'IceTop Tank event data [example: 5 2011/10/24 09:25:54.346  V265[0]        40    16]'
    table_name = 'ITT_events'
    table_title = 'IceTop Tank events'
    cols_and_units = OrderedDict([('time', 's'), ('dom1', ''), ('dom2', ''), ('run', ''), ('time2', 's'),
                                  ('a1', ''), ('a2', ''), ('a3', ''), ('a4', ''),
                                  ('b1', ''), ('b2', ''), ('b3', ''), ('b4', '')])

    _leading_int = re.compile('(^[+-]?\\d+)\\s+(.*)')

    def __init__(self):
        LineHandler.__init__(self)
        self.expecting_second_part = False

    def __call__(self, line):
        'parse line and return tuple with data or None if line was skipped (comment/empty)'
        line = line.strip()
        # skip comments or empty lines
        if line.startswith('#') or line == '':
            return

        # extract leading int
        m = self._leading_int.match(line)
        i = int(m.group(1))
        line = m.group(2)# line w/o leading int
        if i <= 0:
            if i == 0:
                parts = line.split()
                if len(parts) == 4 and parts[0] == 'Run':
                    self.run = int(parts[1])
            return

        # extract the datetime stamp from line and put
        # it into time as datetime and return the rest of the line
        # with the datetime stamp removed
        time, line = self._parse_time(line)

        # list containing data from line, starting with datetime stamp
        data = [time]

        # add the remaining data as floats
        parts = line.split()
        for x in parts:
            try:
                data.append(float(x))
            except: # skip everything that is not parsable as float
                pass

        if self.expecting_second_part:
            self.expecting_second_part = False
            assert self.i == i
#            assert self.data[0] == data[0]
            assert len(data) == 9
            self.data.extend(data)
            data = self.data
        else:
            self.expecting_second_part = True
            assert len(data) == 3
            self.i = i
            data.append(self.run)
            self.data = data
            return


        self.sanitize(data) # modify data (perform cleanup, transformations, etc.)
        data = tuple(data) # freeze data (tuples are immutable)

        self.verify(data) # verify that data fulfills certain criteria
        return data

    _timezone = pytz.timezone('Europe/Berlin')

    def sanitize(self, data):
        for i in (0, 4):
            data[i] = self._timezone.localize(data[i])


    def _verify_time(self, time):
        if self.lastdt is not None:
            if time < self.lastdt:
                raise AssertionError('time <= last time: %s <= %s' % (time.isoformat(), self.lastdt.isoformat()))
        if not time.tzinfo:
                raise AssertionError('time has no tzinfo: %s' % (time.isoformat(),))
        self.lastdt = time

    def verify(self, data):
        time, dom1, dom2, run, time2, a1, a2, a3, a4, b1, b2, b3, b4 = data
        self._verify_time(time)
        self._verify_time(time2)
        verifyrange('dom1', dom1, 0)
        verifyrange('dom2', dom2, 0)
        verifyrange('run', run, 1)
        verifyrange('a1', a1, 0)
        verifyrange('a2', a2, 0)
        verifyrange('a3', a3, 0)
        verifyrange('a4', a4, 0)
        verifyrange('b1', b1, 0)
        verifyrange('b2', b2, 0)
        verifyrange('b3', b3, 0)
        verifyrange('b4', b4, 0)

    def _col_descriptor(self):
        return OrderedDict([(k, t.FloatCol(dflt = nan, pos = i)) for i, k in enumerate(self.col_names)])

def stations():
    p = re.compile("(\\d{5})\\s+(\\d{5})\\s+(.+)\\s+(\\d+)\\s+(\\d+)°\\s+(\\d+)'?\\s+(\\d+)°\\s+(\\d+)'?.*")

    f = open(os.path.join(os.path.dirname(__file__), 'stationsliste.txt'))

    stats = {}
    for line in f:
        line = line.strip()
        if line.startswith('#'):
            continue
        m = p.match(line)
        g = m.groups()
        #       height       lat                             lon                      klimakennung name
        data = [float(g[3]), float(g[4]) + float(g[5]) / 60, float(g[6]) + float(g[7]) / 60, g[1], g[2]]
        #     station ID
        stats[int(g[0])] = data
    f.close()

    return stats

class DWDTageswerteHandler(LineHandler):
    description = 'Klimadaten Tageswerte of the DWD (http://www.dwd.de) [example: 10004 20111028  1          12.0   12.9   13.9   85.7    4.0   12.1    3.0               1020.6]'
    table_name = 'dwd_daily_weather'
    table_title = 'DWD Tageswerte'
    cols_and_units = OrderedDict([('time', ''), ('stat', ''), ('qn', ''), ('tg', ''), ('tn', ''), ('tm', ''), ('tx', ''),
                                  ('rfm', ''), ('fm', ''), ('fx', ''), ('so', ''), ('nm', ''), ('rr', ''), ('pm', ''), ('h', ''), ('lat', ''), ('lon', '')])
#   (pos,len) time    stat    qn       tg       tn       tm       tx       rfm      fm       fx       so       nm       rr       pm
    fields = [(7, 8), (1, 5), (16, 2), (19, 6), (26, 6), (33, 6), (40, 6), (47, 6), (54, 6), (61, 6), (68, 6), (75, 6), (82, 6), (89, 6)]

    def __init__(self):
        self.stations = stations()

    def __call__(self, line):
        'parse line and return tuple with data or None if line was skipped (comment/empty)'
        line = line.strip()
        # skip comments or empty lines
        if line.startswith('<') or line.startswith('Tageswerte') or line.startswith('-----') or line == '':
            return
        if line.startswith('STAT'):
            assert line == 'STAT JJJJMMDD QN     TG     TN     TM     TX    RFM     FM     FX     SO     NM     RR     PM'
            return

        data = []
        for i, f in enumerate(self.fields):
            a = f[0] - 1
            b = a + f[1]
            field = line[a:b]
            if i == 0:
                data.append(dp.parse(field))
            elif 1 <= i <= 2:
                data.append(int(field))
            elif field.strip() == '':
                data.append(nan)
            else:
                data.append(float(field))

        stat = data[1]
        pos = self.stations[stat][0:3] if stat in self.stations else 3 * [nan]
        data.extend(pos) # append height, lat, lon


        self.sanitize(data) # modify data (perform cleanup, transformations, etc.)
        data = tuple(data) # freeze data (tuples are immutable)

        self.verify(data) # verify that data fulfills certain criteria
        return data

    _timezone = pytz.timezone('Europe/Berlin')

    def sanitize(self, data):
        data[0] = self._timezone.localize(data[0])
        data[0] += dt.timedelta(hours = 12)


    def _verify_time(self, time):
        if self.lastdt is not None:
            if time < self.lastdt:
                raise AssertionError('time <= last time: %s <= %s' % (time.isoformat(), self.lastdt.isoformat()))
        if not time.tzinfo:
                raise AssertionError('time has no tzinfo: %s' % (time.isoformat(),))
        self.lastdt = time

    def verify(self, data):
        pass

    def _col_descriptor(self):
        descriptor = OrderedDict([(k, t.FloatCol(dflt = nan, pos = i)) for i, k in enumerate(self.col_names)])
        descriptor['stat'] = t.IntCol(dflt = -1, pos = self.col_names.index('stat'))
        descriptor['qn'] = t.IntCol(dflt = -1, pos = self.col_names.index('qn'))
        return descriptor

class PolarsternHandler(LineHandler):
    description = 'Polarstern myon rate data [example: 2010 10 26  0 53 56.07 N 4  9.26 E 1025.7 10.1 39539 0 -1 63.5 12051 10000 1537]'
    table_name = 'polarstern_events'
    table_title = 'Polarstern myon rate data'
    cols_and_units = OrderedDict([('time', 's'), ('lat', '°'), ('lon', '°'),
                                  ('p', 'hPa'), ('T', '°C'), ('H', '%'), ('rate', '1/s')])

    def __call__(self, line):
        'parse line and return tuple with data or None if line was skipped (comment/empty)'
        line = line.strip()
        # skip comments or empty lines
        if line.startswith('#') or line == '':
            return

        fields = line.split()

        yy, mm, dd, hh = map(int, fields[:4])
        time = dt.datetime(yy, mm, dd, hh)

        deg, mins = map(float, fields[4:6])
        lat = (deg + mins / 60.) * (-1 if fields[6] == 'S' else 1)
        deg, mins = map(float, fields[7:9])
        lon = (deg + mins / 60.) * (-1 if fields[9] == 'W' else 1)

        ff = map(float, fields[10:])

        data = [time, lat, lon, ff[0], ff[1], ff[5], ff[8]]

        self.sanitize(data) # modify data (perform cleanup, transformations, etc.)
        data = tuple(data) # freeze data (tuples are immutable)

        self.verify(data) # verify that data fulfills certain criteria
        return data

    _timezone = pytz.timezone('Europe/Berlin')

    def sanitize(self, data):
        data[0] = self._timezone.localize(data[0])

    def verify(self, data):
        time, lat, lon, p, T, H, rate = data
        self._verify_time(time)
        verifyrange('lat', lat, -90, 90)
        verifyrange('lon', lon, -180, 180)
        verifyrange('T', T, -50 , 50)
        verifyrange('H', H, 0 , 100)
        verifyrange('p', p , 800, 1200)
        verifyrange('rate', rate, 0, 5000)

    def _col_descriptor(self):
        descriptor = OrderedDict([(k, t.FloatCol(dflt = nan, pos = i)) for i, k in enumerate(self.col_names)])
        return descriptor


available_handlers = (WeatherHandler, CTEventHandler, ITTEventHandler, DWDTageswerteHandler, PolarsternHandler)


def autodetect(filename, handlers = available_handlers):
    """
    try to parse file (filename) with the given handlers (types, not instances).
    if the first 10 lines of the file can be parsed by a handler
    without error and there is only one handler that successfully
    parses the file (unique match) return this handler (type, not instance), 
    else raise RuntimeError
    """
    matched_handlers = []
    # try each handler
    for h in handlers:
        try: # try to parse the file
            for i, data in enumerate(fileiter(filename, h())):
                if i > 10: break # stop after 10 lines

            # if parsing was successful (no exception), add this handler
            matched_handlers.append(h)

        except Exception as e: # ignore errors, try next handler
#            print h, e
            pass

    # return a unique match...
    if len(matched_handlers) == 1:
        return matched_handlers[0]
    else: # ...or raise
        raise RuntimeError('could not autodetect handler for ' + filename)


def starttime(filename, handler):
    """
    get the first time stamp in the file using the given LineHandler,
    assuming the handler produces a 'time' column
    """
    time_idx = handler.col_names.index('time')

    first_record = fileiter(filename, handler).next()
    return first_record[time_idx]


def detect_and_sort(filenames):
    """
    detect files types (handlers) and sort the files 'time' ascending,
    return dict(LineHandler --> tuple(time sorted filenames))
    """
    sorted_files = {}

    # map files to auto detected handlers
    for filename in filenames:
        handler = autodetect(filename)
        if handler in sorted_files:
            sorted_files[handler].append(filename)
        else:
            sorted_files[handler] = [filename]

    # time sort files and freeze file lists
    for h, files in sorted_files.iteritems():
        files.sort(key = lambda x: starttime(x, h()))
        sorted_files[h] = tuple(files)

    return sorted_files


def raw_to_h5(filenames, out = "out.h5", handlers = available_handlers,
              t0 = dp.parse('2004-01-01 00:00:00 +0000'), skip_on_assert = False, show_progress = True):
    """
    converts ASCII data to HDF5 tables
        filenames : iterable, filenames of all data files (events, weather, etc.) in any order
              out : string, filename of outputfile (default='out.h5')
         handlers : iterable of LineHandlers for parsing the data files (default=available_handlers)
               t0 : datetime, reference time for 'time' column,
                    time is stored as 'time since t0' (default='2004-01-01 00:00:00 +0100')
    skip_on_assert: if True, skip lines that are invalid (if LineHandler.verify() raises AssertionError)
                    (default=False, exception is raised)
    """

    _filenames = []
    for f in filenames:
        if path.exists(f):
            if path.isdir(f):
                for dn, dns, fns in os.walk(f):
                    for fn in fns:
                        _filenames.append(path.join(dn, fn))
            else:
                _filenames.append(f)
    filenames = _filenames

    if show_progress:
        pb = ProgressBar(maxval = len(filenames), widgets = [Bar(), ' ', Percentage(), ' ', ETA()], fd = sys.stdout)
        print "reference time t0 =", t0
        print 'autodetecting file types...'

    def read_files(files, row, handler):
        for f in files:
            for entry in fileiter(f, handler, skip_on_assert, show_progress):
                try:
                    for k, v in zip(handler.col_names, entry):
                        if isinstance(v, dt.datetime):
                            row[k] = (v - t0).total_seconds()
                        else:
                            row[k] = v

                    row.append()

                except StopIteration:
                    pass

            if show_progress:
                pb.update(pb.currval + 1)

    # autodetect handlers and time sort files
    files_dict = detect_and_sort(filenames)

    if show_progress:
        print 'detected file types:', ['{} ({})'.format(k.table_name, len(v)) for k, v in files_dict.iteritems()]
        print "processing data... (%d files)" % (len(filenames),)
        pb.start()

    # create HDF5 file
    filters = t.Filters(complevel = 1, complib = 'zlib')
    with t.openFile(out, 'w', 'datafile created with raw_to_h5', filters = filters) as h5:
        h5.root._v_attrs.creationdate = dt.datetime.now(pytz.utc).isoformat()
        raw = h5.createGroup(h5.root, 'raw', 'raw data')

        # create and fill raw data tables
        for handler, files in files_dict.iteritems():
            handler = handler() # instanciate the LineHandler
            title = handler.table_title
            if show_progress:
                print 'creating table: %s (%s)' % (handler.table_name, title)
            table = h5.createTable(raw, handler.table_name, handler.col_descriptor,
                                   title, expectedrows = 10000 * len(files))
            set_attrs(table, t0, handler.col_units)
            read_files(files, table.row, handler)
            table.flush()

    if show_progress:
        pb.finish()

if __name__ == '__main__':
    import argparse as ap
    formats = ''
    for i, h in enumerate(available_handlers):
        if i > 0:
            formats += ', '
        formats += h.description

    parser = ap.ArgumentParser(description = 'convert raw ASCII data tables into tables in one HDF5 file',
                               epilog = 'raw data can be in the following formats: ' + formats +
                               '. The program tries to autodetect the file format and sorts the input files by time automatically. ' +
                               'Times are stored as double as seconds since reference time t0.')

    parser.add_argument('--version', action = 'version', version = '%(prog)s {} from {}'.format(__version__, __date__))
    parser.add_argument('-o', '--out', metavar = 'file', default = 'out.h5', help = 'HDF5 output file (default: out.h5)')
    parser.add_argument('-f', '--force', action = 'store_true', help = 'overwrite existing file')
#    parser.add_argument('-a', '--append', action = 'store_true', help = 'append new data to existing file')
    parser.add_argument('-t', '--reftime', metavar = 'datetime', default = '2004-01-01T00:00:00+0000', type = dp.parse, help = 'reference time t0 (default: 2004-01-01T00:00:00+0000)')
    parser.add_argument('-s', '--noskip', action = 'store_true', help = 'do not skip invalid lines, stop on error')
    parser.add_argument('-q', '--quiet', action = 'store_true', help = 'do not show progressbar, just print error messages')
    parser.add_argument('infiles', nargs = '+', help = 'input files, if a directory is given, all files in it and in its subdirectories are used')

    opts = parser.parse_args()


    if not opts.out.endswith('.h5'):
        out = opts.out + '.h5'
    else:
        out = opts.out;

    if not opts.force and path.exists(out):
        raise RuntimeError('file \'{}\' already exists'.format(out))


    raw_to_h5(opts.infiles, out = out, skip_on_assert = not opts.noskip, show_progress = not opts.quiet, t0 = opts.reftime)
