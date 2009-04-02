
"""
Graph.py is the heart of the GraphTool package.  It provides the base Graph
class, from which all the others are derived.  GraphTool provides lots of
functionality - such as a standard look-and-feel above and beyond matplotlib.

The idea is to only need to pass the graph's data, the type of graph, and any
sort of metadata required for the graph, and to come out with a "print-quality"
graph.
"""

# System imports
import numpy
import cStringIO
import StringIO
import traceback
import time
import datetime
import warnings
import types
import os
import gc
import logging

log = logging.getLogger("GraphTool.Graph")

gclog = logging.getLogger("GraphTool.GC")

# PIL imports
import Image as PILImage, ImageEnhance as PILImageEnhance

# Graphtool imports
import graphtool.graphs.common as common

# matplotlib-related imports
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.figure import Figure
from matplotlib.ticker import FixedLocator, FixedFormatter
from matplotlib.backends.backend_svg import RendererSVG
from matplotlib.patches import Wedge, Shadow, Rectangle, Polygon
from matplotlib.numerix import Float32
from matplotlib.pylab import setp
from graphtool.tools.common import to_timestamp, expand_string
from graphtool.tools.cache import Cache
from graphtool.database.query_handler import QueryHandler
from matplotlib.dates import date2num

cStringIO_type = type(cStringIO.StringIO())

# These preferences are considered my "sane defaults", although one can
# certainly override them via the command line.  That said, they should
# probably be factored out into a separate config file.

prefs = {
  'text_size' : 7,    #Size of non-title text in graph; in pixels
  'text_padding' : 3, #Padding above and below text in legend; in pixels
  'legend_padding' : .01, # Padding between legend and the axes of the graph;
                          # In percent of screen space / 100
  'figure_padding' : 50, # Padding around the edge of the figure. in pixels
  'width' : 800,  #in pixels
  'height' : 500,
  'width_inches' : 8,    # Somewhat arbitrary, as dpi is adjusted to
                       # fit the pixel sizes requested above.
  'columns' : 5,    # The number of columns to use in the legend
  'max_rows' : 9,  # Maximum number of rows in the legend
  'title_size' : 14, # In pixels
  'subtitle_size' : 10,
  'font' : 'Lucida Grande',
  'font_family' : 'sans-serif',
  'square_axis' : False,
  'watermark' : '$GRAPHTOOL_ROOT/static_content/CMSbwl3.png',
  'fixed-height' : True
}

def draw_empty( text, file, kw ):
    """ Draw empty does exactly that; draws an empty graph with text in the
        center.  Perfect for times when there is no data to plot, but you at
        least want to inform your users of that.

        :Parameters:
            - `text` : Text string which will be in center of the output.
            - `file` : File-like object that the graph data will be written to.
            - `kw` : Keywords passed to draw_empty.
    """

    prefs = dict(globals()['prefs'])
    for key, data in kw.items():
        prefs[key] = data
    fig = Figure()
    canvas = FigureCanvasAgg( fig )
    dpi = prefs['width'] /prefs['width_inches']
    height_inches = prefs['height'] / float(dpi)
    fig.set_size_inches( prefs['width_inches'], height_inches )
    fig.set_dpi( dpi )
    fig.set_facecolor('white')
    fig.text( .5, .5, text, horizontalalignment='center' )
    if isinstance( file , StringIO.StringIO ) or type(file) == cStringIO_type:
        canvas.draw()
        size = canvas.get_renderer().get_canvas_width_height()
        buf=canvas.tostring_argb()
        im=PILImage.fromstring('RGBA', size, buf, 'raw', 'RGBA', 0, 1)
        a, r, g, b = im.split()
        im = PILImage.merge( 'RGBA', (r, g, b, a) )
        im.save( file, format = 'PNG' )
    else:
        canvas.print_figure(  file, **kw )

def find_info( attr, kw, metadata, default='' ):
    """ Helper function.  This allows me to easily find a specific
        attribute in more than one dictionary, as well as having a
        default value.

        :Parameters:
            - `attr` : Attribute name to search for; will be turned into
                       a string.
            - `kw` : A dictionary of attribute-value pairs; takes precedence.
            - `metadata` : A dictionary of attribute-value pairs; it will
                           be searched if `attr` isn't found in `kw`.
            - `default`='' : The default value to be returned.

        :Returns:
            - The correct value of `attr`.
    """
    str_attr = str(attr)
    return kw.get( str_attr, metadata.get( str_attr, default ) )

