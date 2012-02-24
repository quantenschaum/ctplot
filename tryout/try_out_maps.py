
import numpy as np
import matplotlib.pyplot as plt
import dateutil.parser as dp
import utils
import datetime as dt
import pytz
import ticks

def drawmap(lat = None, lon = None, margin = 0.05, width = 1e6, height = None, boundarylat = 40,
         projection = 'cyl', drawcoastline = 1, drawgrid = 1, drawspecgrid = 1, bluemarble = 0, nightshade = None,
         places = [('Neumayer-St.'    , -70.6666      , -8.2666),
                   ('Amundsen-Scott-St.'   , -90.     , 0.),
                   ('DESY Zeuthen'  , 52.346142    , 13.633432)]):

    minlat, maxlat = np.nanmin(lat), np.nanmax(lat)
    lat0 = (minlat + maxlat) / 2
    minlat, maxlat = minlat - margin * (maxlat - minlat), maxlat + margin * (maxlat - minlat)
    minlat, maxlat = max(-90, minlat), min(90, maxlat)

    minlon, maxlon = np.nanmin(lon), np.nanmax(lon)
    lon0 = (minlon + maxlon) / 2
    minlon, maxlon = minlon - margin * (maxlon - minlon), maxlon + margin * (maxlon - minlon)
    #minlon, maxlon = max(-90,minlon), min(90,maxlon)

    if projection in ('ortho', 'robin'):
        map_options = { 'lat_0' : lat0, 'lon_0' : lon0, 'resolution':'l'}
        latlabels = [1, 0, 0, 0] # left, right, top, bottom
        lonlabels = [0, 0, 0, 1]
    elif projection in ('npaeqd', 'nplaea', 'npstere', 'spaeqd', 'splaea', 'spstere'): # polar
        if projection.startswith('s'):
            boundarylat = -abs(boundarylat)
        else:
            boundarylat = abs(boundarylat)
        map_options = { 'lat_0' : lat0, 'lon_0' : lon0, 'boundinglat' :boundarylat, 'resolution':'l'}
        latlabels = [0, 0, 1, 1]
        lonlabels = [1, 1, 0, 0]
    elif projection in ('cyl', 'merc'):
        map_options = { 'llcrnrlon' : minlon, 'llcrnrlat' : minlat, 'urcrnrlon' : maxlon, 'urcrnrlat' : maxlat, 'resolution':'l'}
        latlabels = [1, 0, 0, 0]
        lonlabels = [0, 0, 0, 1]
    elif projection in ('aeqd', 'laea', 'stere'):
        if height is None:
            height = width / np.sqrt(2)
        map_options = { 'lat_0' : lat0, 'lon_0' : lon0, 'width':width, 'height':height , 'resolution':'i'}
        latlabels = [1, 0, 0, 0]
        lonlabels = [0, 0, 0, 1]
    else:
        raise ValueError('unknow projection: ' + projection)

    #print map_options

    import mpl_toolkits.basemap as bm
    m = bm.Basemap(projection = projection, **map_options)

    if bluemarble:
        m.bluemarble(scale = 0.5)
        #m.warpimage(image = 'c:/Program Files (x86)/Python27/Lib/site-packages/mpl_toolkits/basemap/data/etopo1.jpg', scale = 0.5)
        #m.warpimage(image = 'c:/Users/al/Downloads/bluemarble/Earthlights_2002-5400x2700.jpg', scale = 0.5)
    elif drawcoastline:
        m.drawcoastlines(color = 'k')
        #m.drawcountries(color = 'k')
        #m.drawrivers(color = 'b')
        m.fillcontinents(color = '#f7d081')
        #m.drawlsmask(land_color = '#f7d081', lakes = True)

    if nightshade is not None:
        if isinstance(nightshade, basestring):
            datetime = dp.parse(nightshade)
        m.nightshade(datetime, color = 'k', delta = 0.25, alpha = 0.7)

    if drawgrid:
        if projection in ('ortho', 'robin', 'npaeqd', 'nplaea', 'npstere', 'spaeqd', 'splaea', 'spstere'):
            parallels, meridians = np.arange(-90, 90, 10), np.arange(-180, 180, 20)
        else:
            parallels, meridians = ticks.get_ticks(m.llcrnrlat, m.urcrnrlat, 6), ticks.get_ticks(m.llcrnrlon, m.urcrnrlon, 6)

        pmc = '0.6' if bluemarble else 'k'
        m.drawparallels(parallels, labels = latlabels, linewidth = 0.5, color = pmc)
        m.drawmeridians(meridians, labels = lonlabels, linewidth = 0.5, color = pmc)

    if drawspecgrid:
        ecl = 23.44 # ecliptic
        m.drawparallels([-90 + ecl, -ecl, ecl, 90 - ecl], dashes = [2, 2], linewidth = 0.5, color = pmc)
        m.drawparallels([0], dashes = [1, 0], linewidth = 0.5, color = pmc)
        m.drawmeridians([0], dashes = [1, 0], linewidth = 0.5, color = pmc)


    m.drawmapboundary(linewidth = 1.5, fill_color = 'white')

    for name, la, lo in places:
        x, y = m(lo, la)
        m.plot(x, y, 'rs', markersize = 4)
        plt.annotate(name, (x, y), textcoords = 'offset points', xytext = (5, 2))

    return m


