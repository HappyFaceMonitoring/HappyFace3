
import types, cStringIO, datetime, calendar, time, threading, datetime
from graphtool.base.xml_config import XmlConfig, import_module
from graphtool.database import DatabaseInfoV2
from graphtool.tools.common import convert_to_datetime, to_timestamp


class SqlQueries( DatabaseInfoV2 ):

  is_executable = False

  def __init__( self, *args, **kw ):
    self.commands = {}
    super( SqlQueries, self ).__init__( *args, **kw )

  def parse_dom( self ):
    super( SqlQueries, self ).parse_dom()
    self.default_query_class = self.dom.getAttribute('default_query_class')
    if self.default_query_class == None or len(self.default_query_class) == 0:
      self.default_query_class = 'SqlQuery'
    self.name = self.dom.getAttribute('name')
    for agg in self.dom.getElementsByTagName('aggregate'):
      self.parse_agg( agg )
    for query in self.dom.getElementsByTagName('query'):
      self.parse_query( query )
    for transform in self.dom.getElementsByTagName('transform'):
      self.parse_transform( transform )

  def parse_agg( self, agg_dom ):
        if agg_dom.getAttribute('all').lower() == 'true':
            self.metadata['agg'] = self.connection_manager.list_connection_names()
            return
        for conn_dom in agg_dom.getElementsByTagName('connection'):
            textNode = conn_dom.firstChild
            assert textNode.nodeType == textNode.TEXT_NODE 
            name = str(textNode.data).strip()
            if self.metadata.get('agg',None) == None:
                self.metadata['agg'] = [ name ]
            else:
                self.metadata['agg'].append( name )

  def parse_query( self, query_dom ):
    query_class_name = query_dom.getAttribute('class')
    if query_class_name == None or len(query_class_name) == 0:
      query_class_name = self.default_query_class

    query_class = globals()[ query_class_name ]

    query_obj = query_class( query_dom, self )
 
    for kw, item in self.metadata.items():
      if kw not in query_obj.metadata:
        query_obj.metadata[kw] = item

    name = query_dom.getAttribute('name')
    setattr( self, name, query_obj )
    self.commands[name] = name

