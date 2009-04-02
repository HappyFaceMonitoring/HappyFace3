
import types, datetime, numpy, math
from graphtool.tools.common import to_timestamp, expand_string, \
    convert_to_datetime
from graphtool.database.query_handler import histogram_parser
from graphtool.graphs.graph import Graph, PivotGraph, PivotGroupGraph, \
    TimeGraph, HorizontalGraph, draw_empty, find_info
from graphtool.graphs.common import pretty_float, statistics
import matplotlib.cm as cm
from matplotlib.mlab import linspace
from matplotlib.dates import date2num
from matplotlib.patches import Polygon, Wedge, Shadow, Rectangle, Circle
from matplotlib.ticker import FixedLocator, FixedFormatter
from matplotlib.cbook import is_string_like
from matplotlib.colors import normalize
from pylab import setp, figure, bar, legend, box, axis

try:
    set
except:
    import sets
    set = sets.Set

class BarGraph( PivotGraph ):

    """
    The BarGraph class is a straightforward bar graph; given a dictionary
    of values, it takes the keys as the independent variable and the values
    as the dependent variable.
    """

    bar_graph_space = .2
    is_timestamps = False

    def setup(self):
        """
        Setup the BarGraph class.  Most of the work is done in the super class.
        Also, try and figure out the `width` of the bars.  If there is a value
        of span, use that.  Otherwise, the `width` is 1.
        """
        self.width = self.metadata.get('span',1.0)
        super( BarGraph, self ).setup()
        self.legend = False
     
    def make_bottom_text(self ):
        """
        Attempt to calculate the maximum, minimum, average, and current values
        for the graph.  These statistics will be printed on the bottom of the 
        graph.
        """
        units = str(self.metadata.get('column_units','')).strip()
        results = dict(self.parsed_data)
        try:
            vars = getattr( self, 'vars', {} )
            span = find_info('span',vars,self.metadata,None)
            if getattr(self, 'is_timestamps',False) and span != None:
                starttime = self.begin
                starttime = starttime - (starttime % span)
                results[starttime] = 0
            if self.is_timestamps:
                data_min, data_max, data_average, data_current = statistics(results, span, True)
            else:
                data_min, data_max, data_average = statistics(results, span)
        except Exception, e:
            values = results.values()
            try:
                data_max = max(values)
            except:
                data_max = None
            try:
                data_min = min(values)
            except:
                data_min = None
            try:
                data_average = numpy.average( values )
            except:
                data_average = None
            try:
                last_time = max(results.keys())
                data_current = results[last_time]
            except:
                data_current = None
        retval = ''
        if data_max != None:
            try:
                retval += "Maximum: " + pretty_float( data_max ) + " " + units
            except Exception, e:
                pass
        if data_min != None:
            try:
                retval += ", Minimum: " + pretty_float( data_min ) + " " + units
            except Exception, e:
                pass
        if data_average != None:
            try:
                retval += ", Average: " + pretty_float( data_average ) + " " + units
            except Exception, e:
                pass
        if (self.is_timestamps) and (data_current != None):
            try:
                retval += ", Current: " + pretty_float( data_current ) + " " + units
            except Exception, e:
                pass
        return retval

    def draw( self ):
      results = self.parsed_data
      if len( results.items() ) == 0:
          return None
      keys = self.sort_keys( results )
      tmp_x = []; tmp_y = []
  
      width = float(self.width)
      if self.is_timestamps:
          #width = (1 - self.bar_graph_space) * width / 86400.0
          width = width / 86400.0
          offset = 0
      elif self.string_mode:
          width = (1 - self.bar_graph_space) * width
          offset = self.bar_graph_space / 2.0
      else:
          offset = 0
      for pivot, data in results.items():
          if self.string_mode:
              transformed = self.transform_strings( pivot )
              tmp_x.append( transformed + offset )
          else:
            tmp_x.append( pivot + offset )
          tmp_y.append( float(data) )
      if self.is_timestamps:
          tmp_x = [date2num( datetime.datetime.utcfromtimestamp(key) ) for key in tmp_x]
      if self.log_yaxis:
          self.bars = self.ax.bar( tmp_x, tmp_y, bottom=.001, width=width )
      else:
          self.bars = self.ax.bar( tmp_x, tmp_y, width=width )
      setp( self.bars, linewidth=0.5 )
      pivots = keys
      for idx in range(len(pivots)):
          self.coords[ pivots[idx] ] = self.bars[idx]
      if self.string_mode:
          ymax = max(tmp_y); ymax *= 1.1
          if self.log_xaxis:  
              xmin = 0.001
          else: 
              xmin = 0
          if self.log_yaxis:
              ymin = 0.001
          else:
              ymin = 0
          self.ax.set_xlim( xmin=xmin, xmax=len(self.string_map.keys()) )
          self.ax.set_ylim( ymin=ymin, ymax=ymax )
      elif self.is_timestamps:
          self.ax.set_xlim( xmin=min(tmp_x), xmax=max(tmp_x)+width )
        
    def transform_strings(self, pivot ):
        smap = self.string_map
        try:
            return smap[pivot]
        except Exception, e:
            raise Exception( "While transforming strings to coordinates, encountered an unknown string: %s" % group)

    def get_coords( self ):
        height = self.prefs['height']
        coords = self.coords
        keys = self.sort_keys( self.parsed_data )
        for pivot in keys:
            bar = coords[pivot]
            t = bar.get_transform()
            my_coords = t.seq_xy_tups( bar.get_verts() )
            coords[ pivot ] = tuple( [(i[0],height-max(i[1],0)) for i in my_coords] )
        return coords
    
    def parse_data(self):
        # Start off by looking for strings in the groups.
        self.string_mode = False
        for pivot in getattr(self,'parsed_data',self.results).keys():
            if type(pivot) == types.StringType:
                self.string_mode = True; break
            if self.string_mode == True: break
        
        self.string_map = {}
        self.next_value = 0
        # Then parse as normal
        super( BarGraph, self ).parse_data()
        if self.string_mode:
            keys = self.sort_keys(self.parsed_data); keys.reverse()
            for key in keys:
                self.string_map[key] = self.next_value
                self.next_value += 1

    def x_formatter_cb( self, ax ):
        if self.string_mode:
            smap = self.string_map
            reverse_smap = {}
            for key, val in smap.items():
                reverse_smap[val] = key
            ticks = smap.values(); ticks.sort()
            ax.set_xticks( [i+.5 for i in ticks] )
            ax.set_xticklabels( [reverse_smap[i] for i in ticks] )
            labels = ax.get_xticklabels()
            ax.grid( False )
            if self.log_xaxis:
                xmin = 0.001
            else:
                xmin = 0
            ax.set_xlim( xmin=xmin,xmax=len(ticks) )
        else:
            try:
                super(BarGraph, self).x_formatter_cb( ax )
            except:
                return None

class Histogram(BarGraph):
    """
    The Histogram is a straightforward bar graph which performs histogramming
    of the data given to the class.
    """
    
    default_nbins = 10
    default_span = 1.0
    string_mode = False
    
    def setup(self):
        self.width = self.metadata.get('span', self.default_span)
        super(Histogram, self).setup()
        self.legend = False
        
    def parse_data(self):
        """
        Take the input list or array of data, and run the histogram parser on 
        it.
        """
        results = self.results
        nbins = self.metadata.get('nbins', self.default_nbins)
        
        parsed_data, metadata = histogram_parser(results, nbins=nbins,
                                             results=None)
        self.metadata['span'] = metadata.get('span', self.default_span)
        
        new_parsed_data = {}
        for pivot, data in parsed_data.items():
            new_pivot = self.parse_pivot(pivot)
            data = self.parse_datum(data)
            if data != None:
                new_parsed_data[new_pivot] = data
        self.parsed_data = new_parsed_data        
                