class Grapher( Cache, QueryHandler ):

    """ Thread-safe, caching grapher.  Simply call "do_graph" to
        make the graph.

        This thread-safe class is handy for web interfaces; you don't need
        to worry about generating the same graph twice.

        This is *not* the Graph class.  It is just a convenient way to wrap
        around it.
    """

    def __init__( self, *args, **kw ):
        super( Grapher, self ).__init__( *args, **kw )
        globals()['log'] = logging.getLogger("GraphTool.Graph")
        for query in self.objs:
            query.metadata['grapher'] = self
        for query in self.known_commands.values():
            query.metadata['grapher'] = self

    def get_coords( self, query, metadata, **kw ):
        """ The Graph class writes to a file-like object, as well as returns a
        dictionary containing the coordinates of the graphing object it wrote.

        This is useful in making image maps for a web interface.

        The Grapher caches both; use this function to retrieve the coordinates.

        :Parameters:
            - `query` : Name of query to look up.
            - `metadata` : The metadata for this kind of graph.
            - **`kw` : The keywords for this specific graph instance; for example,
                       may be the specific attr-value pairs the user passed through
                       the web interface.

        :Returns:
            - `cache_data` : A dictionary of coordinates, or None if there was some
                             error in generating the graph.
        """
        hash_str = self.make_hash_str( query, **kw )

        graph = self.do_graph( query, metadata, True, **kw )
        cache_data = self.check_cache( hash_str )
        if cache_data:
            return cache_data[0]
        else:
            return None

    def pre_command( self, query, *args, **kw ):
        hash_str = self.make_hash_str( query, **kw )
        results = self.check_cache( hash_str )
        if results: return results[1]

    def handle_results( self, results, metadata, *args, **kw ):
        return self.do_graph( results, metadata, **kw )

    def do_graph( self, obj, metadata, is_query=False, **kw ):
        timer = -time.time()
        if is_query: query = obj
        else: query = metadata['query']
        hash_str = self.make_hash_str( query, **kw )
        log.debug("Hash str: %s" % hash_str)
        graphing_lock = self.check_and_add_progress( hash_str )

        if graphing_lock:
            graphing_lock.acquire()
            results = self.check_cache( hash_str )[1]
            graphing_lock.release()
            log.debug("Serving graph from cache.")
            return results
        else:
            results =  self.check_cache( hash_str )
            if results:
                self.remove_progress( hash_str )
                log.debug("Serving graph from cache.")
                return results[1]
            if is_query:
                timer += time.time()
                try:
                    results, metadata = query( **kw )
                except Exception, e:
                    self.remove_progress( hash_str )
                    raise e
                timer -= time.time()
            else:
                results = obj
            if 'graph_type' in metadata:
                try:
                    graph_name = metadata['graph_type']
                    graph = self.globals[ graph_name ]
                    file = cStringIO.StringIO()
                    graph_instance = graph()
                    graph_results = graph_instance.run( results, file, metadata, **kw )
                except Exception, e:
                    self.remove_progress( hash_str )
                    st = cStringIO.StringIO()
                    traceback.print_exc( file=st )
                    raise Exception( "Error in creating graph, hash_str:%s\n%s\n%s" % \
                                     (hash_str, str(e), st.getvalue()) )
                try:
                    self.add_cache( hash_str, (graph_results, file.getvalue()) )
                except Exception, e:
                    log.exception(e)
            self.remove_progress( hash_str )
            timer += time.time()
            log.debug("Graph generated in %.2f seconds." % timer)
            log.debug("Objects in memory: %i" % len(gc.get_objects()))
            return file.getvalue()

# Some versions of matplotlib threw this warning no matter what you did; I
# suppress it here.
warnings.filterwarnings('ignore', 'integer argument expected, got float')

