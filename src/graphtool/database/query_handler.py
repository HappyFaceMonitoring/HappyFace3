
import re
import types
import array
import datetime
import cStringIO

import numpy

from graphtool.base.xml_config import XmlConfig
from graphtool.base.iterator   import ObjectIterator
from graphtool.tools.common import to_timestamp

try:
    a = set()
except:
    from sets import Set as set

class QueryHandler( ObjectIterator ):

  def __init__( self, *args, **kw ):
    self.tag_name = 'queryobj'
    super( QueryHandler, self ).__init__( *args, **kw )

  def list( self, *args, **kw ):
    if len(self.known_commands.keys()) == 0:
      print "\nNo queries known!\n"
    else:
      print "Currently available queries:"
      for query_name in self.known_commands.keys():
        print " - %s" % query_name
      print ""    

def echo( *args, **kw ):
  if len(args) > 1:
    return args
  return args[0]

def make_string( *args, **kw ):
  return str(args[0])

def make_int( *args, **kw ):
  return int(args[0])

def make_float( *args, **kw ):
  return int(args[0])

def make_entry( row, cols, transform=None, row_size=None, **kw ):
  if row_size == None: row_size = len(row)
  if len(cols) > 1:
    my_entry = tuple([row[i] for i in range(row_size) if i in cols])
    if transform != None: my_entry = transform( *my_entry, **kw )
  else:
    my_entry = row[cols[0]]
    if transform != None: my_entry = transform( my_entry, **kw )
  return my_entry

def add_data( old_data, row, results_cols ):
  if len(results_cols) > 1:
    for i in range(len(results_cols)):
      if type(row[results_cols[i]]) == types.StringType:
        try:
          old_data[i] += float(row[results_cols[i]])
        except:
          old_data[i] += '\n' + row[results_cols[i]]
      elif type(row[results_cols[i]]) == array.array:
        old_data[i] += '\n' + row[results_cols[i]].tostring()
      else:
        old_data[i] += row[results_cols[i]]
  else:
    if type(row[results_cols[0]]) == types.StringType:
      try:
        old_data += float( row[results_cols[0]] )
      except: 
        old_data += '\n' + row[results_cols[0]]
    elif type(row[results_cols[0]]) == array.array:
      old_data += '\n' + row[results_cols[0]].tostring()
    else:
      new_data = row[results_cols[0]]
      if new_data == None or old_data == None:
        old_data = None
      else:
        old_data += row[results_cols[0]]
  return old_data

def new_data( row, results_cols, len_results_cols=None ):
  if len_results_cols == None: len_results_cols = len(results_cols)
  if len(results_cols) > 1:
    my_results = []
    for i in range(len_results_cols):
      if type( row[results_cols[i]] ) == array.array: my_results.append( row[results_cols[i]].tostring() )
      else:
        try:
          my_results.append( float(row[results_cols[i]]) )
        except:
          my_results.append( row[results_cols[i]] )
    return my_results
  else:
    if type( row[results_cols[0]] ) == array.array: return row[results_cols[0]].tostring()
    else:
      try:
        return float(row[results_cols[0]] )
      except:
        return row[results_cols[0]]

def check_tuple( data, num_cols ):
  if num_cols == 1:
    return data
  if num_cols > 1:
    return tuple(data)

def has_nonzero( data, num_cols ):
  if num_cols == 1 and data != 0:
    return True
  elif num_cols > 1:
    for datum in data:
      if datum != 0: return True
  return False
     
def adjust_time( mytime, **kw ):
  if 'adjust_hours' in kw.keys():
    timechange = float(kw['adjust_hours'])*3600
  else:
    timechange = 0
  timestamp = to_timestamp(mytime)
  timestamp += timechange
  #print mytime, datetime.datetime.utcfromtimestamp( timestamp )
  return datetime.datetime.utcfromtimestamp( timestamp )