class HorizontalBarGraph( HorizontalGraph, BarGraph ):

    """
    The HorizontalBarGraph is just like the BarGraph class, except the bars are
    placed horizontally; the independent variable is along the y-axis.
    """

    def draw( self ):
        results = getattr(self,'parsed_data',self.results)
        if len( results.items() ) == 0:
            return None
        keys = self.sort_keys(results)
        tmp_x = []; tmp_y = []; yerr = []

        width = float(self.width)
        if self.string_mode:
            width = (1 - self.bar_graph_space) * width
            offset = self.bar_graph_space / 2.0
        else:
            offset = 0
        keys = self.sort_keys(results)
        for pivot in keys:
            data = results[pivot]
            if self.string_mode:
                transformed = self.transform_strings( pivot )
                tmp_x.append( transformed + offset )
            else:
                tmp_x.append( pivot + offset )
            if type(data) == types.TupleType:
                tmp_y.append( float(data[0]) )
                yerr.append( float(data[1]) )
            else:
                tmp_y.append( float(data) )
        if len(yerr) != 0:
            self.bars = self.ax.barh( tmp_x, tmp_y, height=width, xerr=yerr, ecolor='red' )
        else:
            self.bars = self.ax.barh( tmp_x, tmp_y, height=width )
        setp( self.bars, linewidth=0.5 )
        pivots = keys
        for idx in range(len(pivots)):
            self.coords[ pivots[idx] ] = self.bars[idx]
        if self.string_mode:
            ymax = max(tmp_y); ymax *= 1.1
            if self.log_yaxis: 
                ymin = 0.001
            else:
                ymin = 0
            if self.log_xaxis:
                xmin = 0.001
            else:
                xmin = 0
            self.ax.set_ylim( ymin=ymin, ymax=len(self.string_map.keys()) )
            self.ax.set_xlim( xmin=xmin, xmax=ymax )
    
    def x_formatter_cb( self, ax ):
        """
        The x_formatter_cb - calls the PivotGraph directly, skipping the 
        HorizontalGraph.
        """
        try:
            super( PivotGraph, self ).x_formatter_cb( ax )
        except:
            pass
    
    def y_formatter_cb( self, ax ):
        if self.string_mode:
            smap = self.string_map
            reverse_smap = {}
            for key, val in smap.items():
                reverse_smap[val] = key
            ticks = smap.values(); ticks.sort()
            ax.set_yticks( [i+.5 for i in ticks] )
            ax.set_yticklabels( [reverse_smap[i] for i in ticks] )
            labels = ax.get_yticklabels()
            ax.grid( False )
            if self.log_yaxis:
                ymin = 0.001
            else:
                ymin = 0
            ax.set_ylim( ymin=ymin,ymax=len(ticks) )
        else:
            try:
                super( PivotGraph, self).y_formatter_cb( ax )
            except:
                return None

class HorizontalGroupedBarGraph(HorizontalBarGraph):
    
    """
    A horizontal bar graph which groups bars together.
    """
    
    def setup(self):
        max_len = 1
        for pivot, val in self.parsed_data.items():
            if hasattr(val, '__len__'):
                max_len = max(max_len, len(val))
        self.metadata['pixels_per_label_multiplier'] = max_len
        super(HorizontalGroupedBarGraph, self).setup()
    
    def draw( self ):
        results = self.parsed_data
        if len( results.items() ) == 0:
            return None
        keys = self.sort_keys( results )
        tmp_x = []; tmp_y = []; yerr = []

        width = float(self.width)
        bar_graph_space = getattr(self, 'bar_graph_space', .1)
        width = (1 - bar_graph_space) * width
        offset = bar_graph_space / 2.0
        keys = self.sort_keys( results )
        data_len_dict = {}
        colors = tuple(self.colors)
        my_colors = []
        for pivot in keys:
            data = results[pivot]
            try:
                data_len = len(data)
                data_len_dict[pivot] = data_len
                bar_width = width / float(data_len)
                while len(colors) < data_len:
                    colors += colors
                my_colors.extend(colors[:data_len])
            except Exception, e:
                #print e
                raise ValueError("Must pass the HorizontalGroupedBarGraph a " \
                                 "dictionary of sequences.  See example.")
            if self.string_mode:
                transformed = self.transform_strings( pivot )
                tmp_x.append( transformed + offset )
            else:
                tmp_x.append( pivot + offset )
            base = tmp_x[-1]
            tmp_x.extend([base+bar_width*(i+1) for i in range(data_len-1)])
            for datum in data:
                if type(datum) == types.TupleType:
                    tmp_y.append( float(datum[0]) )
                    yerr.append( float(datum[1]) )
                else:
                    tmp_y.append( float(datum) )
        if len(yerr) != 0:
            self.bars = self.ax.barh( tmp_x, tmp_y, height=bar_width, \
                                      xerr=yerr, ecolor='red', \
                                      color=my_colors )
        else:
            self.bars = self.ax.barh( tmp_x, tmp_y, height=bar_width, \
                                      color=my_colors)
        setp( self.bars, linewidth=0.5 )
        pivots = keys
        ctr = 0
        for idx in range(len(pivots)):
            self.coords[ pivots[idx] ] = self.bars[ctr]
            ctr += data_len_dict[pivots[idx]]
        if self.string_mode:
            ymax = max(tmp_y); ymax *= 1.1
            if self.log_yaxis: 
                ymin = 0.001
            else:
                ymin = 0 
            if self.log_xaxis:
                xmin = 0.001
            else: 
                xmin = 0
            self.ax.set_ylim( ymin=ymin, ymax=len(self.string_map.keys()) )
            self.ax.set_xlim( xmin=xmin, xmax=ymax )

