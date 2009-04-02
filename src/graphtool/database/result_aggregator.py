
from graphtool.database.query_handler import QueryHandler, ExtDict

class ResultAggregator( QueryHandler ):

  display_name = 'result_aggregator'

  def parse_dom( self ):
    super( ResultAggregator, self ).parse_dom()
    self.known_commands = {}
    self.commands = {}
    classes = self.find_classes( must_be_executable=False )
    self.agg_sources = {}
    for agg_dom in self.dom.getElementsByTagName('aggregate'):
      agg_name = agg_dom.getAttribute('name')
      text_node = agg_dom.firstChild
      if text_node.nodeType != text_node.TEXT_NODE: continue
      text = str( text_node.data.strip() )
      agg_sources_names = [ i.strip() for i in text.split(',') ]
      self.agg_sources[agg_name] = []
      for source_name in agg_sources_names:
        class_name, method_name = source_name.split('.')
        if not (class_name in classes.keys() ): continue
        my_class = classes[class_name]
        if not (method_name in my_class.commands.keys()): continue
        my_method_name = my_class.commands[ method_name ]
        my_method = getattr( my_class, my_method_name )
        self.agg_sources[agg_name].append( my_method )
      query_obj = self.create_aggregator( agg_name )
      setattr( self, agg_name, query_obj )
      self.known_commands[agg_name] = agg_name
      self.commands[agg_name] = agg_name

  def create_aggregator( self, agg_name ):

    if len( self.agg_sources[agg_name] ) == 0:
      raise Exception( "Result aggregator %s created without any sources." % agg_name )
    #query_kind = self.agg_sources[agg_name][0].kind
    #for query in self.agg_sources[agg_name]:
    #  if query.kind != query_kind:
    #    raise Exception( "Result aggregator %s passed a queries with different result types; both %s and %s types were found." % (agg_name, query_kind, query.kind) ) 
    agg_sources = self.agg_sources[agg_name]

    def aggregated_results( *query_args, **kw ):
      results = []
      for query in agg_sources:
        results.append( query( *list(query_args), **dict(kw) ) )
      query_kind = results[0].kind
      if query_kind == 'pivot-group':
        parsed_results = {}
        for result_set in results:
          for pivot, groups in result_set.items():
            if not (pivot in parsed_results.keys()):
              parsed_results[ pivot ] = {}
            parsed_results_pivot = parsed_results[pivot]
            for group, data in groups.items():
              if not (group in parsed_results[pivot].keys()):
                parsed_results[pivot][group] = data
              else:
                parsed_results[pivot][group] += data
      elif query_kind == 'pivot':
        parsed_results = {}
        for result_set in results:
          for pivot, data in result_set.items():
            if not (pivot in parsed_results.keys()):
              parsed_results[pivot] = data
            else:
              parsed_results[pivot] += data
      final_results = ExtDict( parsed_results )
      for key, value in results[0].__dict__.items():
        setattr(final_results, key, value)
      final_results.query = aggregated_results
      return final_results
    for key, value in agg_sources[0].__dict__.items():
      setattr( aggregated_results, key, value )
    aggregated_results.self = self
    aggregated_results.name = agg_name
    return aggregated_results