def results_parser( sql_results, pivots="0,1", grouping="2", results="3", \
        pivot_transform="echo", grouping_transform="echo", globals=globals(), \
        data_transform='echo', suppress_zeros=True, **kw ): 
    metadata = {}
    pivot_cols = [int(i.strip()) for i in pivots.split(',')]
    grouping_cols = [int(i.strip()) for i in grouping.split(',')]
    results_cols = [int(i.strip()) for i in results.split(',')]
    len_results_cols = len(results_cols)
    if len(sql_results) > 0:
      row_size = len(sql_results[0])
    if callable(pivot_transform):
      pivot_transform_func = pivot_transform
    elif pivot_transform == 'echo':
      pivot_transform_func = echo
    else:
      pivot_transform_func = globals[pivot_transform.strip()]
    if callable(grouping_transform):
      grouping_transform_func = grouping_transform
    if grouping_transform == 'echo':
      grouping_transform_func = echo
    else:
      grouping_transform_func = globals[grouping_transform.strip()]
    if callable(data_transform):
        data_transform_func = data_transform
    elif data_transform == 'echo':
        data_transform_func = echo
    else:
        data_transform_func = globals[data_transform.strip()]
    parsed_results = {}
    for row in sql_results:
      my_pivot = make_entry( row, pivot_cols, pivot_transform_func, row_size, **kw )
      if my_pivot == None: continue
      my_group = make_entry( row, grouping_cols, grouping_transform_func, row_size, **kw )
      if not (my_pivot in parsed_results.keys()): parsed_results[my_pivot] = {}
      if my_group in parsed_results[my_pivot].keys():
        parsed_results[my_pivot][my_group] = add_data( parsed_results[my_pivot][my_group], row, results_cols )
      else:
        parsed_results[my_pivot][my_group] = new_data( row, results_cols, len_results_cols )

    filtered_results = {}
    metadata['kind'] = 'pivot-group'

    for pivot in parsed_results.keys():
      data = parsed_results[pivot]
      tmp_group = {}
      pivot_has_nonzero = False
      for grouping, info in data.items():
        info = check_tuple( info, len_results_cols )
        if has_nonzero( info, len_results_cols ):
          tmp_group[grouping] = info
          pivot_has_nonzero = True
      if pivot_has_nonzero:
        filtered_results[pivot] = tmp_group

    for pivot, groups in filtered_results.items():
        for group, data in groups.items():
            groups[group] = data_transform_func(data, **kw)

    return filtered_results, metadata

def histogram_parser(sql_results, results="0", globals=globals(),
                    data_transform='echo', nbins=10, **kw):
    metadata = {'kind': 'pivot'}

    if results:
        results_cols = [int(i.strip()) for i in results.split(',')]
        len_results_cols = len(results_cols)
    else:
        results_cols = None
        len_results_cols = 0
    try:
        nbins = int(nbins)
    except:
        raise ValueError("Unable to convert nbins argument into integer.")
    if nbins == 0:
        return {}, metadata
    if len_results_cols > 1:
        raise ValueError("Unable to make multi-dimension histograms!")
    if len(sql_results) > 0 and results:
        row_size = len(sql_results[0])
    else:
        row_size = None
    if callable(data_transform):
        data_transform_func = data_transform
    elif data_transform == 'echo':
        data_transform_func = echo
    else:
        data_transform_func = globals[data_transform.strip()]
    
    transformed_results = []
    if results:
        for row in sql_results:
            my_data = make_entry(row, results_cols, data_transform_func, 
                                 row_size, **kw)
            if my_data == None:
                continue
            transformed_results.append(my_data)
    else:
        for row in sql_results:
            my_data = data_transform_func(row)
            if my_data != None:
                transformed_results.append(my_data)

    if len(transformed_results) == 0:
        return {}, metadata

    count, left_edges = numpy.histogram(transformed_results, nbins)

    results = {}
    for i in range(len(left_edges)):
        results[left_edges[i]] = count[i]

    if len(left_edges) == 1:
        width = max(transformed_results) - min(transformed_results)
        if width == 0:
            width = 1
    else:
        width = left_edges[1] - left_edges[0]
    metadata['span'] = width
    
    return results, metadata

