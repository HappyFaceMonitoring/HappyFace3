
import pytz, math, os, types, numpy, warnings
from matplotlib.dates import AutoDateLocator, AutoDateFormatter, DateFormatter, RRuleLocator, rrulewrapper, HOURLY, MINUTELY, SECONDLY, YEARLY, MONTHLY, DAILY
from matplotlib.ticker import ScalarFormatter
from dateutil.relativedelta import relativedelta

def comma_format(x_orig):
    x = float(x_orig)
    if x >= 1000:
        after_comma = x % 1000
        before_comma = int(x) / 1000 
        return '%s,%03g' % (comma_format(before_comma), after_comma)
    else:
        return str(x_orig)

class PrettyScalarFormatter( ScalarFormatter ):

    def _set_orderOfMagnitude(self,range):
        # if scientific notation is to be used, find the appropriate exponent
        # if using an numerical offset, find the exponent after applying the offset
        locs = numpy.absolute(self.locs)
        if self.offset: oom = math.floor(math.log10(range))
        else:
            if locs[0] > locs[-1]: val = locs[0]
            else: val = locs[-1]
            if val == 0: oom = 0
            else: oom = math.floor(math.log10(val))
        if oom <= -7:
            self.orderOfMagnitude = oom
        elif oom >= 9:
            self.orderOfMagnitude = oom
        else:
            self.orderOfMagnitude = 0
            
    def pprint_val(self, x):
        pstring = ScalarFormatter.pprint_val(self, x)
        return comma_format(pstring)

class PrettyDateFormatter( AutoDateFormatter ):
    """ This class provides a formatter which conforms to the
        desired date formates for the Phedex system.
    """
  
    def __init__( self, locator ):
      tz = pytz.timezone('UTC')
      AutoDateFormatter.__init__( self, locator, tz=tz )
    
    def __call__(self, x, pos=0):
        scale = float( self._locator._get_unit() )
        if ( scale == 365.0 ):
            self._formatter = DateFormatter("%Y", self._tz)
        elif ( scale == 30.0 ):
            self._formatter = DateFormatter("%b %Y", self._tz)
        elif ( (scale >= 1.0) and (scale <= 7.0) ):
            self._formatter = DateFormatter("%Y-%m-%d", self._tz)
        elif ( scale == (1.0/24.0) ):
            self._formatter = DateFormatter("%H:%M", self._tz)
        elif ( scale == (1.0/(24*60)) ):
            self._formatter = DateFormatter("%H:%M", self._tz)
        elif ( scale == (1.0/(24*3600)) ):
            self._formatter = DateFormatter("%H:%M:%S", self._tz)
        else:
            self._formatter = DateFormatter("%b %d %Y %H:%M:%S", self._tz)
        
        return self._formatter(x, pos)