class QualityBarGraph( HorizontalBarGraph ):
    
    """
    A special case of the HorizontalBarGraph.  The QualityBarGraph
    displays bars between 0% and 100%, has a special formatting on the x-axis
    (appends the % symbol) and colors the individual bars depending on their
    length; 0% is red, 50% is yellow, and 100% is green.
    """
    
    def setup(self):
        super(QualityBarGraph,self).setup()
        results = getattr(self,'parsed_data',self.results)
        self.color_override = self.metadata.get('color_override', {})
        # Setup the colormapper to get the right colors
        norms = normalize(0,100)
        mapper = cm.ScalarMappable( cmap=cm.RdYlGn, norm=norms )
        # Hack to make mapper work:
        def get_alpha(*args, **kw):
            return 1.0
        mapper.get_alpha = get_alpha
        A = linspace(0,100,100)
        mapper.set_array(A)
        self.mapper = mapper

        # Kill the xlabel / ylabel
        #self.xlabel = ''; self.ylabel = ''

    def draw( self ):
        results = self.parsed_data
        if len( results.items() ) == 0:
          return None
        keys = self.sort_keys( results )
        tmp_x = []; tmp_y = []; yerr = []; color = []
    
        width = float(self.width)
        if self.string_mode:
            width = (1 - self.bar_graph_space) * width
            offset = self.bar_graph_space / 2.0
        else:
            offset = 0
        keys = self.sort_keys( results )
        for pivot in keys:
          data = results[pivot]
          print data, self.color_override
          if data != None:
            if data in self.color_override:
                color.append(self.color_override[data])
            else:
                color.append( self.mapper.to_rgba( data ) )
            tmp_y.append( data )
            if self.string_mode:
                transformed = self.transform_strings( pivot )
                tmp_x.append( transformed + offset )
            else:
                tmp_x.append( pivot + offset )
        self.bars = self.ax.barh( tmp_x, tmp_y, height=width, color=color )
            
        setp( self.bars, linewidth=0.5 )
        pivots = keys
        for idx in range(len(pivots)):
          self.coords[ pivots[idx] ] = self.bars[idx]
        if self.string_mode:
            ymax = max(tmp_y); ymax *= 1.1
            self.ax.set_ylim( ymin=0, ymax=len(self.string_map.keys()) )

        # Make the colorbar
        # Calculate padding
        pad_pix = self.additional_vertical_padding()
        height_inches = self.fig.get_size_inches()[-1]
        pad_perc = pad_pix / self.fig.get_dpi() / height_inches / 2.0
        cb = self.fig.colorbar( self.mapper, format="%d%%", 
                                orientation='horizontal', fraction=0.04, 
                                pad=pad_perc, aspect=40  )
        setp( cb.outline, linewidth=.5 )
        setp( cb.ax.get_xticklabels(), size=10 )
        setp( cb.ax.get_xticklabels(), family=self.prefs['font_family'] )
        setp( cb.ax.get_xticklabels(), fontname = self.prefs['font'] )
        self.ax.set_xlim( xmin=0, xmax=100 )
        
    def additional_vertical_padding(self):
        """
        The quality bar graph needs about 120 extra pixels at the bottom of
        the graph to place the color legend.
        """
        return 120

    def parse_data( self ):
        """
        The QualityBarGraph actually does quite a bit of preprocessing of data,
        as it needs to convert all the data into a percentage between 0-100.
        
        See the QualityMap class for more explanation of what kind of data this
        class can process; it can do multiple columns, two columns, or direct
        percentages.
        """
        self.multi_column = False
        self.two_column = False
        self.percentages = False

        results = getattr(self,'parsed_data',self.results)
        # Determine the columns to use; deprecated.
        if 'done_column' in self.metadata:
            self.done_column = int( self.metadata.get('done_column',1) )
            self.fail_column = int( self.metadata.get('fail_column',2) )
            self.multi_column = True
        else:
            # See if the values are tuples.
            found_data = False
            for key, val in results.items():
                found_data = True
                first_data = val
            if type(first_data) == types.TupleType or type(found_data) == types.ListType:
                assert len(first_data) == 2
                self.two_column = True
            else:
                self.percentages = True
        return super( QualityBarGraph, self ).parse_data( )

    def parse_datum( self, data ):
        if self.multi_column or self.two_column:
          if self.multi_column:
              try:
                  attempted, done, fail = data[try_column], data[done_column], data[fail_column]
              except Exception, e:
                  done = 0; fail = 0;
          if self.two_column:
              done, fail = data
          if float(done) > 0:
            value = done / float( fail + done )
          elif float(done) > 0 or float(fail) > 0:
            value = 0.0
        elif self.percentages:
            value = data
        if value != None: 
            return float(value)*100
        return None
    
class StackedBarGraph( PivotGroupGraph ):

  is_timestamps = False

  def setup(self):
      super(StackedBarGraph, self).setup()

  def make_bottom_text( self ):
    units = str(self.metadata.get('column_units','')).strip()
    vars = getattr( self, 'vars', {} )
    span = find_info('span', vars, self.metadata, None)
    agg_stats = {}
    results = getattr(self,'parsed_data',self.results)
    if self.is_timestamps and span != None:
        starttime = self.begin
        starttime = starttime - (starttime % float(span))
        agg_stats[starttime] = 0
    for link, groups in results.items():
      for timebin, value in groups.items():
        if agg_stats.has_key(timebin):
          agg_stats[timebin] += value
        else:
          agg_stats[timebin] = value
    try:
        if self.is_timestamps:
            data_min, data_max, data_average, data_current = statistics( agg_stats, span, True )
        else:
            data_min, data_max, data_average = statistics( agg_stats, span )
    except Exception, e:
        values = agg_stats.values()
        try: data_max = max(values)
        except: data_max = None
        try: data_min = min(values)
        except: data_min = None
        try: data_average = numpy.average( values )
        except: data_average = None
        try:
          last_time = max( agg_stats.keys() )
          data_current = agg_stats[last_time]
        except: data_current = None
    retval = ''
    if data_max != None: retval += "Maximum: " + pretty_float( data_max ) + " " + units
    if data_min != None: retval += ", Minimum: " + pretty_float( data_min ) + " " + units
    if data_average != None: retval += ", Average: " + pretty_float( data_average ) + " " + units
    if self.is_timestamps:
        if data_current != None: retval += ", Current: " + pretty_float( data_current ) + " " + units
    return retval

  def draw(self):
    vars = getattr( self, 'vars', {} )
    self.width = find_info('span',vars,self.metadata,1.0)
    results = getattr(self,'parsed_data',self.results)
    bottom = None
    colors = list(self.colors)
    coords = self.coords
    keys = self.sort_keys(results)
    keys = list(keys)
    keys.reverse()
    info = zip(keys,colors); #info.reverse()
    for pivot,color in info:
      if self.string_mode:
          transformed = self.transform_strings(results[pivot])
          bottom, bars = self.make_stacked_bar( transformed, bottom, color )
      else:
          bottom, bars = self.make_stacked_bar(results[pivot], bottom, color)
      groups = results[pivot].keys(); groups.sort() 
      coords[pivot] = {}
      bar_dict = {}
      for bar in bars:
          bar_dict[ bar.get_verts()[0][0] ] = bar
      bars_keys = bar_dict.keys(); bars_keys.sort() 
      for idx in range(len(groups)):
          coords[pivot][groups[idx]] = bar_dict[ bars_keys[idx] ]
    if self.string_mode:
        if self.log_xaxis:
            xmin = 0.001
        else:
            xmin = 0 
        self.ax.set_xlim( xmin=xmin, xmax=len(self.string_map.keys()) )

  def transform_strings(self, groupings ):
      smap = self.string_map
      new_groupings = {}
      try:
          for group, data in groupings.items():
              new_groupings[smap[group]] = data
      except Exception, e:
          raise Exception( "While transforming strings to coordinates, encountered an unknown string: %s" % group)
      return new_groupings
  
  def parse_data(self):
    # Start off by looking for strings in the groups.
    self.string_mode = False
    for pivot, groups in getattr(self,'parsed_data',self.results).items():
      for group in groups.keys():
        if type(group) == types.StringType:
          self.string_mode = True; break
      if self.string_mode == True: break
        
    self.string_map = {}
    self.next_value = 0
    # Then parse as normal
    super( StackedBarGraph, self ).parse_data()

  def parse_group(self, group):
      
      if self.string_mode:
          group = str(group)
    
          # Return if we've already seen this string
          if self.string_map.get(group,-1) == -1:
              # Otherwise, add it to the hash map
              self.string_map[group] = self.next_value
              self.next_value += 1
              
      return super( StackedBarGraph, self ).parse_group( group )
      
  def make_stacked_bar( self, points, bottom, color ):
    if bottom == None:
      bottom = {}
    tmp_x = []; tmp_y = []; tmp_b = []

    for key in points.keys():
      if self.is_timestamps:
        key_date = datetime.datetime.utcfromtimestamp( key )
        key_val = date2num( key_date )
      else:
        key_val = key
      tmp_x.append( key_val )
      tmp_y.append( points[key] )
      if not bottom.has_key( key ):
        if self.log_yaxis:
            bottom[key] = 0.001
        else:
            bottom[key] = 0
      tmp_b.append( bottom[key] )
      bottom[key] += points[key]
    if len( tmp_x ) == 0:
      return bottom, None
    width = float(self.width)
    if self.is_timestamps:
        width = float(width) / 86400.0
    elif self.string_mode:
        tmp_x = [i + .1*width for i in tmp_x]
        width = .8 * width
    bars = self.ax.bar( tmp_x, tmp_y, bottom=tmp_b, width=width, color=color )
    setp( bars, linewidth=0.5 )
    return bottom, bars

  def get_coords( self ):
    coords = self.coords
    keys = self.sort_keys(self.parsed_data)
    for pivot in keys:
      groupings = coords[pivot]
      for group, p in groupings.items():
        t = p.get_transform()
        my_coords = t.seq_xy_tups( p.get_verts() )
        height = self.prefs['height']
        coords[pivot][group] = tuple( [(i[0],height-i[1]) for i in my_coords] )
    self.coords = coords
    return coords

  def x_formatter_cb( self, ax ):
      if self.string_mode:
          smap = self.string_map
          reverse_smap = {}
          for key, val in smap.items():
              reverse_smap[val] = key
          ticks = smap.values(); ticks.sort()
          ax.set_xticks( [i+.5 for i in ticks] )
          ax.set_xticklabels( [reverse_smap[i] for i in ticks] )
          labels = ax.get_xticklabels()
          ax.grid( False )
          if self.log_xaxis:
              xmin = 0.001
          else:
              xmin = 0 
          ax.set_xlim( xmin=xmin,xmax=len(ticks) )
      else:
          try:
              super(StackedBarGraph, self).x_formatter_cb( self, ax )
          except:
              return None