class Graph( object ):

    """ The base class for all the graphs.  Doesn't actually plot any data by
    itself; however, does lots of formatting with respect to the placement of
    objects on the canvas and the legend.

    The most important method for the end-user to know is `run`.  The most
    important method for the developer is `draw`.
    """

    def __init__( self, *args, **kw ):
        super( Graph, self ).__init__( *args, **kw )
        self.sorted_keys = None

    def __call__( self, *args, **kw ):
        """ For convenience, the default call of the Graph is the `run`
        function
        """
        return self.run( *args, **kw )

    def run( self, results, file, metadata, **kw ):
        """ The `run` method does all the work for generating the graph.

        :Parameters:
          - `results` : The data to be plotted inside the graph.
          - `file` : A file-like object (StringIO or File) that the graph
                     will be written to.
          - `metadata` : Metadata to generate the graph.
          - `kw` : Specific keywords to generate the graph.

        :Returns:
          - `coords` : The coordinates of the objects in the graph, if there
                       were any generated.

       ..notes: The run method executes Graph's other methods in the following
        order:
          - parse_data: Change the values in `results` for this specific graph.
          - setup: Prepare any data structures specific to the graph type.
          - prepare_canvas: Draw the background objects of the graph.
          - draw: Draw the graph objects (bars, lines, pie chart, etc)
          - write_graph: Post-draw operations, and write the graph to `file`.
          - get_coords: Generates the coordinates of the objects in the graph.
        """
        if types.DictType != type(metadata):
            raise Exception( "Wrong types; run's signature is <dict> results,"
                               "<file> file, <dict> metadata\nPassed types were"
                               " %s, %s, %s." % (type(results), type(file),
                               type(metadata)))
        self.prefs = dict(prefs)
        self.kw = kw
        self.file = file
        self.results = results
        self.metadata = metadata
        self.coords = {}
        self.parse_data( )
        self.setup( )
        if len( self.parsed_data.keys() ) > 0:
            self.prepare_canvas( )
            self.draw( )
        else:
            self.draw_empty()
        self.write_graph( )
        self.get_coords( )
        return getattr( self, 'coords', None )

    def make_bottom_text( self ):
        """
        Add text to the bottom of the graph; usually used for graph
        statistics.
        """
        return None

    def sort_keys( self, results, ignore_cache=False ):
        """
        Sort the keys in the graph.  The base Graph method just uses the
        python `sort` function on the list of the keys.
        """
        if self.sorted_keys != None and (not ignore_cache):
            return self.sorted_keys
        mykeys = list( results.keys() ); mykeys.sort()
        self.sorted_keys = mykeys
        return mykeys

    def setup(self):
        """
        The only default setting up we do is to make the labels and pick colors.
        """
        self.labels = getattr( self, 'labels', self.make_labels_common( self.parsed_data ) )
        keys = list( self.sort_keys(self.parsed_data) )
        # We reverse so the `first` colors get given to the `largest`
        # data elements.
        #keys.reverse()
        self.colors = self.preset_colors(keys)

    def make_labels_common(self, results):
        """
        Make the keys of the graph into labels.  This is usually used
        to correct spelling or add special formatting.

        In the Graph object, all the labels simply get cast into strings.
        """
        labels = []
        keys = self.sort_keys( results )
        for label in keys:
            labels.append( str(label) )
        labels.reverse()
        return labels

    def parse_data( self ):
        """
        Parse the input data into the format desired for the graph.  In the
        Graph implementation, this simply casts the data into a dictionary.
        """
        self.parsed_data = dict( self.results )

    def draw_empty( self ):
        """
        Draw an empty graph; this is called if there are no
        keys in the parsed data.
        """
        prefs = self.prefs
        fig = Figure()
        canvas = FigureCanvasAgg( fig )
        dpi = prefs['width'] /prefs['width_inches']
        height_inches = prefs['height'] / float(dpi)
        fig.set_size_inches( prefs['width_inches'], height_inches )
        fig.set_dpi( dpi )
        fig.set_facecolor('white')
        fig.text( .5, .5, "No data returned by DB query.", horizontalalignment='center' )
        self.ax = None
        self.fig = fig
        self.canvas = canvas

    # This is the list of colors that GraphTool will cycle through.  Originated
    # in a list from the PhEDEx source code; Lassi claims he got it by going
    # through the defaults of Excel.  Probably could use some attention.
    hex_colors = [ "#e66266", "#fff8a9", "#7bea81", "#8d4dff", "#ffbc71", "#a57e81",
                   "#baceac", "#00ccff", "#ccffff", "#ff99cc", "#cc99ff", "#ffcc99",
                   "#3366ff", "#33cccc" ]

    def preset_colors( self, labels ):
        """
        Determine a color for each of the labels.  This is often rewritten to
        match an application's specific color scheme.
        """
        size_labels = len( labels )
        self.color_override = self.metadata.get('color_override', {})
        try:
            if self.color_override == {}:
                raise Exception('going to the default')
            colours = self.color_override
            size_colors = len ( colours )
            retval = []
            for label in labels:
                mycolour = colours[label]
                retval.append(mycolour)
        except:
            hex_colors = self.hex_colors
            size_colors = len( hex_colors )
            retval = [ hex_colors[ i % size_colors ] for i in range( size_labels ) ]

        retval.reverse()
        return retval

    def prepare_canvas( self ):
        """
        The prepare_canvas lays out the "background" of the graph - the axis,
        the title and subtitle, the legend, and the text at the bottom of the
        graph.

        This is the "heart" of the Graph object.  Most subclasses should try
        to not touch the canvas which is prepared, in order to keep the correct
        look and feel.
        """
        self.bottom_text = self.make_bottom_text()
        title = getattr( self, 'title', self.metadata.get('title','') )
        xlabel = getattr( self, 'xlabel', self.metadata.get('xlabel','') )
        ylabel = getattr( self, 'ylabel', self.metadata.get('ylabel','') )
        labels = getattr( self, 'labels', [] )
        colors = getattr( self, 'colors', [] )
        colors = list(colors); colors.reverse()
        x_formatter_cb = getattr( self, 'x_formatter_cb', lambda x: None )
        y_formatter_cb = getattr( self, 'y_formatter_cb', lambda x: None )
        legend = getattr( self, 'legend', self.metadata.get('legend', True) )
        bottom_text = getattr( self, 'bottom_text', None )
        kw = self.kw

        if type(legend) == types.StringType and legend.lower().find('f') > -1:
            legend = False
        elif type(legend) == types.StringType:
            legend = True

        prefs = self.prefs
        if 'svg' in kw.keys():
            svg = kw['svg']
        else:
            svg = False
        if svg:
            FigureCanvas = FigureCanvasSVG
        else:
            FigureCanvas = FigureCanvasAgg

        # Change the preferences based on passed metadata *and* kw keys.
        for key in prefs.keys():
            if key in self.metadata.keys():
                my_type = type( prefs[key] )
                # bool('false') is true!  That's
                # why we have to do this override.
                if my_type == types.BooleanType:
                    if str(self.metadata[key]).lower().find('f') >= 0:
                        prefs[key] = False
                    else:
                        prefs[key] = True
                else:
                    prefs[key] = my_type(self.metadata[key])
            if key in kw.keys():
                my_type = type( prefs[key] )
                # bool('false') is true!  That's
                # why we have to do this override.
                if my_type == types.BooleanType:
                    if str(self.kw[key]).lower().find('f') >= 0:
                        prefs[key] = False
                    else:
                        prefs[key] = True
                else:
                    prefs[key] = my_type(self.kw[key])

        self.prefs = prefs
        # Alter the number of label columns, if necessary.  First,
        # calculate the max length of all the labels we are considering.
        max_length = 0
        for label in labels:
            max_length = max( len(label), max_length )

        # This is a hack to change the number of columns if the max_length
        # is very long.
        if max_length > 23:
            prefs['columns'] = min( 4, prefs['columns'] )
        if max_length > 30:
            prefs['columns'] = min( 3, prefs['columns'] )
        if max_length > 37:
            prefs['columns'] = min( 2, prefs['columns'] )

        # Figure size
        num_labels = len( labels )
        dpi = prefs['width'] / float(prefs['width_inches'])
        height_inches = prefs['height'] / dpi

        # Conversion from pixels to percentage of screen
        figure_padding_perc = prefs['figure_padding'] / float(prefs['height'])

        # Calculations for the legend
        rows = 0.0; column_height = 0.0; bottom = 0.0
        # Max number of rows in the legend
        rows = max(1,min( numpy.ceil(num_labels / float(prefs['columns'])), \
                   prefs['max_rows']) + 2*int(bottom_text != None))
        # Width and height for the legend, then converted into pixels.
        legend_width = 1 - 2 * prefs['legend_padding'] # In percent of screen.
        legend_height = (2*prefs['text_padding'] + prefs['text_size']) * \
                        rows/float(prefs['height']) # In percent of screen.
        leg_pix_height = legend_height * height_inches          * dpi
        leg_pix_width =  legend_width  * prefs['width_inches']  * dpi
        self.leg_pix_width = leg_pix_width
        self.leg_pix_height = leg_pix_height
        column_width = 1.0 / float( prefs['columns'] )
        self.column_width = column_width

        if legend:
            column_height = (2 * prefs['text_padding'] + prefs['text_size']) / \
                            leg_pix_height
            bottom = 2 * prefs['legend_padding'] + legend_height

        box_width = prefs['text_size']
        self.box_width = box_width

        # Create our figure and canvas to work with
        fig = Figure()
        canvas = FigureCanvas( fig )

        # Set the figure properties we derived above.
        fig.set_size_inches( prefs['width_inches'], height_inches )
        fig.set_dpi( dpi )

        fig.set_facecolor('white')

        # rect = (left, bottom, width, height)
        legend_rect = prefs['legend_padding'], prefs['legend_padding'], \
                      legend_width, legend_height
        self.legend_rect = legend_rect
        if prefs['square_axis']:
            min_size = min( 1 - 1.5*figure_padding_perc, 1 - bottom - \
                2*figure_padding_perc )
            ax_rect = (.5 - min_size/2.0*prefs['height']/float(prefs['width']),
                       figure_padding_perc + bottom,
                       prefs['height']/float(prefs['width'])*min_size,
                       min_size )
        else:
            ax_rect = (figure_padding_perc,
                       figure_padding_perc + bottom,
                       1 - 1.5*figure_padding_perc,
                       1 - bottom - 2*figure_padding_perc)

        # Add a watermark:
        if 'watermark' in prefs.keys() and str(prefs['watermark']) != 'False':
            watermark_filename = os.path.expandvars( os.path.expanduser( \
                                   prefs['watermark'] ) )
            if os.path.exists(watermark_filename):
                try:
                    i = PILImage.open(watermark_filename)
                    enh = PILImageEnhance.Contrast( i )
                    i = enh.enhance( .033 )
                    img_size = i.size
                    resize = 1.0
                    if prefs['width'] < img_size[0]:
                        resize = prefs['width'] / float(img_size[0])
                    if prefs['height'] < img_size[1]:
                        resize = min(resize, prefs['height']/float(img_size[1]))
                    box = (0.0, 0.0, img_size[0]/float(prefs['width'])*resize, \
                           img_size[1]/float(prefs['height'])*resize)
                    #print box
                    ax_wm = fig.add_axes( box )
                    im = ax_wm.imshow( i, origin='lower', aspect='equal' )
                    ax_wm.axis('off')
                    ax_wm.set_frame_on( False )
                    ax_wm.set_clip_on( False )
                except Exception, e:
                    print e
                    pass
            else:
                # Do nothing right now.  Write a warning sometime?
                pass

        # Create our two axes, and set properties
        ax = fig.add_axes( ax_rect )
        frame = ax.get_frame()
        frame.set_fill( False )

        # If requested, make x/y axis logarithmic
        if find_info('log_xaxis',kw,self.metadata,'False').find('r') >= 0:
            ax.semilogx()
            self.log_xaxis = True
        else:
            self.log_xaxis = False
        if find_info('log_yaxis',kw,self.metadata,'False').find('r') >= 0:
            ax.semilogy()
            self.log_yaxis = True
        else:
            self.log_yaxis = False

        setp( ax.get_xticklabels(), family=prefs['font_family'] )
        setp( ax.get_xticklabels(), fontname=prefs['font'] )
        setp( ax.get_xticklabels(), size=prefs['text_size'] )

        setp( ax.get_yticklabels(), family=prefs['font_family'] )
        setp( ax.get_yticklabels(), fontname=prefs['font'] )
        setp( ax.get_yticklabels(), size=prefs['text_size'] )

        setp( ax.get_xticklines(),  markeredgewidth=2.0 )
        setp( ax.get_yticklines(),  markeredgewidth=2.0 )
        setp( ax.get_xticklines(),  zorder=4.0 )

        if legend:
            legend_ax = fig.add_axes( legend_rect )
            legend_ax.set_axis_off()

        ax.grid( True, color='#555555', linewidth=0.1 )

        # Set text on main axes.
        # Creates a subtitle, if necessary
        title = title.split('\n',1)
        subtitle_height_pix = (prefs['subtitle_size'] + \
                               2*prefs['text_padding']) * \
                              (len(title) > 1)
        ax_height_pix = ax_rect[-1] * height_inches * dpi
        ax.title = ax.text( 0.5, 1 + (subtitle_height_pix + \
                            prefs['text_padding'])/ \
                            ax_height_pix, title[0],
                            verticalalignment='bottom', \
                            horizontalalignment='center' )
        ax.title.set_transform( ax.transAxes )
        ax.title.set_clip_box( None )
        ax._set_artist_props( ax.title )

        if len(title) > 1:
            ax.subtitle = ax.text( 0.5, 1.0 + prefs['text_padding']/\
                ax_height_pix, title[1],
                verticalalignment='bottom',
                horizontalalignment='center' )
            ax.subtitle.set_family( prefs['font_family'] )
            ax.subtitle.set_fontname( prefs['font'] )
            ax.subtitle.set_size(prefs['subtitle_size'])
            ax.subtitle.set_transform( ax.transAxes )
            ax.subtitle.set_clip_box( None )

        ax.title.set_family( prefs['font_family'] )
        ax.title.set_fontname( prefs['font'] )
        ax.title.set_weight('bold')
        ax.title.set_size( prefs['title_size'] )

        # Set labels
        t = ax.set_xlabel( xlabel )
        t.set_family(prefs['font_family'])
        t.set_fontname(prefs['font'])
        t.set_size(prefs['text_size'])

        t = ax.set_ylabel( ylabel )
        t.set_family(prefs['font_family'])
        t.set_fontname(prefs['font'])
        t.set_size(prefs['text_size'])
        # Now, make the legend.
        offset = 0
        early_stop = False; labels = list(labels)
        labels.reverse()
        zipped = zip(labels,colors); #zipped.reverse()

        # Loop over the labels.
        for my_text, my_color in zipped:
            # Size calculations
            left = (box_width+3*prefs['text_padding'])/leg_pix_width + \
                    column_width*(offset % prefs['columns'])
            top = 1 - (column_height)*(numpy.floor( offset / prefs['columns'] ))
            next_bottom = 1 - (column_height)*(numpy.floor((offset+1)/prefs['columns']) + 2*int(bottom_text != None))

            # Stop early if we ran out of room.
            if next_bottom < 0 and (num_labels - offset > 1):
                early_stop = True
                break

            # Create text
            if legend:
                t = legend_ax.text( left, top, str(my_text), horizontalalignment='left',
                                   verticalalignment='top', size=prefs['text_size'])
                t.set_fontname( prefs['font'] )
                t.set_family( prefs['font_family'] )

                # Create legend rectangle:
                patch = Rectangle( ((column_width*(offset % prefs['columns']) + \
                                1.2*prefs['text_padding']/leg_pix_width),
                                top - box_width/leg_pix_height),
                                1.2*box_width/leg_pix_width, 1.2*box_width/leg_pix_height )
                patch.set_ec('black')
                patch.set_linewidth(0.25)
                patch.set_fc( my_color )
                legend_ax.add_patch( patch )

            offset += 1

        # Set some additional text if we stopped early
        if early_stop == True:
            my_text = '... plus %i more' % (num_labels - offset)
            if legend: legend_ax.text( left, top, my_text, horizontalalignment='left',
                                       verticalalignment='top', size = prefs['text_size'] )

        top = 1 - column_height*( rows-1 )
        left = 0.5

        if bottom_text != None:
            if legend:
                t = legend_ax.text( left, top, str(bottom_text), horizontalalignment='center',
                                    verticalalignment='top', size=prefs['text_size'] )
            t.set_family( prefs['font_family'] )
            t.set_fontname( prefs['font'] )

        x_formatter_cb( ax )
        y_formatter_cb( ax )

        self.ax = ax
        self.canvas = canvas
        self.fig = fig

    def write_graph( self ):
        """
        Render the graph into the file; if the `svg` keyword is set, then
        we write out a SVG instead of a PNG.
        """

        #If we are on a logarithmic scale, set the lowest order of magnitude
        if getattr(self,'log_yaxis',False):
            self.ax.set_ylim(ymin=10**float(find_info('log_ymin',self.kw,self.metadata,-1)))

        kw = self.kw
        file = self.file
        canvas = self.canvas
        if 'svg' in kw.keys():
            svg = kw['svg']
        else:
            svg = False
        canvas.draw() # **kw )
        if svg:
            renderer = RendererSVG(prefs[width], prefs[height], file)
            canvas.figure.draw(renderer)
            renderer.finish()
        else:
            size = canvas.get_renderer().get_canvas_width_height()
            buf = canvas.tostring_argb()
            im = PILImage.fromstring('RGBA', size, buf, 'raw', 'RGBA', 0, 1)

            # We must realign the color bands, as matplotlib outputs
            # ARGB and PIL uses RGBA.
            a, r, g, b = im.split()
            im = PILImage.merge( 'RGBA', (r, g, b, a) )
            im.save( file, format = 'PNG' )

    def draw( self, **kw ):
        """
        Draw the graph.  Does nothing for the Graph object.
        """
        pass