def cumulative_pivot_group_parser( sql_results, pivots="0,1", grouping="2", results="3", pivot_transform="echo", grouping_transform="echo", data_transform="echo", globals=globals(), suppress_zeros=True, **kw ):
    metadata = {}
    pivot_cols = [int(i.strip()) for i in pivots.split(',')]
    grouping_cols = [int(i.strip()) for i in grouping.split(',')]
    results_cols = [int(i.strip()) for i in results.split(',')]
    len_results_cols = len(results_cols) 
    if len(sql_results) > 0:
      row_size = len(sql_results[0])
    if callable(pivot_transform):
      pivot_transform_func = pivot_transform
    elif pivot_transform == 'echo':
      pivot_transform_func = echo
    else:
      pivot_transform_func = globals[pivot_transform.strip()]
    if grouping_transform == 'echo':
      grouping_transform_func = echo
    else:
      grouping_transform_func = globals[grouping_transform.strip()]
    if data_transform == 'echo':
      data_transform_func = echo
    else:
      data_transform_func = globals[data_transform.strip()]
    parsed_results = {}

    groups = set()
    pivots = set()

    for row in sql_results:
      my_pivot = make_entry( row, pivot_cols, pivot_transform_func, row_size, **kw )
      if my_pivot == None: continue
      my_group = make_entry( row, grouping_cols, grouping_transform_func, row_size, **kw )
      my_group = to_timestamp( my_group )
      groups.add( my_group )
      pivots.add( my_pivot )

    groups = list(groups)
    groups.sort()

    if len(groups) > 0:
      min_span = groups[-1]
      for i in range( len(groups)-1 ):
        min_span = min( groups[i+1] - groups[i], min_span )

    for row in sql_results:
      my_pivot = make_entry( row, pivot_cols, pivot_transform_func, row_size, **kw )
      if my_pivot == None: continue
      my_group = make_entry( row, grouping_cols, grouping_transform_func, row_size, **kw )
      my_group = to_timestamp( my_group )
      if not (my_pivot in parsed_results.keys()): parsed_results[my_pivot] = {}
      if my_group in parsed_results[my_pivot].keys():
        parsed_results[my_pivot][my_group] = add_data( parsed_results[my_pivot][my_group], row, results_cols )
      else:
        parsed_results[my_pivot][my_group] = new_data( row, results_cols, len_results_cols )

    filtered_results = {}
    metadata['kind'] = 'pivot-group'
    metadata['is_cumulative'] = True

    for pivot in parsed_results.keys():
      data = parsed_results[pivot]
      tmp_group = {}
      pivot_has_nonzero = False
      for grouping, info in data.items():
        info = check_tuple( info, len_results_cols )
        if has_nonzero( info, len_results_cols ):
          tmp_group[grouping] = info
          pivot_has_nonzero = True
      if pivot_has_nonzero:
        filtered_results[pivot] = tmp_group

    if len(groups) == 0:
      return filtered_results, metadata

    results = filtered_results

    filtered_results = {};

    current_group = groups.pop(0)
    csum = {}
    for pivot in results.keys():
      csum[ pivot ] = 0
      filtered_results[pivot] = {}

    def add_cumulative_data( current_group ):
      for pivot in results.keys():
        if current_group in results[pivot].keys():
          csum[ pivot ] += float(results[pivot][current_group])
        filtered_results[pivot][current_group] = csum[ pivot ]

    while len(groups) > 0:
      next_group = groups[0]
      add_cumulative_data( current_group )
      while current_group + min_span < next_group:
        current_group += min_span
        add_cumulative_data( current_group )
      current_group = groups.pop(0)
    add_cumulative_data( current_group )

    for pivot, groups in filtered_results.items():
        for group, data in groups.items():
            groups[group] = data_transform_func(data, **kw)

    return filtered_results, metadata

def pivot_group_parser_plus( sql_results, pivots="0,1", grouping="2", results="3", pivot_transform="echo", grouping_transform="echo", data_transform="echo", globals=globals(), suppress_zeros=True, **kw ):
    metadata = {}
    pivot_cols = [int(i.strip()) for i in pivots.split(',')]
    grouping_cols = [int(i.strip()) for i in grouping.split(',')]
    results_cols = [int(i.strip()) for i in results.split(',')]
    len_results_cols = len(results_cols) 
    if len(sql_results) > 0:
      row_size = len(sql_results[0])
    if callable(pivot_transform):
      pivot_transform_func = pivot_transform
    elif pivot_transform == 'echo':
      pivot_transform_func = echo
    else:
      pivot_transform_func = globals[pivot_transform.strip()]
    if grouping_transform == 'echo':
      grouping_transform_func = echo
    else:
      grouping_transform_func = globals[grouping_transform.strip()]
    if data_transform == 'echo':
      data_transform_func = echo
    else:
      data_transform_func = globals[data_transform.strip()]
    parsed_results = {}

    groups = set()
    pivots = set()

    for row in sql_results:
      my_pivot = make_entry( row, pivot_cols, pivot_transform_func, row_size, **kw )
      if my_pivot == None: continue
      my_group = make_entry( row, grouping_cols, grouping_transform_func, row_size, **kw )
      my_group = to_timestamp( my_group )
      groups.add( my_group )
      pivots.add( my_pivot )

    groups = list(groups)
    groups.sort()

    if len(groups) > 0:
      min_span = groups[-1]
      for i in range( len(groups)-1 ):
        min_span = min( groups[i+1] - groups[i], min_span )

    for row in sql_results:
      my_pivot = make_entry( row, pivot_cols, pivot_transform_func, row_size, **kw )
      if my_pivot == None: continue
      my_group = make_entry( row, grouping_cols, grouping_transform_func, row_size, **kw )
      my_group = to_timestamp( my_group )
      if not (my_pivot in parsed_results.keys()): parsed_results[my_pivot] = {}
      if my_group in parsed_results[my_pivot].keys():
        parsed_results[my_pivot][my_group] = add_data( parsed_results[my_pivot][my_group], row, results_cols )
      else:
        parsed_results[my_pivot][my_group] = new_data( row, results_cols, len_results_cols )

    filtered_results = {}
    metadata['kind'] = 'pivot-group'
    #metadata['is_cumulative'] = True

    for pivot in parsed_results.keys():
      data = parsed_results[pivot]
      tmp_group = {}
      #pivot_has_nonzero = True
      for grouping, info in data.items():
        info = check_tuple( info, len_results_cols )
        #if has_nonzero( info, len_results_cols ):
        tmp_group[grouping] = info
          #pivot_has_nonzero = True
      #if pivot_has_nonzero:
      filtered_results[pivot] = tmp_group

    if len(groups) == 0:
      return filtered_results, metadata

    results = filtered_results

    filtered_results = {};

    current_group = groups.pop(0)
    csum = {}
    for pivot in results.keys():
      csum[ pivot ] = 0
      filtered_results[pivot] = {}

    def add_cumulative_data( current_group ):
      for pivot in results.keys():
        if current_group in results[pivot].keys():
          csum[ pivot ] = float(results[pivot][current_group])
        filtered_results[pivot][current_group] = csum[ pivot ]

    while len(groups) > 0:
      next_group = groups[0]
      add_cumulative_data( current_group )
      while current_group + min_span < next_group:
        current_group += min_span
        add_cumulative_data( current_group )
      current_group = groups.pop(0)
    add_cumulative_data( current_group )

    for pivot, groups in filtered_results.items():
        for group, data in groups.items():
            groups[group] = data_transform_func(data, **kw) 

    return filtered_results, metadata