class ScatterPlot(PivotGroupGraph):

    def scatter(self, data, color):
        groups = data.keys()
        groups.sort()
        patches = []
        xcoords = []
        ycoords = []
        radii = []
        for coords in groups:
            size = data[coords]
            radius = math.sqrt(size/math.pi)
            radii.append(radius)
            xcoords.append(coords[0])
            ycoords.append(coords[1])
            c = Circle(coords, radius, facecolor=color)
            self.ax.add_patch(c)
            patches.append(c)
        max_radii = max(radii)
        self.min_x = min(min(xcoords)-max_radii, self.min_x)
        self.min_y = min(min(ycoords)-max_radii, self.min_y)
        self.max_x = max(max(xcoords)+max_radii, self.max_x)
        self.max_y = max(max(ycoords)+max_radii, self.max_y)
        return patches

    def x_formatter_cb(self, ax):
        ax.set_xlim(xmin=self.min, xmax=self.max)

    def y_formatter_cb(self, ax):
        ax.set_ylim(ymin=self.min, ymax=self.max)

    def prepare_canvas( self ):
        self.min_x, self.min_y, self.max_x, self.max_y = 0.0, 0.0, 0.0, 0.0
        for _, groups in self.parsed_data.items():
            xcoords = []
            ycoords = []
            radii = []
            for coords, size in groups.items():
                radius = math.sqrt(size/math.pi)
                radii.append(radius)
                xcoords.append(coords[0])
                ycoords.append(coords[1])
            max_radii = max(radii)
            self.min_x = min(min(xcoords)-max_radii, self.min_x)
            self.min_y = min(min(ycoords)-max_radii, self.min_y)
            self.max_x = max(max(xcoords)+max_radii, self.max_x)
            self.max_y = max(max(ycoords)+max_radii, self.max_y)
        self.min = min(self.min_x, self.min_y)
        self.max = min(self.max_x, self.max_y)
        self.kw['square_axis'] = True
        super(ScatterPlot, self).prepare_canvas()

    def draw(self):
        vars = getattr(self, 'vars', {})
        self.width = find_info('span',vars,self.metadata,1.0)
        results = getattr(self,'parsed_data',self.results)
        colors = list(self.colors)
        coords = self.coords
        keys = self.sort_keys(results)
        keys = list(keys)
        keys.reverse()
        info = zip(keys,colors); #info.reverse()
        for pivot,color in info:
          dots = self.scatter(results[pivot], color)
          groups = results[pivot].keys(); groups.sort() 
          coords[pivot] = {}
          dot_dict = {}
          for dot in dots:
              dot_dict[ dot.get_verts()[0][0] ] = dot
          dots_keys = dot_dict.keys(); dots_keys.sort() 
          for idx in range(len(groups)):
              coords[pivot][groups[idx]] = dot_dict[ dots_keys[idx] ]
    
    def get_coords( self ):
      coords = self.coords
      keys = self.sort_keys(self.parsed_data)
      for pivot in keys:
          groupings = coords[pivot]
          for group, p in groupings.items():
              t = p.get_transform()
              my_coords = t.seq_xy_tups( p.get_verts() )
              height = self.prefs['height']
              coords[pivot][group] = tuple( [(i[0],height-i[1]) for i in my_coords] )
      self.coords = coords
      return coords
      