class HorizontalGraph( Graph ):

    """
    The HorizontalGraph gives a graph where the independent variable is on the
    y-axis and the dependent variable is on the x-axis; this is switched from
    a normal graph.

    As such, there are a couple differences from the base Graph object.  The
    most significant is that the height of the graph can be adjusted based on
    the number of labels in the y-axis.  The HorizontalGraph is usually used
    for a large, discrete number of bars (such as one per site for monitoring
    graphs), as opposed to continuous time, which a Graph is better suited for.
    """

    def num_labels( self ):
        labels = getattr( self, 'labels', [] )
        num_labels = len(labels)
        return num_labels

    def prepare_canvas(self):
        """
        The HorizontalGraph reuses as much as Graph's `prepare_canvas` as
        possible.  If fixed-height is set to False, then it will change the
        height of the graph, depending on the number of labels that the
        graph has.
        """
        # Fix xlabel / ylabel as the axis is switched.
        tmp = getattr(self,'ylabel','')
        self.ylabel = getattr(self,'xlabel','')
        self.xlabel = tmp

        # First, prepare the canvas to calculate all the necessary parts.
        super( HorizontalGraph, self ).prepare_canvas()
        if self.prefs.get('fixed-height',True) == False:
            # Then, we re-calculate the heights based on number of labels.
            num_labels = self.num_labels()
            height = self.ax.get_position()[3]
            dpi = self.fig.get_dpi()
            fig_width, fig_height = self.fig.get_size_inches()
            height_pix = height * fig_height * dpi
            pixels_per_label = 2*self.prefs['text_padding'] + self.prefs['text_size']
            pixels_per_label *= self.metadata.get('pixels_per_label_multiplier', 1.0)
            new_height_pix = max(num_labels * pixels_per_label + 2*self.prefs['figure_padding'], height_pix)
            self.metadata['height'] = self.prefs['height'] + new_height_pix - height_pix + self.additional_vertical_padding()
            self.metadata['fixed-height'] = True
            # After we calculate the new height, prepare the canvas again.
            super( HorizontalGraph, self ).prepare_canvas()

    def y_formatter_cb(self, ax):
        """
        The HorizontalGraph takes the labels in the graph and creates a fixed
        locator; one tick for each of the labels
        """
        # y_vals should be the y-location of the labels.
        labels = getattr( self, 'labels', [] )
        labels = list(labels); #labels.reverse()
        y_vals =  numpy.arange(.5,len(labels)+.5,1)

        # Locations should be fixed.
        fl = FixedLocator( y_vals )
        # Make the formatter for the y-axis
        ff = FixedFormatter( labels )
        ax.yaxis.set_major_formatter( ff )
        ax.yaxis.set_major_locator( fl )

    #def x_formatter_cb(self, ax):
    #    """
    #    Set the x formatter to be the pretty one.
    #    """
    #    sf = common.PrettyScalarFormatter( )
    #    ax.xaxis.set_major_formatter( sf )

    def additional_vertical_padding(self):
        """
        Any additional vertical padding needed in the graph.
        """
        return 0

    def write_graph(self):
        """
        We render the graph twice - once to determine the current spacing,
        then possibly again to create the desired spacing.
        """
        if self.ax != None:
            # Calculate the spacing of the y-tick labels:
            labels = getattr( self, 'labels', [] )
            height_per = self.ax.get_position()[-1]
            height_inches = self.fig.get_size_inches()[-1] * height_per
            height_pixels = self.fig.get_dpi() * height_inches
            max_height_labels = height_pixels / max( 1, len(labels) )

            # Adjust the font height to match the maximum available height
            font_height = max_height_labels * 1.7 / 3.0 - 1.0
            font_height = min( font_height, self.prefs['text_size'] )
            setp( self.ax.get_yticklabels(), size=font_height )

            self.ax.yaxis.draw( self.canvas.get_renderer() )

            total_xmax = 0
            for label in self.ax.get_yticklabels():
                bbox = label.get_window_extent( self.canvas.get_renderer() )
                total_xmax = max( bbox.xmax()-bbox.xmin(), total_xmax )
                move_left = (total_xmax+6) / self.prefs['width']

            pos = self.ax.get_position()
            pos[0] = move_left
            pos[2] = 1 - pos[0] - .02
            self.ax.set_position( pos )

        # Finally, call normal writer.
        super( HorizontalGraph, self ).write_graph()