def simple_results_parser( sql_results, pivots="0", results="1", pivot_transform="echo", data_transform="echo", globals=globals(), suppress_zeros=True, **kw ): 
    pivot_cols = [int(i.strip()) for i in pivots.split(',')]
    results_cols = [int(i.strip()) for i in results.split(',')]
    len_results_cols = len(results_cols)
    if len(sql_results) > 0:
        row_size = len(sql_results[0])
    if callable(pivot_transform):
        pivot_transform_func = pivot_transform
    elif pivot_transform == 'echo':
        pivot_transform_func = echo
    else:
        pivot_transform_func = globals[pivot_transform.strip()]
    if data_transform == 'echo':
        data_transform_func = echo
    else:
        data_transform_func = globals[data_transform.strip()]
    parsed_results = {}
    for row in sql_results:
      my_pivot = make_entry( row, pivot_cols, pivot_transform_func, row_size, **kw )
      if my_pivot == None: continue
      if my_pivot in parsed_results.keys():
          parsed_results[my_pivot] = add_data( parsed_results[my_pivot], row, results_cols ) 
      else:
          parsed_results[my_pivot] = new_data( row, results_cols, len_results_cols )

    filtered_results = {}
    metadata = {}

    for pivot, info in parsed_results.items():
      info = check_tuple( info, len_results_cols )
      if has_nonzero( info, len_results_cols ):
        filtered_results[ pivot ] = data_transform_func(info, **kw)

    metadata['kind'] = 'pivot'

    return filtered_results, metadata

def complex_pivot_parser( sql_results, pivots="0", results="1", pivot_transform="echo", data_transform="echo", globals=globals(), suppress_zeros=True, **kw ):
    metadata = {}
    pivot_cols = [int(i.strip()) for i in pivots.split(',')]
    results_cols = [int(i.strip()) for i in results.split(',')]
    len_results_cols = len(results_cols)
    if len(sql_results) > 0:
      row_size = len(sql_results[0])
    if callable(pivot_transform):
      pivot_transform_func = pivot_transform
    elif pivot_transform == 'echo':
      pivot_transform_func = echo
    else:
      pivot_transform_func = globals[pivot_transform.strip()]
    if data_transform == 'echo':
      data_transform_func = echo
    else:
      data_transform_func = globals[data_transform.strip()]
    parsed_results = []
    for row in sql_results:
      my_pivot = make_entry( row, pivot_cols, pivot_transform_func, row_size, **kw )
      if my_pivot == None: continue
      parsed_results.append( (my_pivot, new_data( row, results_cols, len_results_cols )) )

    filtered_results = []

    for pivot, info in parsed_results:
      info = check_tuple( info, len_results_cols )
      if has_nonzero( info, len_results_cols ):
        filtered_results.append( (pivot,data_transform_func(info, **kw)) )

    metadata['kind'] = 'complex-pivot'

    return filtered_results, metadata

