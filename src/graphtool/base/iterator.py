
from graphtool.base.xml_config import XmlConfig
import sys, cStringIO


#TODO: Test Mylar

class ObjectIterator( XmlConfig ):

  commands = { 'default' : 'run',
               'run' : 'run',
               'list' : 'list' }

  is_executable = False

  default_accepts_any = True

  def __init__( self, *args, **kw ):
    self.known_commands = {}
    self.tag_name = self.__dict__.get('tag_name','obj')
    super( ObjectIterator, self ).__init__( *args, **kw )  

  def parse_dom( self ):
    super( ObjectIterator, self ).parse_dom()
    classes = self.find_classes( must_be_executable=False )
    self.objs = []
    for obj_dom in self.dom.getElementsByTagName(self.tag_name):
      text_node = obj_dom.firstChild
      if text_node.nodeType != text_node.TEXT_NODE: continue
      text = str( text_node.data.strip() )
      if not (text in classes.keys()):
        continue
      obj = classes[text]
      self.objs.append( obj )
      if isinstance( obj, ObjectIterator ):
        command_dict = obj.known_commands
      else:
        command_dict = obj.commands
      for query, method_name in command_dict.items():
        self.known_commands[query] = getattr(obj, method_name )


  def handle_results( self, results, metadata, **kw ):
    return results, metadata

  def handle_args( self, *args, **kw ):
    return args, kw

  def handle_list( self, *args, **kw ):
    return self.list( *args, **kw )

  def pre_command( self, query, *args, **kw ):
    pass

  def run( self, *args, **kw ):
    if len(args) == 0:
      return self.handle_list( *args, **kw )
    cmd_args = args[1:]
    cmd_name = args[0]
    if cmd_name in self.known_commands.keys():
      cmd_func = self.known_commands[ cmd_name ]
    else:
      self.handle_list( *args, **kw )
      raise Exception( "Command name %s not known" % cmd_name )
    cmd_args, kw = self.handle_args( *cmd_args, **kw )
    pre_results = self.pre_command( cmd_func, *cmd_args, **kw )
    if pre_results:
      return pre_results
    results, metadata = cmd_func( *cmd_args, **kw )
    return self.handle_results( results, metadata, **kw )

  def list( self, *args, **kw ):
    out = cStringIO.StringIO()
    if len(self.known_commands.keys()) == 0:
      print >> out, "\nNo queries known!\n"
    else:
      print >> out, "Currently available queries:"
      for query_name in self.known_commands.keys():
        print >> out, " - %s" % query_name
      print >> out, ""
    return out.getvalue()