class DBGraph( Graph ):

    """
    The DBGraph is designed to be used with the database querying system
    that comes with GraphTool (it's nice, go check it out if you don't have
    one already!)

    The DBGraph knows about a few additional metadata keywords, such as
    column_names, column_units, pivot_name, and grouping_name.  It also
    keeps track of the input sql variables.
    """

    def setup( self ):
        """
        The only additional setup that DBGraph does is save the desired
        attributes to the class.
         """
        super( DBGraph, self ).setup()

        results = self.results; metadata = self.metadata
        kw = dict( self.kw )
        self.vars = metadata.get('sql_vars',{})
        self.title = getattr( self, 'title', find_info('title', kw, metadata ) )
        column_names = find_info( 'column_names', kw, metadata )
        column_units = find_info( 'column_units', kw, metadata )
        if len(str(column_units)) > 0:
            ylabel = "%s [%s]" % (column_names, column_units)
        else:
            ylabel = str(column_names)
        alt_ylabel = find_info( 'ylabel', kw, metadata )
        if alt_ylabel:
            self.ylabel = alt_ylabel
        else:
            self.ylabel = ylabel
        self.xlabel = find_info( 'grouping_name', kw, metadata )
        if len(self.xlabel) == 0:
            self.xlabel = find_info( 'xlabel', kw, metadata )
        self.kind  = find_info( 'pivot_name', kw, metadata )
        self.title = expand_string( self.title, self.vars )