class StackedLineGraph(StackedBarGraph):

  def make_stacked_bar( self, points, bottom, color ):
        
    span = self.width
    ax = self.ax
    begin = self.begin; end = self.end
    if bottom == None: bottom = {}
        
    new_points = {}
    if self.is_timestamps:
      for group, data in points.items():
        key_date = datetime.datetime.utcfromtimestamp( group )
        key_val = date2num( key_date )
        new_points[ key_val ] = data
      points = new_points 
      begin = date2num( datetime.datetime.utcfromtimestamp( self.begin ) )
      end = date2num( datetime.datetime.utcfromtimestamp( self.end ) )
      
    min_key = min(points.keys())
    if min_key - begin > span:
      points[min_key-span] = points[min_key]
    
    # Get the union of all times:
    times_set = set( points.keys() )
    times_set = times_set.union( bottom.keys() )
    times_set.add( end ) 
    times_set.add( begin )
     
    my_times = list( times_set ); my_times.sort(); my_times.reverse()

    bottom_keys = list(bottom.keys()); bottom_keys.sort()
    points_keys = list(points.keys()); points_keys.sort()

    polygons = []; seq = []; next_bottom = {}
    if len( bottom.keys() ) > 0:
      prev_bottom_val = max( bottom.values() )
    else:
      prev_bottom_val = 0
    if len( points.keys() ) > 0:
      last_val = max(points.keys())
      prev_val = points[last_val]
    else:
      prev_val = 0
    prev_key = my_times[-1]
    for key in my_times:
      if not bottom.has_key( key ):
        my_bottom_keys = list(bottom_keys)
        my_bottom_keys.append( key )
        my_bottom_keys.sort()
        if my_bottom_keys[0] == key:
          bottom[key] = 0
        else:
          next_key = my_bottom_keys[ my_bottom_keys.index(key)-1 ]
          next_val = bottom[ next_key ]
          bottom[key] = (prev_bottom_val - next_val)*(key-next_key)/float(prev_key-next_key) + next_val
      if not points.has_key( key ):
        if key <= points_keys[0] and key != end:
          points[key] = points[points_keys[0]]
        else:
          points[key] = prev_val
      prev_bottom_val = bottom[key]
      prev_val = points[key]
      prev_key = key
      val = points[key] + bottom[key]
      next_bottom[key] = val
      y = val
      x = key
      seq.append( (x,y) )
      next_bottom[key] = val
    my_times.reverse()
    for key in my_times:
      y = float(bottom[key])
      x = key
      seq.append( (x,y) )
    poly = Polygon( seq, facecolor=color, fill=True, linewidth=.5 )
    ax.add_patch( poly )
    polygons.append( poly )
    new_ymax = max(max(next_bottom.values())+.5, ax.axis()[3])
    ax.set_xlim( xmin=float(my_times[0]), xmax=float(my_times[-1]) )
    ax.set_ylim( ymax = new_ymax )
    return next_bottom, polygons

  def draw( self ):
    
    results = getattr( self, 'parsed_data', self.results )
    colors = self.colors
    bottom = None
    coords = self.coords
    keys = self.sort_keys( results ); keys.reverse()
    info = zip(keys,colors); #info.reverse()
    for link, color in info:
      bottom, bars = self.make_stacked_bar( results[link], bottom, color )
      coords[ link ] = bars[0]

  def get_coords( self ):
    results =  getattr( self, 'parsed_data', self.results )
    links = self.coords
    if len(links.keys()) == 0: return None

    height = self.prefs['height']
    coords = {}
    for link in links:
      coords[link] = {}
    transform = links.values()[0].get_transform()
    timebins = results.values()[0].keys(); timebins.sort()
    timebins_num = [date2num( datetime.datetime.utcfromtimestamp( to_timestamp( timebin ) ) ) for timebin in timebins]
    keys = self.sort_keys( results ); keys.reverse()
    for idx in range(len(timebins)-1):
      timebin = timebins[idx]
      timebin_next = timebins[idx+1]
      timebin_num = timebins_num[idx]
      csum_left = 0; csum_right = 0
      for pivot in keys:
        groups = results[pivot]
        time_begin = timebin_num
        time_end = time_begin + self.width/86400.0
        size_left = groups[timebin]
        size_right = groups[timebin_next]
        bottom_left = csum_left
        csum_left += size_left
        bottom_right = csum_right
        csum_right += size_right
        my_coords = transform.seq_xy_tups( [(time_begin, bottom_left), (time_begin, csum_left), \
                    (time_end, csum_right), (time_end, bottom_right), (time_begin, bottom_left)] )
        coords[pivot][timebin] = tuple( [(i[0],height-i[1]) for i in my_coords] )
    timebin = timebins[-1]
    timebin_num = timebins_num[-1]
    csum_left = 0; csum_right = 0
    for pivot in keys:
      groups = results[pivot]
      time_begin = timebin_num
      time_end = self.end_num
      size_left = groups[timebin]
      bottom_left = csum_left
      csum_left += size_left
      my_coords = transform.seq_xy_tups( [(time_begin, bottom_left), (time_begin, csum_left), \
                  (time_end, csum_left), (time_end, bottom_left), (time_begin, bottom_left)] )
      coords[pivot][timebin] = tuple( [(i[0],height-i[1]) for i in my_coords] )

    self.coords = coords
    return coords

class HorizontalStackedBarGraph( HorizontalGraph, StackedBarGraph ):

    """
    The HorizontalStackedBarGraph is just like the StackedBarGraph class, 
    except the bars are placed horizontally; the independent variable is along 
    the y-axis.
    """
    
    def draw( self ):
        vars = getattr( self, 'vars', {} )
        self.width = find_info('span',vars,self.metadata,1.0)
        results = getattr(self,'parsed_data',self.results)
        bottom = None
        colors = list(self.colors)
        coords = self.coords
        keys = self.sort_keys( results ); keys.reverse()
    
        for pivot,color in zip(keys,colors):
            if self.string_mode:
                transformed = self.transform_strings( results[pivot] )
                bottom, bars = self.make_stacked_bar( transformed, bottom, color )
            else:
                bottom, bars = self.make_stacked_bar( results[pivot], bottom, color )
            groups = results[pivot].keys(); groups.sort() 
            coords[pivot] = {}
            bar_dict = {}
            for bar in bars:
                bar_dict[ bar.get_verts()[0][1] ] = bar
            bars_keys = bar_dict.keys(); bars_keys.sort() 
            for idx in range(len(groups)):
                coords[pivot][groups[idx]] = bar_dict[ bars_keys[idx] ]
        
        if self.string_mode:
            self.ax.set_ylim( ymin=0, ymax=len(self.string_map.keys()) )

    
    def make_stacked_bar( self, points, bottom, color ):
        if bottom == None:
            bottom = {}
        tmp_x = []; tmp_y = []; tmp_b = []
    
        for key in points.keys():
            if self.is_timestamps:
                key_date = datetime.datetime.utcfromtimestamp( key )
                key_val = date2num( key_date )
            else:
                key_val = key
            tmp_x.append( key_val )
            tmp_y.append( points[key] )
            if not bottom.has_key( key ):
                if self.log_yaxis:
                    bottom[key] = 0.001
                else:
                    bottom[key] = 0
            tmp_b.append( bottom[key] )
            bottom[key] += points[key]
        if len( tmp_x ) == 0:
            return bottom, None
        width = float(self.width)
        if self.is_timestamps:
            width = float(width) / 86400.0
        elif self.string_mode:
            tmp_x = [i + .1*width for i in tmp_x]
            width = .8 * width
        bars = self.ax.barh( tmp_x, tmp_y, left=tmp_b, height=width, color=color )
        setp( bars, linewidth=0.5 )
        return bottom, bars
    
    def x_formatter_cb( self, ax ):
        """
        The x_formatter_cb - calls the PivotGraph directly, skipping the 
        HorizontalGraph.
        """
        try:
            super( PivotGraph, self ).x_formatter_cb( ax )
        except:
            pass
    
    def y_formatter_cb( self, ax ):
        if self.string_mode:
            smap = self.string_map
            reverse_smap = {}
            for key, val in smap.items():
                reverse_smap[val] = key
            ticks = smap.values(); ticks.sort()
            ax.set_yticks( [i+.5 for i in ticks] )
            ax.set_yticklabels( [reverse_smap[i] for i in ticks] )
            labels = ax.get_yticklabels()
            ax.grid( False )
            ax.set_ylim( ymin=0,ymax=len(ticks) )
        else:
            try:
                super( PivotGraph, self).y_formatter_cb( ax )
            except:
                return None
         
