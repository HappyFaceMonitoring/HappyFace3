
from graphtool.database.query_handler import QueryHandler
from graphtool.tools.common import expand_string, to_timestamp
from xml.sax.saxutils import XMLGenerator
import types, cStringIO, datetime, traceback, sys

class XmlGenerator( QueryHandler ):

  XSLT_NAME='xml_results.xsl'

  def handle_results( self, results, metadata, **kw ):
    output = cStringIO.StringIO()
    gen = self.startPlot( output, results, metadata )
    kind = metadata.get('kind','Type not specified!')
    if kind == 'pivot-group':
      self.addResults_pg( results, metadata, gen )
    elif kind == 'pivot':
      self.addResults_p( results, metadata, gen )
    elif kind == 'complex-pivot':
      self.addResults_c_p( results, metadata, gen )
    else:
      raise Exception("Unknown data type! (%s)" % kind) 
    self.endPlot( gen )
    return output.getvalue()

  def handle_list( self, *args, **kw ):
    output = cStringIO.StringIO()
    gen = self.startDocument( output )
    base_url = ''
    if 'base_url' in self.__dict__:
      base_url = self.base_url
      if base_url[-1] != '/':
        base_url += '/'
    i = 0
    for query_obj in self.objs:
      i += 1
      if 'display_name' in query_obj.__dict__:
        name = query_obj.display_name
      else:
        name = "Query"
      gen.startElement("pagelist",{'name':name, 'id':str(i)})
      for page in query_obj.commands.keys():
        gen.characters("\t\t\n")
        attrs = {}
        my_page = self.known_commands[page]
        if 'title' in my_page.__dict__.keys():
          attrs['title'] = my_page.title
        gen.startElement('page',attrs)
        gen.characters( base_url + page )
        gen.endElement('page')
      gen.characters("\t\n")
      gen.endElement("pagelist")
      gen.characters("\t\n")
    self.endDocument( gen )
    return output.getvalue()

  def startDocument( self, output, encoding='UTF-8' ):
    gen =  XMLGenerator( output, encoding )
    gen.startDocument()
    try:
        static_location = '/static/content'
        static_object = self.globals['static']
        static_location = static_object.metadata.get('base_url','/static')
        static_location += '/content'
    except:
        pass
    output.write('<?xml-stylesheet type="text/xsl" href="%s/%s"?>\n' % \
        (static_location, self.XSLT_NAME) )
    output.write('<!DOCTYPE graphtool-data>\n')
    gen.startElement('graphtool',{})
    gen.characters("\n\t")
    return gen

  def startPlot( self, output, results, metadata, encoding='UTF-8' ):
    gen = self.startDocument( output, encoding )
    query_attrs = {}
    name = metadata.get('name','')
    if name and len(name) > 0:
      query_attrs['name'] = name
    gen.startElement('query', query_attrs)
    gen.characters("\n\t\t")
    title = expand_string( metadata.get('title',''), metadata.get('sql_vars','') )
    if title and len(title) > 0:
      gen.startElement('title',{})
      gen.characters( title )
      gen.endElement( 'title' )
      gen.characters("\n\t\t")
    graph_type = metadata.get('graph_type',False)
    if graph_type and len(graph_type) > 0:
      gen.startElement( 'graph',{} )
      gen.characters( graph_type )
      gen.endElement( 'graph' )
      gen.characters("\n\t\t")
    sql_string = str(metadata.get('sql',''))
    gen.startElement( 'sql',{} )
    gen.characters( sql_string )
    gen.characters("\n\t\t")
    gen.endElement( 'sql' )
    gen.characters("\n\t\t")
    self.write_sql_vars( results, metadata, gen )
    gen.characters("\n\t\t")
    base_url = None
    graphs = metadata.get('grapher',None)
    if graphs and 'base_url' in graphs.metadata:
        base_url = graphs.metadata['base_url']
    else:
      print "Base URL not specified!"
      print metadata
      if graphs:
        print graphs.metadata
      else:
        print "Graphs not specified"
      pass 
    my_base_url = self.metadata.get('base_url','')
    gen.startElement( 'attr',{'name':'base_url'} )
    gen.characters( my_base_url )
    gen.endElement( 'attr' )
    gen.characters('\n\t\t')
    try:
        static_location = '/static/content'
        static_object = self.globals['static']
        static_location = static_object.metadata.get('base_url','/static')
        static_location += '/content'
    except:
        pass
    gen.startElement( 'attr',{'name':'static_base_url'} )
    gen.characters( static_location )
    gen.endElement( 'attr' )
    gen.characters('\n\t\t')
    self.write_graph_url( results, metadata, gen, base_url=base_url )
    gen.characters('\n\t\t')
    return gen

  def write_graph_url( self, results, metadata, gen, base_url=None ):
    if base_url != None:
      base = base_url + '/' + metadata.get('name','') + '?'
      kw = metadata.get('given_kw',{})
      for key, item in kw.items():
        base += str(key) + '=' + str(item) + '&'
      gen.startElement("url",{})
      gen.characters( base )
      gen.endElement("url")

  def write_sql_vars( self, data, metadata, gen ):
    sql_vars = metadata['sql_vars']
    for key, item in metadata['given_kw'].items():
      sql_vars[key] = item
    gen.startElement( 'sqlvars', {} )
    for var in sql_vars:
      gen.characters("\n\t\t\t")
      gen.startElement('var',{'name':var})
      gen.characters( str(sql_vars[var]) )
      gen.endElement('var')
    gen.characters("\n\t\t")
    gen.endElement( 'sqlvars' )
    gen.characters("\n\t\t")

  def endPlot( self, gen ):
    gen.endElement('query')
    gen.characters("\n")
    self.endDocument( gen )

  def endDocument( self, gen ):
    gen.endElement('graphtool')
    gen.characters("\n")
    gen.endDocument()

  def write_columns( self, metadata, gen ):
    column_names = str(metadata.get('column_names',''))
    column_units = str(metadata.get('column_units',''))
    names = [ i.strip() for i in column_names.split(',') ]
    units = [ i.strip() for i in column_units.split(',') ]
    columns = {}
    num_columns = min(len(names),len(units))
    for idx in range(num_columns):
      columns[names[idx]] = units[idx]
    if len(columns.items()) > 0:
      gen.startElement('columns',{})
      i=1
      for header in names:
        gen.characters("\n\t\t\t")
        gen.startElement('column',{'unit':columns[header], 'index':str(i)})
        i += 1
        gen.characters(header)
        gen.endElement('column')
      gen.characters("\n\t\t")
      gen.endElement('columns')
      gen.characters("\n\t\t")

  def addResults_pg( self, data, metadata, gen, **kw ):

    try:
      if 'grapher' in metadata:
        coords = metadata['grapher'].get_coords( metadata['query'], metadata, **metadata['given_kw'] )
      else: coords = None
    except Exception, e: 
      print e
      traceback.print_exc( sys.stdout )
      coords = None

    attrs = {'kind':'pivot-group'}
    pivot_name = str(metadata['pivot_name'])
    if pivot_name and len(pivot_name) > 0:
      attrs['pivot'] = pivot_name
    grouping_name = str(metadata.get('grouping_name',''))
    if grouping_name and len(grouping_name) > 0:
      attrs['group'] = grouping_name
    if coords:
      attrs['coords'] = 'True'
    else:
      attrs['coords'] = 'False'
    self.write_columns( metadata, gen )
    gen.startElement('data',attrs)

    for pivot in data.keys():
      gen.characters("\n\t\t\t")
      gen.startElement( *self.pivotName( pivot, attrs ) )
      my_groups = data[pivot].keys(); my_groups.sort(); my_groups.reverse()
      for grouping in my_groups:
        gen.characters("\n\t\t\t\t")
        grouping_attrs = {}
        gen.startElement('group', self.groupingAttrs( grouping_name, grouping ) )
        if coords:
          try:
            groups = coords[pivot]
            if type(grouping) == datetime.datetime and (not (grouping in groups.keys()) ):
              kw['coords'] = groups[to_timestamp(grouping)]
            else: kw['coords'] = groups[grouping] 
          except Exception, e:
            #print "Missing coords", pivot, grouping
            #print e
            pass
        self.addData( data[pivot][grouping], gen, **kw )
        gen.endElement('group')
      gen.endElement( self.pivotName( pivot, attrs )[0] )
    gen.characters("\n\t\t")
    gen.endElement('data')
    gen.characters("\n\t")

  def addResults_p( self, data, metadata, gen, **kw ):

    coords = None
    try:
      if ('grapher' in metadata) and ('name' in metadata):
        coords = metadata['grapher'].get_coords( metadata['query'], metadata, **metadata.get('given_kw',{}) )
    except Exception, e: pass

    attrs = {'kind':'pivot'}
    pivot_name = str(metadata.get('pivot_name',''))
    if pivot_name and len(pivot_name) > 0:
      attrs['pivot'] = pivot_name
    if coords:
      attrs['coords'] = 'True'
    else:
      attrs['coords'] = 'False'

    self.write_columns( metadata, gen )
    gen.startElement('data',attrs)
    for pivot in data.keys():
      gen.characters("\n\t\t\t")
      gen.startElement( *self.pivotName(pivot, attrs) )
      if coords and (pivot in coords.keys()):
        kw['coords'] = coords[pivot]
      self.addData( data[pivot], gen, **kw )
      gen.characters("\n\t\t\t")
      gen.endElement( self.pivotName( pivot, attrs)[0] )
    gen.characters("\n\t\t")
    gen.endElement('data')
    gen.characters("\n\t")

  def addResults_c_p( self, data, metadata, gen, **kw ):
    attrs = {'kind':'pivot'}
    pivot_name = str(metadata.get('pivot_name',''))
    if pivot_name and len(pivot_name) > 0:
      attrs['pivot'] = pivot_name
    self.write_columns( metadata, gen )
    gen.startElement('data',attrs)
    for pivot, info in data:
      gen.characters("\n\t\t\t")
      gen.startElement( *self.pivotName(pivot, attrs) )
      self.addData( info, gen, **kw )
      gen.characters("\n\t\t\t")
      gen.endElement( self.pivotName( pivot, attrs)[0] )
    gen.characters("\n\t\t")
    gen.endElement('data')
    gen.characters("\n\t")    

  def groupingAttrs( self, grouping_name, grouping ):
    grouping_attrs = {}
    if grouping_name and str(grouping_name).lower()=='time':
      grouping_attrs['value'] = str(datetime.datetime.utcfromtimestamp(to_timestamp(grouping)))
    else:
      grouping_attrs['value'] = str(grouping)
    return grouping_attrs

  #TODO: make this more generic!  Built in change for Phedex link.
  def pivotName( self, pivot, attrs ):
    #if attrs['pivot'] == 'Link':
    #  return 'link', {'from':pivot[0],'to':pivot[1]}
    #else:
       return 'pivot',{'name':str(pivot)}

  def addData( self, data, gen, coords=None, **kw ):
        if type(data) != types.TupleType:
          my_data = [  data ]
        else:
          my_data = data
        if coords:
          gen.characters("\n\t\t\t\t\t")
          coords = str( coords ).replace('(','').replace(')','')
          gen.startElement( 'coords', {} )
          gen.characters( coords )
          gen.endElement( 'coords' )
        for datum in my_data:
          gen.characters("\n\t\t\t\t\t")
          gen.startElement('d',{})
          gen.characters( str(datum) )
          gen.endElement( 'd' )
        gen.characters("\n\t\t\t\t")

class XmlGeneratorAlt(XmlGenerator):

    XSLT_NAME='web_layout.xsl'