class PivotGroupGraph( Graph ):

    """
    PivotGroupGraph represents the more complex of the two input
    data-types that GraphTool was originally built with.  It is for graphs
    which take dictionaries-of-dictionaries.  This means each data entry has
    two unique attribtues associated with.  The first attribute, the `pivot`,
    represents a general way the data is classified.  The second attribute,
    the `group`, is the value of the independent variable for that data entry.

    For example, if we were to produce a stacked bar graph of the number of
    events produced per site during a time period, the `pivot` would be the
    name of the site.  The `group` would be the independent variable - time.

    The PivotGroupGraph requires the dictionary-of-dictionaries format for its
    input data; it also provides a way for one to parse the data as necessary.
    """

    def num_labels( self ):
        my_groups = []
        for pivot in self.parsed_data:
            for group in self.parsed_data[pivot]:
                if group not in my_groups:
                    my_groups.append( group )
        num_labels = len(my_groups)
        return num_labels

    def sort_keys( self, results ):
        """
        Sort all the keys (the pivots) of `results` according to the max
        size of all the values stored in the pivot's dictionary.
        """
        if self.sorted_keys != None:
            return self.sorted_keys
        reverse_dict = {}
        for key, item in results.items():
            size = self.data_size( item )
            if size not in reverse_dict:
                reverse_dict[size] = [key]
            else:
                reverse_dict[size].append( key )

        sorted_dict_keys = reverse_dict.keys(); sorted_dict_keys.sort()
        sorted_dict_keys.reverse()
        sorted_keys = []
        for key in sorted_dict_keys:
            sorted_keys.extend( reverse_dict[key] )
        return sorted_keys

    def data_size( self, groups ):
        """
        Determine the max data size of the `groups` dictionary.
        Simply takes the max of all the values.
        """
        #if len(groups) == 0:
        #    return 0
        return max( groups.values() )

    def parse_pivot( self, pivot ):
        """
        Parse the pivot; for this class, this is the identity function.
        """
        return pivot

    def parse_group( self, group ):
        """
        Parses the group; for this class, simply the identity function.
        """
        return group

    def parse_datum( self, data ):
        """
        Parses the value of `data`.
        """
        return data

    def parse_data( self ):
        """
        Parse the data passed to the graph.
        """
        super( PivotGroupGraph, self ).parse_data()
        new_parsed_data = {}
        parsed_data = getattr( self, 'parsed_data', self.results )
        for pivot, groups in parsed_data.items():
            new_pivot = self.parse_pivot(pivot)
            if new_pivot == None:
                continue
            new_groups = {}
            new_parsed_data[ new_pivot ] = new_groups
            for group, data in groups.items():
                new_group = self.parse_group(group)
                new_datum = self.parse_datum(data)
                if new_group == None:
                    continue
                new_groups[ new_group ] = new_datum
            if len(new_groups) == 0:
                del new_parsed_data[new_pivot]
        self.parsed_data = new_parsed_data

