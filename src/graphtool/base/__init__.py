
import os
import sys
import time
import types
import threading

try:
    import readline
except:
    pass

class GraphToolInfo(object):

  commands = {}

  default_accepts_any = False

  is_executable = False

  display_name = None

  def __init__( self, *args, **kw ):
    self.is_executable = True
    self.args = args
    self.kw = kw
    self.globals = globals()
    self.metadata = {}

  def consume_keyword( self, kw_name, args=None ):
    if args == None:
      if kw_name in self.kw.keys():
        setattr( self, kw_name, self.kw.pop( kw_name ) )
    else:
        setattr( self, kw_name, args.pop( kw_name ) )

  #def __getattr__( self, name ):
  #  print "\nDid not pass option %s!" % name
  #  print "Try adding '-%s=<some value>' to your arguments\n" % name
  #  raise AttributeError( "%s not found" % name )

  def find_classes( self, must_be_executable=True ):
    my_classes = {}
    for name in self.globals.keys():
      item = self.globals[name]
      if isinstance(item, GraphToolInfo) and (item.is_executable or not must_be_executable):
        my_classes[ name ] = item
      elif types.TypeType == type(item) and issubclass(item, GraphToolInfo) and (item.is_executable or not must_be_executable):
        if item.display_name:
          my_classes[ item.display_name ] = item
        else:
          my_classes[ name ] = item
    return my_classes

  def expand_path( self, path ):
    #return os.path.abspath( os.path.expandvars( os.path.expanduser( path ) ) )
    return os.path.expandvars( os.path.expanduser( path ) )

  def command( self, args, opts, kwargs, cmd_name = 'default' ):
    # TODO: reorganize
    try:
      function_name = self.commands[cmd_name]
    except:
      if cmd_name != "default" and (not self.default_accepts_any):
        print "Command name %s not recognized." % cmd_name
        print "Try 'phedex-info.py help <class>' for possibly more info."
        return
      elif self.default_accepts_any and ('default' in self.commands.keys()):
        function_name = self.commands['default']
        args = [cmd_name] + list(args)
      else:
        print "No default command is known for class (contact developers!)"
        print "Try 'phedex-info.py help <class>' for possibly more info."
        return
    function = getattr( self, function_name, None )
    if function == None:
      print "Command name %s mapped, but function not found, doing nothing (contact developers!)." % function_name
      return
    kw = dict( kwargs )
    for opt in opts:
      kw[opt] = True
    function( *args, **kw )