class SqlQuery( XmlConfig ):

  def __init__( self, query_dom, sqlQueries ):
    self.queries_obj = sqlQueries
    super( SqlQuery, self ).__init__( dom=query_dom )
    self.__unicode__ = self.__str__

  def __call__( self, *args, **kw ):
    return self.query( *args, **kw )

  def __str__(self):
    return "Queries object:%s\nQuery %s\nSQL:%s" % (self.queries_obj.name, \
        self.metadata['name'], self.metadata['sql'])

  def parse_dom( self ):
    super( SqlQuery, self ).parse_dom()
    query_dom = self.dom
    name = query_dom.getAttribute('name')
    if name == '': return 
    base_name = query_dom.getAttribute('base')
    self.base = self.parse_base( query_dom )

    sql_dom = query_dom.getElementsByTagName('sql')[0]
    sql = Sql( dom=sql_dom, query=self )
    sql_string = str(sql)

    inputs_dom = query_dom.getElementsByTagName('inputs')
    inputs_dom = [ i for i in inputs_dom if i in query_dom.childNodes ]

    if self.base == None: 
      query = self.make_query( sql_string, inputs_dom, query_dom )
    else:
      query = self.make_query_chain( sql_string, self.base, inputs_dom, query_dom )
    self.metadata['name'] = name
    self.metadata['sql'] = sql
    self.metadata['query'] = query
    self.query = query

  def make_query_func( self, inputs, results_inputs, agg, sql_string, function ):

    def query( *args, **my_kw ):
      sql_vars = inputs.filter_sql( my_kw )
      vars = results_inputs.filter( my_kw )
      vars = inputs.filter( vars )
      class Context: pass
      ctx = Context()
      vars['query'] = ctx
      if agg == None or 'conn' in vars.keys():
        results = self.queries_obj.execute_sql( sql_string, sql_vars, **vars )
      else:
        results = []
        result_lock = threading.Lock()
        sem = threading.Semaphore( len(agg) )
        class QueryThread( threading.Thread ):
          def run( self ):
            try:
              my_results = self.sqlqueries.execute_sql( sql_string, sql_vars, conn=self.conn, **vars )
              result_lock.acquire()
              results.extend( my_results )
              result_lock.release()
              sem.release()
            except Exception, e:
              sem.release()
              raise e
        for conn in agg:
          qt = QueryThread( )
          qt.conn = conn
          qt.sqlqueries = self.queries_obj
          sem.acquire()
          qt.start()
        sem_count = 0
        while sem_count != len(agg):
          sem.acquire()
          sem_count += 1
      vars['globals'] = self.globals 
      results, metadata = function( results, **vars )
      for kw, val in self.metadata.items():
        if kw not in metadata: metadata[kw] = val 
      metadata['query'] = self 
      metadata['given_kw'] = inputs.filter( my_kw )
      metadata['sql_vars'] = sql_vars
      return results, metadata

    self.metadata['results'] = function
    self.metadata['agg'] = agg
    self.metadata['inputs'] = inputs
    return query

  def make_query_chain( self, sql_string, old_query, inputs_dom, query_dom ):
    results_dom = query_dom.getElementsByTagName('results')
    if len(results_dom)>0:
      results_inputs_dom  = results_dom[0].getElementsByTagName('inputs')
      if old_query.metadata['results_inputs'] == None:
        results_inputs = Inputs( results_inputs_dom )
      else:
        results_inputs = Inputs( results_inputs_dom, old_query.metadata['results_inputs'] )
    elif old_query.metadata['results_inputs'] == None:
      raise Exception("No inputs for results set specified!")
    else:
      results_inputs = old_query.metadata['results_inputs']

    if len(results_dom) > 0: function = self.find_function( results_dom[0] )
    else: function = None
    if function == None:
      function = old_query.metadata.get('results',None)
    if function == None:
      raise Exception( "Results parsing function not specified for chained query %s, and parent query %s doesn't specify it either." % (self.metadata.get('name',''),old_query.metadata.get('name','')))

    if self.queries_obj.metadata.get('agg',None) == None and old_query.metadata.get('agg',None) != None: agg = old_query.metadata['agg']
    else: agg = self.queries_obj.metadata.get('agg',None)

    if old_query.metadata['inputs'] == None: inputs = Inputs( inputs_dom )
    else: inputs = Inputs( inputs_dom, old_query.metadata['inputs'] )
    query = self.make_query_func( inputs, results_inputs, agg, sql_string, function )

    metadata = self.metadata
    for name, item in old_query.metadata.items():
      if name not in metadata:
        metadata[name] = item
    self.parse_attributes( self.metadata, query_dom )
    return query

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

  def make_query( self, sql_string, inputs_dom, query_dom ):
    results_dom = query_dom.getElementsByTagName('results')[0]
    results_inputs_dom = results_dom.getElementsByTagName('inputs')

    function = self.find_function( results_dom )

    inputs = Inputs( inputs_dom )

    results_inputs = Inputs( results_inputs_dom )

    agg = self.queries_obj.metadata.get('agg',None)

    query = self.make_query_func( inputs, results_inputs, agg, sql_string, function )
 
    self.metadata['results'] = function
    self.metadata['inputs'] = inputs
    self.metadata['results_inputs'] = results_inputs
    self.parse_attributes( self.metadata, query_dom )
    return query
      
  def parse_base( self, query_dom ):
    base_str = query_dom.getAttribute('base')
    if base_str == '':
      return None
    base_components = base_str.split('.')
    try:
      base = self.globals[base_components[0]]
      base_components = base_components[1:]
    except Exception, e:
      raise Exception( "Unable to find class %s\n%s" % (base_components[0], str(e)) )
    try:
      obj = base
      for comp in base_components: 
        obj = getattr( obj, comp )
    except Exception, e:
      raise Exception( "Unable to find attribute %s in %s.\n%s" % (comp, str(obj), str(e)) )
    return obj

  def parse_transform( self, transform_dom ):
    pass

  def parse_type( self, string, my_type ):
    if my_type == 'int':
      return int( string )
    elif my_type == 'float':
      return float( string )
    elif my_type == 'eval':
      return eval(str(string),{'__builtins__':None,'time':time},{})
    elif my_type == 'datetime':
      return convert_to_datetime( string )
    elif my_type == 'timestamp':
      return to_timestamp( string )
    else:
      return str( string )

class Sql( XmlConfig ):
  
  def __init__( self, *args, **kw ):
    self.pieces = []
    self.consume_keyword( 'query', kw )
    super( Sql, self ).__init__( *args, **kw )

  def fill_slot( self, slot, value ):
    for piece in self.pieces:
      if type(piece) == types.DictType and (slot in piece.keys()):
        piece[slot] = value
  
  def __str__( self ):
    strng = ""
    for piece in self.pieces:
      if type(piece) == types.StringType:
        strng += " " + piece + " "
      elif type(piece) == types.DictType:
        for key in piece.keys():
          strng += " " + str(piece[key]) + " "
    return strng

  def parse_dom( self ):
    super( Sql, self ).parse_dom()
    if self.query.base != None:
      return self.parse_chain_dom( )
    for piece in self.dom.childNodes:
      if piece.nodeType == piece.TEXT_NODE:
        self.pieces.append( str(piece.data) )
      elif piece.nodeType == piece.ELEMENT_NODE:
        if piece.tagName == 'slot':
          name = piece.getAttribute('name')
          if name == '': continue
          self.pieces.append( {name:''} )

  def parse_chain_dom( self ):
    base_query = self.query.base
    base_sql = base_query.metadata.get('sql',None)
    if base_sql == None:
      out = cStringIO.StringIO()
      print >> out, "Could not find chained object's SQL for %s" % self.dom.getAttribute('name')
      print >> out, "\n%s\n" % str(ae)
      print >> out, base_query
      raise Exception( out.getvalue() )
    if type(base_sql) != Sql:
      raise Exception("Object's SQL is not of type Sql")
    for piece in base_sql.pieces:
      if type(piece) == types.StringType:
        self.pieces.append( str(piece) )
      elif type(piece) == types.DictType:
        self.pieces.append( dict(piece) )
    for filler in self.dom.getElementsByTagName('filler'):
      name = filler.getAttribute('name')
      if name == '': continue
      value = filler.firstChild
      if value.nodeType != value.TEXT_NODE: continue
      self.fill_slot( str(name), str(value.data) )    