class CumulativeGraph( TimeGraph, PivotGroupGraph ):
 
  def make_bottom_text( self ):
    results = self.results 
    units = str(self.metadata.get('column_units','')).strip()
    agg_stats = {} 
    data_max = 0
    for pivot, groups in results.items():
      if self.is_cumulative:
          try:
              data_max += max(groups.values())
          except:
              pass
      else:
          data_max += sum(groups.values())
  
    timespan = (self.end_num - self.begin_num)*86400.0

    retval = "Total: " + pretty_float( data_max ) + " " + units
    retval += ", Average Rate: " + pretty_float( data_max / timespan ) + " " + units + "/s"
    return retval

  def make_labels_common(self, results):
      labels = super(CumulativeGraph, self).make_labels_common(results)
      label_nums = {}
      for pivot, groups in results.items():
        timebins = groups.keys(); timebins.sort()
        if timebins:
            if self.is_cumulative:
                label_nums[pivot] = groups[timebins[-1]]
            else:
                label_nums[pivot] = sum(groups.values())
      new_labels = []
      for label in labels:
          if label in label_nums:
              num = float(label_nums[label])
              label = '%s (%s)' % (label, pretty_float(num))
          new_labels.append(label)
      return new_labels

  def setup( self ):
    
    is_cumulative = self.metadata.get( 'is_cumulative', None )

    if isinstance(is_cumulative, types.StringType):
        is_cumulative = is_cumulative.lower().find("f") < 0 and \
             is_cumulative.lower().find("n") < 0
    self.is_cumulative = is_cumulative

    super( CumulativeGraph, self ).setup()
    results = getattr( self, 'parsed_data', self.results)

    if is_cumulative == None:
      raise Exception( "The is_cumulative metadata was not set; set to true if data is cumulative, false otherwise." )

    if is_cumulative == False and results:
        # A routine to turn pivot-group data into cumulative data.
        data = {}
        span = self.metadata.get('span', None)
        if span == None:
            raise Exception( "Span is a required metadata value if is_cumulative=False." )
        # Figure out all the timebins:
        timebins = set()
        for key, value in results.items():
            for group in value.keys():
                timebins.add(group)
        timebins_list = []
        min_timebin = min(timebins); max_timebin = max(timebins);
        cur_timebin = min_timebin
        while cur_timebin <= max_timebin:
            timebins_list.append(cur_timebin)
            if cur_timebin in timebins:
                timebins.remove(cur_timebin)
            cur_timebin += span
        if len(timebins) > 0:
            raise Exception("Some data is not aligned to timebins!  Extra values are: %s" % str(timebins))
        for key, value in results.items():
            groups = value.keys()
            csum = 0
            cur_dict = {}
            data[key] = cur_dict
            for timebin in timebins_list:
                if timebin in groups:
                    csum += value[timebin]
                cur_dict[timebin] = csum
        self.parsed_data = data
    

  def make_stacked_line( self, points, bottom, color ):

    span = self.width
    ax = self.ax
    begin = self.begin; end = self.end
    if bottom == None: bottom = {}

    new_points = {}
    if self.is_timestamps:
      for group, data in points.items():
        key_date = datetime.datetime.utcfromtimestamp( group )
        key_val = date2num( key_date )
        new_points[ key_val ] = data
      points = new_points
      begin = date2num( datetime.datetime.utcfromtimestamp( self.begin ) )
      end = date2num( datetime.datetime.utcfromtimestamp( self.end ) )

    min_key = min(points.keys())
    if min_key - begin > span:
      points[min_key-span] = 0
    
    # Get the union of all times:
    times_set = set( points.keys() )
    times_set = times_set.union( bottom.keys() )
    times_set.add( end )
    times_set.add( begin )
     
    my_times = list( times_set ); my_times.sort(); my_times.reverse()
      
    bottom_keys = list(bottom.keys()); bottom_keys.sort()
    points_keys = list(points.keys()); points_keys.sort()

    polygons = []; seq = []; next_bottom = {}
    if len( bottom.keys() ) > 0:
      prev_bottom_val = max( bottom.values() )
    else:
      prev_bottom_val = 0
    if len( points.keys() ) > 0:
      prev_val = max( points.values() )
    else:
      prev_val = 0
    prev_key = my_times[-1]
    for key in my_times:
      if not bottom.has_key( key ):
        my_bottom_keys = list(bottom_keys)
        my_bottom_keys.append( key )
        my_bottom_keys.sort()
        if my_bottom_keys[0] == key:
          bottom[key] = 0
        else:
          next_key = my_bottom_keys[ my_bottom_keys.index(key)-1 ]
          next_val = bottom[ next_key ]
          bottom[key] = (prev_bottom_val - next_val)*(key-next_key)/float(prev_key-next_key) + next_val
      if not points.has_key( key ):
        if key <= points_keys[0] and key != end:
          points[key] = 0
        else:
          points[key] = prev_val
      prev_bottom_val = bottom[key]
      prev_val = points[key]
      prev_key = key
      val = points[key] + bottom[key]
      next_bottom[key] = val
      y = val
      x = key
      seq.append( (x,y) )
      next_bottom[key] = val
    my_times.reverse()
    for key in my_times:
      y = float(bottom[key])
      x = key
      seq.append( (x,y) )
    poly = Polygon( seq, facecolor=color, fill=True, linewidth=.5 )
    ax.add_patch( poly )
    polygons.append( poly )
    new_ymax = max(max(next_bottom.values())+.5, ax.axis()[3])
    ax.set_xlim( xmin=float(my_times[0]), xmax=float(my_times[-1]) )
    ax.set_ylim( ymax = new_ymax )
    return next_bottom, polygons

  def draw( self ):

    results = getattr( self, 'parsed_data', self.results )
    colors = self.colors
    bottom = None
    coords = self.coords
    keys = self.sort_keys( results ); keys.reverse()
    info = zip(keys,colors); #info.reverse()
    for link, color in info:
      bottom, bars = self.make_stacked_line( results[link], bottom, color )
      coords[ link ] = bars[0]  

  def get_coords( self ):
    results =  getattr( self, 'parsed_data', self.results )
    links = self.coords
    if len(links.keys()) == 0: return None

    height = self.prefs['height']
    coords = {}
    for link in links:
      coords[link] = {}
    transform = links.values()[0].get_transform()
    timebins = results.values()[0].keys(); timebins.sort()
    timebins_num = [date2num( datetime.datetime.utcfromtimestamp( to_timestamp( timebin ) ) ) for timebin in timebins]
    keys = self.sort_keys( results ); keys.reverse()
    for idx in range(len(timebins)-1):
      timebin = timebins[idx]
      timebin_next = timebins[idx+1]
      timebin_num = timebins_num[idx]
      csum_left = 0; csum_right = 0
      for pivot in keys:
        groups = results[pivot]
        time_begin = timebin_num
        time_end = time_begin + self.width/86400.0
        size_left = groups[timebin]
        size_right = groups[timebin_next]
        bottom_left = csum_left
        csum_left += size_left
        bottom_right = csum_right
        csum_right += size_right
        my_coords = transform.seq_xy_tups( [(time_begin, bottom_left), (time_begin, csum_left), \
                    (time_end, csum_right), (time_end, bottom_right), (time_begin, bottom_left)] )
        coords[pivot][timebin] = tuple( [(i[0],height-i[1]) for i in my_coords] )
    timebin = timebins[-1]
    timebin_num = timebins_num[-1]
    csum_left = 0; csum_right = 0
    for pivot in keys:
      groups = results[pivot]
      time_begin = timebin_num
      time_end = self.end_num
      size_left = groups[timebin]
      bottom_left = csum_left
      csum_left += size_left
      my_coords = transform.seq_xy_tups( [(time_begin, bottom_left), (time_begin, csum_left), \
                  (time_end, csum_left), (time_end, bottom_left), (time_begin, bottom_left)] )
      coords[pivot][timebin] = tuple( [(i[0],height-i[1]) for i in my_coords] )

    self.coords = coords
    return coords