class PrettyDateLocator( AutoDateLocator ):

    def get_locator(self, dmin, dmax):
        'pick the best locator based on a distance'
        
        delta = relativedelta(dmax, dmin)
        
        numYears = (delta.years * 1.0)
        numMonths = (numYears * 12.0) + delta.months
        numDays = (numMonths * 31.0) + delta.days
        numHours = (numDays * 24.0) + delta.hours
        numMinutes = (numHours * 60.0) + delta.minutes
        numSeconds = (numMinutes * 60.0) + delta.seconds
        
        numticks = 5
        
        # self._freq = YEARLY
        interval = 1
        bymonth = 1
        bymonthday = 1
        byhour = 0 
        byminute = 0
        bysecond = 0

        if ( numYears >= numticks ):
            self._freq = YEARLY
        elif ( numMonths >= numticks ):
            self._freq = MONTHLY
            bymonth = range(1, 13)
            if ( (0 <= numMonths) and (numMonths <= 14) ):
                interval = 1      # show every month
            elif ( (15 <= numMonths) and (numMonths <= 29) ):
                interval = 3      # show every 3 months
            elif ( (30 <= numMonths) and (numMonths <= 44) ):
                interval = 4      # show every 4 months
            else:   # 45 <= numMonths <= 59
                interval = 6      # show every 6 months
        elif ( numDays >= numticks ):
            self._freq = DAILY
            bymonth = None
            bymonthday = range(1, 32)
            if ( (0 <= numDays) and (numDays <= 9) ):
                interval = 1      # show every day 
            elif ( (10 <= numDays) and (numDays <= 19) ):
                interval = 2      # show every 2 days
            elif ( (20 <= numDays) and (numDays <= 35) ):
                interval = 3      # show every 3 days
            elif ( (36 <= numDays) and (numDays <= 80) ):
                interval = 7      # show every 1 week
            else:   # 100 <= numDays <= ~150
                interval = 14     # show every 2 weeks
        elif ( numHours >= numticks ):
            self._freq = HOURLY
            bymonth = None
            bymonthday = None 
            byhour = range(0, 24)      # show every hour
            if ( (0 <= numHours) and (numHours <= 14) ):
                interval = 1      # show every hour
            elif ( (15 <= numHours) and (numHours <= 30) ):
                interval = 2      # show every 2 hours
            elif ( (30 <= numHours) and (numHours <= 45) ):
                interval = 3      # show every 3 hours
            elif ( (45 <= numHours) and (numHours <= 68) ):
                interval = 4      # show every 4 hours
            elif ( (68 <= numHours) and (numHours <= 90) ):
                interval = 6      # show every 6 hours
            else:   # 90 <= numHours <= 120
                interval = 12     # show every 12 hours
        elif ( numMinutes >= numticks ):
            self._freq = MINUTELY
            bymonth = None
            bymonthday = None
            byhour = None
            byminute = range(0, 60) 
            if ( numMinutes > (10.0 * numticks) ):
                interval = 10
            # end if
        elif ( numSeconds >= numticks ):
            self._freq = SECONDLY
            bymonth = None
            bymonthday = None
            byhour = None
            byminute = None
            bysecond = range(0, 60) 
            if ( numSeconds > (10.0 * numticks) ):
                interval = 10
            # end if
        else:
            # do what?
            #   microseconds as floats, but floats from what reference point?
            pass

        rrule = rrulewrapper( self._freq, interval=interval,          \
                              dtstart=dmin, until=dmax,               \
                              bymonth=bymonth, bymonthday=bymonthday, \
                              byhour=byhour, byminute = byminute,     \
                              bysecond=bysecond )
        
        locator = RRuleLocator(rrule, self.tz)
        
        locator.set_view_interval(self.viewInterval)
        locator.set_data_interval(self.dataInterval)
        return locator

def pretty_float( num ):

    if num > 1000:
        return comma_format(int(num))

    try:
        floats = int(max(2-max(floor(log(abs(num)+1e-3)/log(10)),0),0))
    except:
        floats=2
    format = "%." + str(floats) + "f"
    if type(num) == types.TupleType:
        return format % float(num[0])
    else:
        try:
            retval = format % float(num)
        except:
            raise Exception("Unable to convert %s into a float." % (str(num)))
        return retval

def statistics( results, span=None, is_timestamp = False ):
    results = dict(results)
    if span != None:
        parsed_data = {}
        min_key = min(results.keys())
        max_key = max(results.keys())
        for i in range(min_key, max_key+span, span):
            if i in results:
                parsed_data[i] = results[i]
                del results[i]
            else:
                parsed_data[i] = 0.0
        if len(results) > 0:
            raise Exception("Unable to use all the values for the statistics")
    else:
        parsed_data = results
    values = parsed_data.values()
    data_min = min(values)
    data_max = max(values)
    data_avg = numpy.average( values )
    if is_timestamp:
        current_time = max(parsed_data.keys())
        data_current = parsed_data[ current_time ]
        return data_min, data_max, data_avg, data_current
    else:
        return data_min, data_max, data_avg
    
