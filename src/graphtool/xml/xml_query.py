
# System imports
import threading, urllib

# GraphTool imports
from graphtool.base.xml_config import XmlConfig 
from graphtool.database.queries import Inputs

# 4Suite imports
from Ft.Xml.Xslt import Processor
from Ft.Xml import InputSource
from Ft.Lib.Uri import OsPathToUri

class XmlQueries( XmlConfig ):

  def __init__( self, *args, **kw ):
    self.commands = {}
    super( XmlQueries, self ).__init__( *args, **kw )
    
  def parse_dom( self ):
    super( XmlQueries, self ).parse_dom()
    self.name = self.dom.getAttribute('name')
    for query in self.dom.getElementsByTagName('query'):
      if query not in self.dom.childNodes: continue
      self.parse_query( query )
    
  def parse_query( self, query_dom ):
    query_class_name = query_dom.getAttribute('class')
    if query_class_name == None or len(query_class_name) == 0:
      query_class_name = 'XmlQuery'
    
    query_class = self.globals[ query_class_name ]
    
    query_obj = query_class( query_dom, self )
    
    for kw, item in self.metadata.items():
      if kw not in query_obj.metadata:
        query_obj.metadata[kw] = item

    name = query_dom.getAttribute('name')
    setattr( self, name, query_obj )
    self.commands[name] = name

  def parse_query_results( self, xml_string ):
    
    results_dom = xml.dom.minidom.parseString( xml_string )
    #metadata_dom = results_dom.getElementsByTagName('meta')
    data_dom = results_dom.getElementsByTagName('data')
    #if len( metadata_dom ) != 1:
    #  raise Exception( 'The number of <meta> tags must be 1.' )
    #else:
    #  metadata = parse_metadata( metadata_dom[0] )
    if len( data_dom ) != 1:
      raise Exception( 'The number of <data> tags must be 1.' )
    else:
      data = parse_data( data_dom[0] )
    return data

  def parse_data( self, data_dom ):
    data = []
    for row_dom in data_dom.getElementsByTagName('row'):
      row = []
      for column_dom in row_dom.getElementsByTagName('d'):
        entry = column_dom.firstChild
        if entry.nodeType == entry.TEXT_NODE:
          row.append( column )
        else: break
      data.append( row )

class XmlQuery( XmlConfig ):

  def __init__( self, query_dom, parent_obj ):
    self.queries_obj = parent_obj
    self.processor_lock = threading.Lock()
    super( XmlQuery, self ).__init__( dom=query_dom )

    
  def __call__( self, *args, **kw ):  return self.query( *args, **kw )

  def parse_dom( self ):
    super( XmlQuery, self ).parse_dom()
    query_dom = self.dom
    name = query_dom.getAttribute('name')
    if name == '': return

    target = query_dom.getElementsByTagName('target')
    xsl = query_dom.getElementByTagName('xsl')
    if len(target) > 0 and len(xsl) > 0:
      target = target[0]
      xsl = xsl[0]
    else: raise Exception("Either a URL or file for XML input must be specified")

    self.processor = Processor.Processor()
    if target.find('://') < 0:
      target = OsPathToUri(target)
    if xsl.find('://') < 0:
      xsl = OsPathToUri(xsl)

    self.target = target
    xsl_source    = InputSource.DefaultFactory.fromUri(xsl)
    self.processor.appendStylesheet(transform)

    inputs_dom = query_dom.getElementsByTagName('inputs')
    inputs_dom = [ i for i in inputs_dom if i in query_dom.childNodes ]

    results_dom = query_dom.getElementsByTagName('results')[0]
    results_inputs_dom = results_dom.getElementsByTagName('inputs')

    self.function = self.find_function( results_dom )

    inputs = Inputs( inputs_dom )

    results_inputs = Inputs( results_inputs_dom )

    self.metadata['target_url'] = target 
    self.metadata['xsl'] = xsl 
    self.metadata['inputs'] = inputs
    self.metadata['results_inputs'] = results_inputs
    parse_attributes( self.metadata, query_dom )

  def find_function( self, result_dom ):
    modname = result_dom.getAttribute('module')
    funcname = result_dom.getAttribute('function')
    if modname == '' and funcname == '':
      return None
    elif modname == '':
      function = self.globals[funcname]
    else:
      module = import_module( modname )
      try:
        function = getattr( module, funcname )
      except Exception, e:
        raise Exception( "\nCould not import %s from %s; exception follows.\n%s" % (funcname, modname, str(e)) )

    return function

  def query( self, *args, **my_kw ):
    sql_vars = self.metadata['inputs'].filter_sql( my_kw )
    vars = self.metadata['results_inputs'].filter( my_kw )
    vars = self.metadata['inputs'].filter( vars )
    url = target_url + '?' + urllib.urlencode( sql_vars )
    self.processor_lock.acquire()
    try:
      xml_string = self.processor.run( url )
    finally:
      self.processor_lock.release()
    results = self.queries_obj.parse_query_results( xml_string )
    vars['globals'] = self.globals
    results, metadata = function( results, **vars )
    for kw, val in self.metadata.items():
      if kw not in metadata: metadata[kw] = val
    metadata['query'] = self
    metadata['given_kw'] = inputs.filter( my_kw )
    metadata['sql_vars'] = sql_vars
    return results, metadata