class PivotGraph( Graph ):

    """ The PivotGraph is used when there is one independent variable for
    the graph, called the `pivot`.  Graphs inheriting from the PivotGraph
    expect all their data to be in a dictionary.
    """

    def sort_keys( self, results ):
        """
        Sort keys according to the max data size; this function iterates
        through all of the data in results

        :Parameters:
            - `results` : A dictionary of data to iterate through

        :Returns:
            - `sorted_keys` : Keys sorted according to maximum data size.
        """
        if self.sorted_keys != None:
            return self.sorted_keys
        reverse_dict = {}
        for key, item in results.items():
            size = self.data_size( item )
            if size not in reverse_dict:
                reverse_dict[size] = [key]
            else:
                reverse_dict[size].append( key )
        sorted_dict_keys = reverse_dict.keys(); sorted_dict_keys.sort()
        sorted_dict_keys.reverse()
        sorted_keys = []
        for key in sorted_dict_keys:
            sorted_keys.extend( reverse_dict[key] )
        return sorted_keys

    def data_size( self, item ):
        """
        Determine a numerical size for the data; this is used to
        sort the keys of the graph.

        If the item is a tuple, take the absolute value of the first entry.
        Otherwise, attempt to take the absolute value of that item.  If that
        fails, just return -1.
        """
        if type(item) == types.TupleType:
            return abs(item[0])
        try:
            return abs(item)
        except TypeError, te:
            return -1

    def parse_pivot( self, pivot ):
        """
        Parse the name of the pivot; this is the identity function.
        """
        return pivot

    def parse_datum( self, data ):
        """
        Parse the specific data value; this is the identity.
        """
        return data

    def parse_data( self ):
        """
        Parse all the data values passed to the graph.  For this super class,
        basically does nothing except loop through all the data.  A sub-class
        should override the parse_datum and parse_pivot functions rather than
        this one.
        """
        super( PivotGraph, self ).parse_data()
        new_parsed_data = {}
        parsed_data = getattr( self, 'parsed_data', self.results )
        for pivot, data in parsed_data.items():
            new_pivot = self.parse_pivot( pivot )
            data = self.parse_datum( data )
            if data != None:
                new_parsed_data[ new_pivot ] = data
        self.parsed_data = new_parsed_data

class SummarizePivotGroupGraph(PivotGroupGraph):

    def value_size(self, item):
        if type(item) == types.TupleType:
            return abs(item[0])
        try:
            return abs(item)
        except TypeError, te:
            return -1

    def add_grouping(self, old_val, new_val):
        if type(old_val) == types.TupleType:
            result = list(old_val)
            for i in range(len(result)):
                result[i] += new_val[i]
            return tuple(result)
        return old_val + new_val

    def cumulative_size(self, groups):
        cSum = 0
        for val in groups.values():
            cSum += self.value_size(val)
        return cSum

    def parse_data(self):
        super(SummarizePivotGroupGraph, self).parse_data()
        level = int(self.metadata.get('entries', 20))-1
        cSum = 0
        size_dict= {}
        for pivot, groups in self.parsed_data.items():
            s = self.cumulative_size(groups)
            size_dict[pivot] = s
            cSum += s
        vals = size_dict.values()
        vals.sort()
        if len(vals) <= level:
            min_val = 0
        else:
            min_val = vals[-level-1]
        pivots_to_smash = []
        pivots_to_keep = []
        for pivot, size in size_dict.items():
            if (size > min_val and len(pivots_to_keep) < level):
                pivots_to_keep.append(pivot)
            else:
                pivots_to_smash.append(pivot)
        #for pivot, groups in self.parsed_data.items():
        #    if cSum*level > size_dict[pivot]:
        #        pivots_to_smash.append(pivot)
        if len(pivots_to_smash) <= 1:
            return
        new_parsed_data = {}
        new_parsed_data["Other"] = {}
        other_dict = new_parsed_data["Other"]
        for pivot, groups in self.parsed_data.items():
            if pivot not in pivots_to_smash:
                new_parsed_data[pivot] = groups
            else:
                for key, val in groups.items():
                    other_dict[key] = self.add_grouping(other_dict.get(key, 0),\
                        val)
        self.parsed_data = new_parsed_data

class SummarizePivotGraph(PivotGraph):

    def value_size(self, item):
        if type(item) == types.TupleType:
            return abs(item[0])
        try:
            return abs(item)
        except TypeError, te:
            return -1

    def add_key(self, old_val, new_val):
        if type(old_val) == types.TupleType:
            result = list(old_val)
            for i in range(len(result)):
                result[i] += new_val[i]
            return tuple(result)
        return old_val + new_val

    def parse_data(self):
        super(SummarizePivotGraph, self).parse_data()
        level = int(self.metadata.get('entries', 20))-1
        cSum = 0
        size_dict= {}
        for pivot, groups in self.parsed_data.items():
            s = self.value_size(groups)
            size_dict[pivot] = s
            cSum += s
        vals = size_dict.values()
        vals.sort()
        if len(vals) <= level:
            min_val = 0
        else:
            min_val = vals[-level-1]
        pivots_to_smash = []
        pivots_to_keep = []
        for pivot, size in size_dict.items():
            if (size > min_val and len(pivots_to_keep) < level):
                pivots_to_keep.append(pivot)
            else:
                pivots_to_smash.append(pivot)
        if len(pivots_to_smash) <= 1:
            return
        new_parsed_data = {}
        new_parsed_data["Other"] = 0
        other_dict = new_parsed_data["Other"]
        for pivot, groups in self.parsed_data.items():
            if pivot not in pivots_to_smash:
                new_parsed_data[pivot] = groups
            else:
                new_parsed_data["Other"] = self.add_key(new_parsed_data. \
                       get("Other", 0), groups)
        self.parsed_data = new_parsed_data