class Inputs( XmlConfig ):

  def __init__( self, inputs_dom, parentInputs=None ):
    super( Inputs, self ).__init__()
    self.parentInputs = parentInputs  
    self.parse( inputs_dom )

  def parse_type( self, string, my_type ):
    if my_type == 'int': 
      return int( string )
    elif my_type == 'float':
      return float( string )
    elif my_type == 'eval':
      return eval(str(string),{'__builtins__':None,'time':time},{})
    elif my_type == 'datetime':
      return convert_to_datetime( string )
    elif my_type == 'timestamp':
      return to_timestamp( string )
    elif my_type == 'bool' or my_type == 'boolean':
        if type(string) != types.StringType:
            return bool(string)
        if string.lower().strip() == 'false':
            return False
        elif string.lower().strip() == 'true':
            return True
        else:
            raise TypeError("Cannot convert string %s to boolean; valid "
                      "inputs are 'true' or 'false'." % string )
    else:
      return str( string )

  def parse( self, inputs_dom ):
    """ Parse the XML <inputs> tag. """
    inputs = {}
    inputs_types = {}
    inputs_kind = {}
    partial_up = []
    partial_down = []

    if len(inputs_dom) > 0:
      inputs_dom = inputs_dom[0]
      inputs_dom = inputs_dom.getElementsByTagName('input')

    for input in inputs_dom:
      if input.nodeType != input.ELEMENT_NODE or input.tagName != 'input':
        continue
      varname = str(input.getAttribute('name'))
      if varname == '': continue
      inputs[varname] = None
      for child in input.childNodes:
        if child.nodeType == child.TEXT_NODE:
           inputs[varname] = str(child.data).strip() 
      if varname in self.__dict__:
        inputs[varname] = getattr(self, varname)
      if input.getAttribute('type') != None and len(input.getAttribute('type')) > 0:
        inputs_types[varname] = input.getAttribute('type')
      else: 
        inputs_types[varname] = None
      if input.getAttribute('partial').lower() == 'down':
        partial_down.append(varname)
      if input.getAttribute('partial').lower() == 'up':
        partial_up.append(varname)
      input_kind = input.getAttribute('kind')
      if input_kind != None and len( input_kind ) > 0:
        inputs_kind[varname] = input_kind

    self.inputs = inputs
    self.kind = inputs_kind
    self.types = inputs_types
    self.partial_up = partial_up
    self.partial_down = partial_down

  def get_sql_kw( self ):
    inputs_kind = self.kind; inputs = self.inputs
    attr_list = [ i for i in inputs.keys() if (i in inputs_kind.keys()) and inputs_kind[i] == 'sql' ]
    if self.parentInputs != None:
      attr_list.extend( self.parentInputs.get_sql_kw() )
    return attr_list

  def filter( self, kw ):
    """ Filters the keywords, adding defaults as necessary.
        Precedence:
          1) User-given inputs.
          2) This class's defaults.
          3) Parent class's defaults.
        If sql=True, this only returns SQL variables.
    """

    kw = dict(kw)

    inputs_kind = self.kind; inputs = self.inputs 
    inputs_types = self.types
    
    attr_list = inputs.keys()
    for attr in attr_list:
      if not (attr in kw.keys()):
        kw[attr] = inputs[attr]
 
    for attr in kw.keys():
      if attr in inputs_types.keys() and inputs_types[attr] != None:
        kw[attr] = self.parse_type( kw[attr], inputs_types[attr] )

    for attr in self.partial_down:
        prev_time = kw[attr]
        assert isinstance(prev_time, datetime.datetime)
        if 'span' not in kw:
            continue
        span = kw['span']
        if span == 3600:
            kw[attr] = datetime.datetime(prev_time.year, prev_time.month,
                prev_time.day, prev_time.hour, 0, 0)
        if span >= 86400:
            kw[attr] = datetime.datetime(prev_time.year, prev_time.month, 
                prev_time.day, 0, 0, 0)

    for attr in self.partial_up:
        prev_time = kw[attr]
        assert isinstance(prev_time, datetime.datetime)
        if 'span' not in kw:
            continue
        span = kw['span']
        if span == 3600:
            kw[attr] = datetime.datetime(prev_time.year, prev_time.month, 
                prev_time.day, prev_time.hour, 59, 59)
        if span >= 86400:
            kw[attr] = datetime.datetime(prev_time.year, prev_time.month,
                prev_time.day, 23, 59, 59)

    if isinstance( self.parentInputs, Inputs ):
      kw = self.parentInputs.filter( kw )
 
    return kw   

  def filter_sql( self, kw ):
    kw = self.filter( kw )
    sql_kws = self.get_sql_kw()
    ret_kw = dict(kw)

    for key in kw.keys():
      if not (key in sql_kws):
        del ret_kw[key]

    return ret_kw


