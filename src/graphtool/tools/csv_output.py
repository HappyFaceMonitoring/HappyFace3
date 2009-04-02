
"""
Build a CSV file from the output of a GraphTool query.

This tool has not yet been completed.
"""

import types
import cStringIO
import datetime
import traceback
import sys
import time

from graphtool.database.query_handler import QueryHandler
from graphtool.tools.common import expand_string, to_timestamp, \
    convert_to_datetime

class CsvGenerator(QueryHandler):

    def handle_results( self, results, metadata, **kw ):
        output = cStringIO.StringIO()
        kind = metadata.get('kind','Type not specified!')
        if kind == 'pivot-group':
            self.addResults_pg(results, metadata, output)
        elif kind == 'pivot':
            self.addResults_p(results, metadata, output)
        elif kind == 'complex-pivot':
            self.addResults_c_p(results, metadata, output)
        else:
            raise Exception("Unknown data type! (%s)" % kind) 
        return output.getvalue()

    def addResults_pg( self, data, metadata, gen, **kw ):
      gen.write(metadata.get('pivot_name', 'Unknown Pivot') + ',')
      gen.write(metadata.get('grouping_name', 'Unknown Grouping') + ',')
      gen.write(metadata.get('column_names') + '\n')
      convert_to_time = metadata.get('grouping_name', 'False').lower() == 'time'
      print metadata['grouping_name'], convert_to_time
      for pivot in data.keys():
          my_groups = data[pivot].keys(); my_groups.sort(); my_groups.reverse()
          for grouping in my_groups:
              if convert_to_time:
                  my_group = convert_to_datetime(grouping).strftime('%x %X')
              else:
                  my_group = str(grouping)
              gen.write(str(pivot) + "," + str(my_group) + ",")
              self.addData( data[pivot][grouping], gen, **kw )
              gen.write("\n")

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

    def groupingVal(self, grouping_name, grouping):
        grouping_attrs = {}
        if grouping_name and str(grouping_name).lower()=='time':
          grouping_attrs['value'] = str(datetime.datetime.utcfromtimestamp(to_timestamp(grouping)))
        else:
          grouping_attrs['value'] = str(grouping)
        return grouping_attrs

    def addData( self, data, gen, coords=None, **kw ):
        if type(data) != types.TupleType:
          my_data = [  data ]
        else:
          my_data = data
        gen.write(','.join([str(i) for i in my_data]))