class PieGraph( PivotGraph ):

  def pie(self, x, explode=None, labels=None,
            colors=None,      
            autopct=None,
            pctdistance=0.6,
            shadow=False
            ):
            
        x = numpy.array(x, numpy.float64)

        sx = float(numpy.sum(x))
        if sx>1: x = numpy.divide(x,sx)
            
        if labels is None: labels = ['']*len(x)
        if explode is None: explode = [0]*len(x)
        assert(len(x)==len(labels))
        assert(len(x)==len(explode))
        if colors is None: colors = ('b', 'g', 'r', 'c', 'm', 'y', 'k', 'w')

        center = 0,0
        radius = 1
        theta1 = 0
        i = 0   
        texts = []
        slices = []
        autotexts = []
        color_override = self.color_override
        results = self.parsed_data
        for frac, label, expl in zip(x,labels, explode):
            x, y = center 
            theta2 = theta1 + frac
            thetam = 2*math.pi*0.5*(theta1+theta2)
            x += expl*math.cos(thetam)
            y += expl*math.sin(thetam)
            if color_override == {}:
                w = Wedge((x,y), radius, 360.*theta1, 360.*theta2,
                          facecolor=colors[i%len(colors)])
            else:
                mycolour = color_override[label]
                w = Wedge((x,y), radius, 360.*theta1, 360.*theta2,
                                  facecolor=mycolour)
            slices.append(w)
            self.ax.add_patch(w)
            w.set_label(label)
            
            if shadow:
                # make sure to add a shadow after the call to
                # add_patch so the figure and transform props will be
                # set
                shad = Shadow(w, -0.02, -0.02,
                              #props={'facecolor':w.get_facecolor()}
                              )
                shad.set_zorder(0.9*w.get_zorder())
                self.ax.add_patch(shad)

            
            xt = x + 1.1*radius*math.cos(thetam)
            yt = y + 1.1*radius*math.sin(thetam)
            
            thetam %= 2*math.pi
            
            if 0 <thetam and thetam < math.pi:
                valign = 'bottom'
            elif thetam == 0 or thetam == math.pi:
                valign = 'center'
            else:
                valign = 'top'
            
            if thetam > math.pi/2.0 and thetam < 3.0*math.pi/2.0:
                halign = 'right'
            elif thetam == math.pi/2.0 or thetam == 3.0*math.pi/2.0:
                halign = 'center'
            else:
                halign = 'left'
            if float(results[label]) / self.amt_sum  > self.min_amount:
                t = self.ax.text(xt, yt, label,
                          size=self.prefs['subtitle_size'],
                          horizontalalignment=halign,
                          verticalalignment=valign)
            
                t.set_family( self.prefs['font_family'] )
                t.set_fontname( self.prefs['font'] )
                t.set_size( self.prefs['subtitle_size'] )

                texts.append(t)
            
            if autopct is not None:
                xt = x + pctdistance*radius*math.cos(thetam)
                yt = y + pctdistance*radius*math.sin(thetam)
                if is_string_like(autopct):
                    s = autopct%(100.*frac)
                elif callable(autopct):
                    s = autopct(100.*frac)
                else:                    raise TypeError('autopct must be callable or a format string')
                
                t = self.ax.text(xt, yt, s,
                              horizontalalignment='center',
                              verticalalignment='center')
                
                t.set_family( self.prefs['font_family'] )
                t.set_fontname( self.prefs['font'] )
                t.set_size( self.prefs['subtitle_size'] )
                
                autotexts.append(t)

            
            theta1 = theta2
            i += 1
        
        self.ax.set_xlim((-1.25, 1.25))
        self.ax.set_ylim((-1.25, 1.25))
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        
        self.ax.set_frame_on(False)

        if autopct is None: return slices, texts
        else: return slices, texts, autotexts

  min_amount = .1

  def setup( self ):
    super( PieGraph, self ).setup()

    results = self.results
    parsed_data = self.parsed_data
    self.color_override = self.metadata.get('color_override', {})

    column_units = getattr( self, 'column_units', self.metadata.get('column_units','') )
    column_units = column_units.strip()
    sql_vars = getattr( self, 'vars', {} )
    title = getattr( self, 'title', self.metadata.get('title','') )

    if len(column_units) > 0:
      title += ' (Sum: %i ' + column_units + ')'
    else:
      title += ' (Sum: %i)'
    title = expand_string( title, sql_vars )
  
    labels = []
    amt = [] 
    keys = self.sort_keys( parsed_data )
    for key in keys:
      labels.append( str(key) + (' (%i)' % round(float(parsed_data[key]))) )
      amt.append( float(parsed_data[key]) )
    self.labels = labels
    self.labels.reverse()
    self.title = title % int(float(sum(amt)))
    self.amt_sum = float(sum(amt))
    self.amt = amt

    #labels.reverse()

  def prepare_canvas( self ):
    self.ylabel = ''
    self.kw['square_axis'] = True
    self.kw['watermark'] = False
    super( PieGraph, self ).prepare_canvas()

  def draw( self ):
    amt = self.amt
    results = self.parsed_data
    my_labels = []
    local_labels = list(self.labels); local_labels.reverse()
    for label in local_labels:
      orig_label = label[:label.rfind(' ')]
      val = float(results[orig_label])
      my_labels.append( orig_label )

    def my_display( x ):
      if x > 100*self.min_amount:
        my_amt = int(x/100.0 * self.amt_sum )
        return str(my_amt)
      else:
        return ""

    explode = [.1 for i in amt]

    self.colors.reverse()
    if self.color_override == {}:
        self.wedges, text_labels, percent = self.pie( amt, explode=explode, 
                                                      labels=my_labels, shadow=True, colors=self.colors, autopct=my_display )
    else:
        self.wedges, text_labels, percent = self.pie( amt, explode=explode, 
                                                      labels=my_labels, shadow=True, colors=self.color_override.values(), autopct=my_display )
    
  def get_coords( self ):
    try:
      coords = self.coords
      height = self.prefs['height']
      wedges = self.wedges
      labels = self.labels
      wedges_len = len(wedges)
      for idx in range(wedges_len):
        my_label = labels[idx] 
        orig_label = my_label[:my_label.rfind(' ')]
        wedge = wedges[ wedges_len - idx - 1 ]
        v = wedge.get_verts()
        t = wedge.get_transform()
        my_coords = t.seq_xy_tups( v )
        coords[ orig_label ] = tuple( [(i[0],height-i[1]) for i in my_coords] )
      self.coords = coords
      return coords
    except:
      return None

