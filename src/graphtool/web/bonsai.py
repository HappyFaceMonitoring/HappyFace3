

from graphtool.graphs.common_graphs import PieGraph, BarGraph, StackedBarGraph, \
    CumulativeGraph, HorizontalBarGraph, QualityBarGraph, QualityMap
from graphtool.graphs.graph import TimeGraph
from graphtool.tools.cache import Cache
from xml.sax.saxutils import XMLGenerator
import urllib, types
from cherrypy import expose
try:
    import cStringIO as StringIO
except:
    import StringIO


class TimeBarGraph( TimeGraph, BarGraph ):
    pass
    
class TimeStackedBarGraph( TimeGraph, StackedBarGraph ):
    pass

# Done to make sure we don't execute arbitrary classes...
usable_classes = [PieGraph, BarGraph, StackedBarGraph, CumulativeGraph, \
                  HorizontalBarGraph, QualityBarGraph, QualityMap, TimeBarGraph, \
                  TimeStackedBarGraph]


    
    
class ImageMapWriter:
    
    def __call__(self, url, data, coords, metadata):
        file = StringIO.StringIO()
        gen = XMLGenerator( file, 'UTF-8' )
        gen.startDocument()
        gen.startElement('img', {'usemap':'#map', 'src':str(url)})
        gen.endElement('img')
        self.writeMap( gen, data, coords, metadata ) 
        gen.endDocument()
        return file.getvalue()  
        
    def writeMap(self, gen, data, coords, metadata ):
        if len(data) == 0: return
        is_pivot_group = False
        for pivot, groupings in data.items():
            if isinstance(groupings, types.DictType):
                is_pivot_group = True; break
        gen.startElement('map',{'name':'map'})
        if is_pivot_group:
            for pivot, groupings in data.items():
                # If there is no coordinates for this pivot, 
                # immediately go to the next pivot.
                if not pivot in coords:
                    continue
                groupings_coords = coords[pivot]
                for group, datum in groupings.items():
                    if not group in groupings_coords:
                        continue
                    self.writeArea(gen, datum, groupings_coords[group], pivot, metadata, group)
        else:
            for pivot, datum in data.items():
                if not pivot in coords:
                    continue
                self.writeArea(gen, datum, coords[pivot], pivot, metadata)
        #self.writeMap( gen, coords )
		gen.endElement('map')
            
        
    def writeArea(self, gen, data, data_coords, pivot, metadata, group=None):
        info = {"href":"#", "shape":"poly", "onClick":"return false;"}
        info['coords'] = str(data_coords)[1:-1].replace('(', '').replace(')','')
        pivot_name = metadata.get('pivot_name', 'Pivot')
        pivot_info = '<b>%s:</b> %s <br/>' % (pivot_name, pivot)
        if group != None:
            group_name = metadata.get('group_name', 'Grouping')
            group_info = '<b>%s:</b> %s <br/>' % (group_name, group)
        else: group_info = ''
        # Process Column Names
        column_names = metadata.get('column_names','')
        column_names_dict = {}
        # Process Column Units
        column_units_dict = {}
        # Process data
        data_info = ''
        if not isinstance( data, types.TupleType ): data = (data,)
        for i in range(len(data)):
            if i in column_names_dict: data_info += ('<b>%s: </b>' % column_names_dict[i])
            data_info += str(data[i])
            if i in column_units_dict: data_info += str(column_units_dict[i])
        
        info['onMouseOver'] = "return escape('%s %s %s');" % (pivot_info, group_info, data_info)
        gen.startElement('area',info)        
        gen.endElement('area')
    
class GraphMixIn(Cache):

    # Done to make sure we don't execute arbitrary classes or functions...
    _usable_classes = [PieGraph, BarGraph, StackedBarGraph, CumulativeGraph, \
                  HorizontalBarGraph, QualityBarGraph, QualityMap, TimeBarGraph, \
                  TimeStackedBarGraph]
    _data_generators = {}
    _graph_registry = {}
    
    def __init__(self, *args, **kw):
        super(GraphMixIn, self).__init__(args, kw)
        self.use_cache = True
        self.mounted_url = None #cant set here as controller may not be inited yet

    def getBaseUrl(self):
        """
        Find where the context is mounted
        """
        
        # if cached return
        if self.mounted_url is not None:
            return self.mounted_url
        
        temp_url = ''

        # first check command line for where server mounted
        if self.context.CmdLineArgs().opts.baseUrl:
            temp_url = "%s%s" % (temp_url, self.context.CmdLineArgs().opts.baseUrl)

        #look to see if mounted with baseUrl param to DeclaePlugin 
        if hasattr(self, 'context'):
            for plugin in self.context.PluginManager().plugins():
                if plugin.name.endswith(self.__class__.__name__) and \
                                            plugin.options.has_key('baseUrl'):
                    temp_url = "%s%s" % (temp_url, plugin.options['baseUrl'])
                    
        # set cached value and return
        self.mounted_url = temp_url
        return self.mounted_url
        
    def data_generator(self, func):
        _data_generators[func.func_name] = func
        return func
    
    def templateGraph(self, graphName, data, metadata):
        graph, coords = self._generate_graph(graphName, data, metadata)
        return graph

    def registerGraph(self, graphName, data_generator, graphClass, metadata):
        self._graph_registry[graphName] = (data_generator, graphClass, metadata)

    def lookupGraph(self, graphName):
        return self._graph_registry[graphName]

    def includeGraph(self, graphName, args={}):
        def grapher():
            data_generator, graphClass, metadata = self.lookupGraph(graphName)
            graph, coords, data = self._generate_graph(graphName, graphClass, metadata, data_generator, args)
            url = self.getBaseUrl() + '/graph/' + str(graphName) + '?' + urllib.urlencode(args)
            im = ImageMapWriter()
            output = im(url, data, coords, metadata)
            return output
        return grapher

    def graph(self, graphName, **args):
        #TODO: Wrap with better error handling
        data_generator, graphClass, metadata = self.lookupGraph(graphName)
        graph, coords, data = self._generate_graph(graphName, graphClass, metadata, data_generator, args)
        return graph
    graph = expose( graph )

    def _generate_graph(self, *args, **kw):
        if self.use_cache:
            return self.cached_function( self._generate_uncached_graph, args, kw )
        else:
            return self._generate_uncached_graph( *args, **kw )

    def _generate_uncached_graph(self, graphName, graphClass, metadata, data_generator, args):
        if graphClass in self._usable_classes:
          my_class = graphClass
        else:
          my_class = None    
        my_instance = my_class()
        data = data_generator(args)
        file = StringIO.StringIO()
        coords = my_instance( data, file, metadata )
        return file.getvalue(), coords, data
        
    def make_hash_str(self, function, args, **kwargs ):
        graphName = args[0]
        metadata = args[2]
        args = args[4]
        std_hash_str = super(GraphMixIn, self).make_hash_str(graphName, **args)
        extd_hash_str = super(GraphMixIn, self).make_hash_str(graphName, **metadata)
        return std_hash_str + extd_hash_str
        