plt.rc('font', **{'family':'sans-serif', 'sans-serif':['Dejavu Sans'], 'size':10})
plt.rc('axes', grid = True)
plt.rc('lines', markeredgewidth = 0)
ticks.set_extended_locator(1)
plotwidth = 12
plt.gcf().set_size_inches((plotwidth, plotwidth / np.sqrt(2)));
f = 0.09
plt.gca().set_position([f, f, 1 - 2 * f, 1 - 2 * f])


s = utils.get_scanner()
f = open('../polarstern.txt')
t0 = dp.parse('2004-01-01 00:00 +0100')
times = []
lats = []
lons = []
z = []
for line in f:
    data = s.scan(line)
    #print data[0]
    y, m, d, h, latd, latm, ns, lond, lonm, ew, p, T = data[0][:12]
    time = (dt.datetime(y, m, d, h, tzinfo = pytz.utc) - t0).total_seconds()
    lat = (latd + latm / 60.) * (1 if ns == 'N' else -1)
    lon = (lond + lonm / 60.) * (1 if ew == 'E' else -1)
    z.append(p)

    times.append(time)
    lats.append(lat)
    lons.append(lon)
f.close()

times = np.array(times)
lats = np.array(lats)
lons = np.array(lons)
z = np.array(z)



projections = {
               'ortho': 'Orthographic',
               'robin': 'Robinson',

               'npaeqd': 'North-Polar Azimuthal Equidistant',
               'nplaea': 'North-Polar Lambert Azimuthal',
               'npstere': 'North-Polar Stereographic',

               'spaeqd': 'South-Polar Azimuthal Equidistant',
               'splaea': 'South-Polar Lambert Azimuthal',
               'spstere': 'South-Polar Stereographic',

               'merc': 'Mercator',
               'cyl': 'Cylindrical Equidistant',

               'aeqd': 'Azimuthal Equidistant',
               'laea': 'Lambert Azimuthal Equal Area',
               'stere': 'Stereographic'
               }

#la, lo = np.meshgrid(np.linspace(-90 , 90 , 100), np.linspace(-180 , 180 , 100))
#z = np.sin(3 * np.deg2rad(la)) * np.cos(3 * np.deg2rad(lo))

m = drawmap(lat = lats, lon = lons, projection = 'cyl', width = 8e6, height = 12e6, margin = 0.05, bluemarble = 0)
x, y = m(lons, lats)
plt.plot(x, y, 'r')
#plt.scatter(x, y, c = z, marker = 'o', edgecolor = 'none', s = 6 ** 2)
#plt.colorbar(fraction = 0.04, pad = 0.05, aspect = 40)

#x, y = m(lo, la)
#plt.contourf(x, y, z, 20)

#plt.title(projections[proj])
#plt.tight_layout()


plt.show()