class QualityMap( HorizontalGraph, TimeGraph, PivotGroupGraph ):

  sort_keys = Graph.sort_keys

  def num_labels( self ):
      return len(self.labels)

  def setup( self ):

    super( QualityMap, self ).setup()

    results = self.parsed_data
    self.xlabel = ''; self.ylabel = ''
    
    self.multi_column = False
    self.two_column = False
    self.percentages = False

    self.color_override = self.metadata.get("color_override", {})
    
    # Determine the columns to use; deprecated.
    if 'done_column' in self.metadata:
        self.done_column = int( self.metadata.get('done_column',1) )
        self.fail_column = int( self.metadata.get('fail_column',2) )
        self.multi_column = True
    else:
        # See if the values are tuples.
        found_data = False
        for key, val in results.items():
            for group, data in val.items():
                found_data = True
                first_data = data
                break
            if found_data: break
        if found_data:
            if type(first_data) == types.TupleType or type(found_data) == types.ListType:
                assert len(first_data) >= 2
                self.two_column = True
            else:
                self.percentages = True
        else:
            # No data
            return

    # Rearrange our data
    timebins = set()
    for link in self.sort_keys(results):
      for timebin in results[link].keys():
        timebins.add( timebin )
    links = self.sort_keys(results); 
    links.reverse(); timebins = list(timebins)
    links_lu = {}; timebins_lu = {}
    counter = 0
    for link in links: links_lu[link] = counter; counter += 1
    counter = 0
    for bin in timebins: timebins_lu[bin] = counter; counter += 1

    # Setup the colormapper to get the right colors
    norms = normalize(0,100)
    mapper = cm.ScalarMappable(cmap=cm.RdYlGn, norm=norms)
    def get_alpha(*args, **kw):
        return 1.0
    mapper.get_alpha = get_alpha
    A = linspace(0,100,100)
    mapper.set_array(A)
    self.links = links
    self.links_lu = links_lu
    self.mapper = mapper

    #self.labels.reverse()
    
  def draw_legend(self):
        custom_legend = 'legend' in self.metadata and self.metadata['legend']
      
        # Standard colorbar legend
        if not custom_legend:
            # Make the colorbar
            # Calculate padding
            pad_pix = self.additional_vertical_padding()
            height_inches = self.fig.get_size_inches()[-1]
            pad_perc = pad_pix / self.fig.get_dpi() / height_inches / 2.0
            cb = self.fig.colorbar(self.mapper, format="%d%%", 
                                   orientation='horizontal', fraction=0.04,
                                   pad=pad_perc, aspect=40)
            setp( cb.outline, linewidth=.5 )
            setp( cb.ax.get_xticklabels(), size=10 )
            setp( cb.ax.get_xticklabels(), family=self.prefs['font_family'] )
            setp( cb.ax.get_xticklabels(), fontname = self.prefs['font'] )
            return
        
        # Legend creation taken from the base class
          
        # Create a legend for the specified colors
        legend = self.metadata['legend']
        default_labels = list(legend.keys())
        default_labels.sort()
        labels = getattr(self, 'legend_labels', default_labels)
        labels = list(labels)
        labels.reverse()
        num_labels = len(labels)
        colors = [legend[i] for i in labels]
        offset = 0
        early_stop = False
        zipped = zip(labels,colors)
        prefs = self.prefs

        column_height = (2 * prefs['text_padding'] + prefs['text_size']) / \
                    self.leg_pix_height

        legend_ax = self.fig.add_axes(self.legend_rect)
        legend_ax.set_axis_off()

        for my_text, my_color in zipped:
            # Size calculations
            left = (self.box_width+3*prefs['text_padding'])/ \
                self.leg_pix_width+self.column_width*(offset % prefs['columns'])
            top = 1 - (column_height)*(numpy.floor(offset / prefs['columns']))
            next_bottom = 1 - (column_height)*(numpy.floor((offset+1)/ \
                prefs['columns']))

            # Stop early if we ran out of room.
            if next_bottom < 0 and (num_labels - offset > 1):
                early_stop = True
                break

            # Create text
            t = legend_ax.text(left, 1.2*self.box_width/self.leg_pix_height,
                str(my_text), horizontalalignment='left',
                verticalalignment='top', size=prefs['text_size'])
            t.set_fontname(prefs['font'])
            t.set_family(prefs['font_family'])

            # Create legend rectangle:
            patch = Rectangle(((self.column_width*(offset % prefs['columns']) + \
                1.2*prefs['text_padding']/self.leg_pix_width),
                0),
                1.2*self.box_width/self.leg_pix_width, 1.2*self.box_width/ \
                self.leg_pix_height)
            patch.set_ec('black')
            patch.set_linewidth(0.25)
            patch.set_fc(my_color)
            legend_ax.add_patch(patch)

            offset += 1

        # Set some additional text if we stopped early
        if early_stop == True:
            my_text = '... plus %i more' % (num_labels - offset)
            legend_ax.text(left, top, my_text, horizontalalignment='left',
                           verticalalignment='top', size = prefs['text_size'])
              

  def prepare_canvas( self ):
    self.legend = False
    super(QualityMap, self).prepare_canvas()
    self.draw_legend()
    setp( self.ax.get_yticklines(), markeredgewidth=0.0 )

    links = self.links

    # Make horizontal and vertical light grey lines every 3 ticks:
    lineskip = 2
    len_links = len(self.links); #len_ticks = len(ticks)
    for line_num in range(1,len_links):
      if (len_links - line_num) % lineskip == 0:
        self.ax.plot( [self.begin_num, self.end_num], [line_num, line_num], linewidth=1.0, color='k', linestyle=':' )
    self.ax.xaxis.grid(True)
    self.ax.yaxis.grid(False)
    self.ax.set_ylim( ymin=0, ymax=len(links) )

  def draw( self ):

    coords = self.coords
    ax = self.ax
    links = self.links
    links_lu = self.links_lu
    if self.multi_column:
        done_column, fail_column = self.done_column, self.fail_column
    results = self.parsed_data
    for link in self.sort_keys(results):
      coords[link] = {}
      l= results[link].keys()
      l.sort()
      l.reverse()
      try:
          previous_left=date2num( convert_to_datetime(self.metadata.get('endtime')) )
      except:
          previous_left = self.end_num
      new_width= self.width/86400.0


      for timebin in l:
        data = results[link][timebin]
        value = None
        if self.multi_column or self.two_column:
          if self.multi_column:
              try:
                  try_files, done, fail = data[try_column], data[done_column], data[fail_column]
              except Exception, e:
                  continue
          if self.two_column:
              done, fail = data[:2]
          if float(done) > 0:
            value = done / float( fail + done )
          elif float(done) > 0 or float(fail) > 0:
            value = 0.0
        if self.percentages:
            value = data
        if value != None:
          left = date2num( datetime.datetime.utcfromtimestamp( float(timebin) ) )
          bottom = links_lu[link]
          if value not in self.color_override:
              color = self.mapper.to_rgba( value*100 )
          else:
              color = self.color_override[value]
          if self.metadata.get('expand'):
              new_width=previous_left-left
              previous_left=left
          p = Rectangle( (left, bottom), new_width, 1.0, fill=True, fc=color )
          ax.add_patch(p)
          p.set_linewidth( 0.25 )
          t = p.get_transform()
          coords[link][timebin] = p
    
  def additional_vertical_padding(self):
      return 120

  def get_coords( self ):

    coords = self.coords
    height = self.prefs['height']
    keys = self.sort_keys( self.parsed_data )
    for pivot in keys:
      groups = coords[pivot] 
      for group, p in groups.items():
        t = p.get_transform()
        my_coords = t.seq_xy_tups( p.get_verts() )
        coords[pivot][group] = tuple( [(i[0],height-i[1]) for i in my_coords] )

    return coords

