from graphtool.graphs.graph import DBGraph, TimeGraph
from graphtool.graphs.common_graphs import StackedBarGraph, BarGraph, \
    CumulativeGraph, PieGraph, QualityMap, StackedLineGraph
import types

class BasicGraph( DBGraph ):
  pass
  #hex_colors = [ "#e66266", "#fff8a9", "#7bea81", "#8d4dff", "#ffbc71", "#a57e81",
  #               "#baceac", "#00ccff", "#ccffff", "#ff99cc", "#cc99ff", "#ffcc99",
  #               "#3366ff", "#33cccc" ]

  #def preset_colors( self, labels ):
  #  size_labels = len( labels )
  #  hex_colors = self.hex_colors
  #  size_colors = len( hex_colors )
  #  return [ hex_colors[ i % size_colors ] for i in range( size_labels ) ]

  #def make_labels_common( self, results ):
  #  labels = []
  #  keys = results.keys(); keys.sort()
  #  for label in keys:
  #    labels.append( str(label) )
  #  labels.reverse()
  #  return labels

  #def setup( self ):

  #  super( BasicGraph, self ).setup()

  #  kw = dict(self.kw)
  #  results = self.results
  #  self.labels = getattr( self, 'labels', self.make_labels_common( results ) )
  #  self.colors = self.preset_colors( self.labels )


class BasicStackedBar( BasicGraph, TimeGraph, StackedBarGraph ):

  pass

class BasicStackedLine(BasicGraph, TimeGraph, StackedLineGraph):
  pass

class BasicSimpleStackedBar(BasicGraph, StackedBarGraph):
    pass

class BasicBar( BasicGraph, BarGraph ):

  pass

class BasicCumulative( BasicGraph, CumulativeGraph ):

  pass

class BasicPie( BasicGraph, TimeGraph, PieGraph ):

  pass

class BasicQualityMap( BasicGraph, QualityMap ):

  pass