class TimeGraph( DBGraph ):

    """
    The TimeGraph includes some sane defaults and sizes for when
    the independent variable represents time.

    The TimeGraph expects the 'starttime' keyword to represent the
    starting time of the graph, and the 'endtime' keyword to represent
    the ending time of the graph.
    """

    def __init__( self, *args, **kw ):
        """
        Initialize some strings for the TimeGraph object.
        """
        self.starttime_str = 'starttime'
        self.endtime_str = 'endtime'
        self.is_timestamps = True
        self.resize_time_graph = True
        super( TimeGraph, self ).__init__( *args, **kw )

    def parse_group( self, group ):
        """
        If this is a PivotGroupGraph, converts all the group values
        into unix timestamps.
        """
        return to_timestamp( group )

    def x_formatter_cb( self, ax ):
        """
        This function changes the x-axis according to taste.

        In this case, we set the tick locator and formatter to be
        the GraphTool-custom "PrettyDateLocator" and "PrettyDateFormatter".
        """
        ax.set_xlim( xmin=self.begin_num,xmax=self.end_num )
        dl = common.PrettyDateLocator()
        df = common.PrettyDateFormatter( dl )
        ax.xaxis.set_major_locator( dl )
        ax.xaxis.set_major_formatter( df )
        ax.xaxis.set_clip_on(False)
        sf = common.PrettyScalarFormatter( )
        ax.yaxis.set_major_formatter( sf )
        labels = ax.get_xticklabels()

    # If the graph has more than `hour_switch` minutes, we print
    # out hours in the subtitle.
    hour_switch = 7

    # If the graph has more than `day_switch` hours, we print
    # out days in the subtitle.
    day_switch = 7

    # If the graph has more than `week_switch` days, we print
    # out the weeks in the subtitle.
    week_switch = 7

    def add_time_to_title( self, title ):
        """ Given a title and two times, adds the time info to the title.
            Example results:
               "Number of Attempted Transfers\n(24 Hours from 4:45 12-14-2006 to
                5:56 12-15-2006)"

            There are two important pieces to the subtitle we add - the duration
            (i.e., '48 Hours') and the time interval (i.e., 11:00 07-02-2007 to
             11:00 07-04-2007).

            We attempt to make the duration match the size of the span (for a bar
            graph, this would be the width of the individual bar) in order for it
            to make the most sense.  The formatting of the time interval is based
            upon how much real time there is from the beginning to the end.

            We made the distinction because some would want to show graphs
            representing 168 Hours, but needed the format to show the date as
            well as the time.
        """
        begin = self.begin; end  = self.end
        if 'span' in self.metadata:
            interval = self.metadata['span']
        elif 'given_kw' in self.metadata and 'span' in self.metadata['given_kw']:
            interval = self.metadata['given_kw']['span']
        else:
            interval = self.time_interval( )
        formatting_interval = self.time_interval()
        if formatting_interval == 600:
            format_str = '%H:%M:%S'
        elif formatting_interval == 3600:
            format_str = '%Y-%m-%d %H:%M'
        elif formatting_interval == 86400:
            format_str = '%Y-%m-%d'
        elif formatting_interval == 86400*7:
            format_str = 'Week %U of %Y'

        if interval < 600:
            format_name = 'Seconds'
            time_slice = 1
        elif interval < 3600 and interval >= 600:
            format_name = 'Minutes'
            time_slice = 60
        elif interval >= 3600 and interval < 86400:
            format_name = 'Hours'
            time_slice = 3600
        elif interval >= 86400 and interval < 86400*7:
            format_name = 'Days'
            time_slice = 86400
        elif interval >= 86400*7:
            format_name = 'Weeks'
            time_slice = 86400*7
        else:
            format_str = '%x %X'
            format_name = 'Seconds'
            time_slice = 1

        begin_tuple = time.gmtime(begin); end_tuple = time.gmtime(end)
        added_title = '\n%i %s from ' % (int((end-begin)/time_slice), format_name)
        added_title += time.strftime('%s to' % format_str, begin_tuple)
        if time_slice < 86400:
            add_utc = ' UTC'
        else:
            add_utc = ''
        added_title += time.strftime(' %s%s' % (format_str, add_utc), end_tuple)
        return title + added_title

    def time_interval( self ):
        """
        Determine the appropriate time interval based upon the length of
        time as indicated by the `starttime` and `endtime` keywords.
        """
        begin = self.begin; end = self.end
        if end - begin < 600*self.hour_switch:
            return 600
        if end - begin < 86400*self.day_switch:
            return 3600
        elif end - begin < 86400*7*self.week_switch:
            return 86400
        else:
            return 86400*7

    def setup( self ):
        """
        Sets up the internal structures for the TimeGraph object.  This
        method does the following things:
            - If `croptime` is set, look at all the data to find the minimum
              and maximum time used.
            - Otherwise, use the `starttime` and `endtime` attributes to decide
              what the begin and end times are.
        """
        super( TimeGraph, self ).setup()

        if 'span' in self.metadata and isinstance(self.metadata['span'], \
                types.StringType):
            self.metadata['span'] = float(self.metadata['span'])

        vars = dict(self.vars)

        do_croptime = str(find_info('croptime', self.metadata, self.kw,False)).\
            lower().find('t') >= 0
        if do_croptime:
            begin = numpy.inf; end = 0
            for pivot, groups in self.parsed_data.items():
                for timebin, data in groups.items():
                    begin = min( to_timestamp(timebin), begin )
                    end = max( to_timestamp(timebin), end )
            end += self.metadata.get('span', 0)
        else:
            begin = to_timestamp(find_info( self.starttime_str, vars,
                                          self.metadata, time.time()-24*3600))
            end = to_timestamp(find_info(self.endtime_str,vars, self.metadata,
                                         time.time()))

        self.begin = begin; self.end = end
        self.begin_datetime = datetime.datetime.utcfromtimestamp( float(begin) )
        self.end_datetime   = datetime.datetime.utcfromtimestamp( float(end) )
        self.begin_num = date2num( self.begin_datetime )
        self.end_num   = date2num( self.end_datetime   )

        self.width = int(find_info('span', vars, self.metadata, self.time_interval() ))

        title = getattr( self, 'title', '' )
        self.title = self.add_time_to_title( title )

    def write_graph( self ):
        """ The TimeGraph object overrides the write_graph to make sure that
        the limits of the x-axis go from `starttime` to `endtime`.

        We do this as some graphing methods (bar graphs) change the x-limits
        when you create the graphs.
        """
        if (isinstance(self, PivotGroupGraph )) and self.ax != None and self.resize_time_graph:
            self.ax.set_xlim( xmin=self.begin_num, xmax=self.end_num )
        super( TimeGraph, self ).write_graph()
