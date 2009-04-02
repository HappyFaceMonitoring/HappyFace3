
import os
import mimetools
import mimetypes
mimetypes.init()
mimetypes.types_map['.dwg']='image/x-dwg'
mimetypes.types_map['.ico']='image/x-icon'

import cherrypy
from graphtool.base.xml_config import XmlConfig
from graphtool.base.iterator import ObjectIterator

class WebHost( XmlConfig ):
 
  def __init__(self, *args, **kw):
      self.sub_objects = []
      super(WebHost, self).__init__(*args, **kw)
 
  def parse_dom( self ):
    super( WebHost, self ).parse_dom( )
    self.sub_objects = []
    for mount in self.dom.getElementsByTagName('mount'):
      self.parse_mount( mount )
    classes = self.globals
    for instance_dom in self.dom.getElementsByTagName('instance'):
      if not ( instance_dom in self.dom.childNodes ):
        continue
      name = instance_dom.getAttribute("name")
      location = instance_dom.getAttribute("location")
      if len(location) < 1:
          location = "/" + name
      if name == '':
          continue
      instance = classes[ name ]
      instance.metadata['base_url'] = location
      if location != '':
          cherrypy.tree.mount( instance, location )
      else:
          cherrypy.tree.mount( instance, '/' + name )
      self.sub_objects.append(instance)
    for config in self.dom.getElementsByTagName('config'):
        text = config.firstChild
        if text and text.nodeType == text.TEXT_NODE:
            filename = str(text.data).strip()
            filename =  self.expand_path( filename )
            module_name = config.getAttribute('module')
            if module_name != '':
                try:
                    pkg_resources = __import__('pkg_resources')
                except ImportError, ie:
                    raise Exception("Loading a config file from a module " \
                        "requires setuptools, which failed to import.")
                filename = pkg_resources.resource_filename(module_name, \
                    filename)
            self.load_config(filename)

  def parse_mount( self, mount_dom ):
    location = mount_dom.getAttribute('location')
    if (not location) or len(location) == 0:
      return
    content = mount_dom.getAttribute('content')
    if not (content and len(content) > 0): content = None
    classes = self.find_classes()
    for class_dom in mount_dom.getElementsByTagName('class'):
      instance = classes[class_dom.getAttribute('type')]( dom=class_dom )
    for instance_dom in mount_dom.getElementsByTagName('instance'):
      instance = classes[instance_dom.getAttribute('name')]
    self.mount_instance( instance, location, content )
    instance.metadata['base_url'] = location

  def wrap_function(self, func, content=None, security_obj=None, authtype=None,\
          access = None):
      if security_obj == None:
          def content_func( *args, **kw ):
              results = func( *args, **kw )
              if content:
                  cherrypy.response.headers['Content-Type'] = str(content) 
              return results
          return content_func
      else:
          def content_func(*args, **kw):
              assert cherrypy.request.headers.get('SSL-CLIENT-VERIFY', \
                  'Failure') == 'SUCCESS'
              dn = cherrypy.request.headers.get('SSL-CLIENT-S-DN',None)
              membership = kw.get(access, "Unknown")
              if not security_obj.authenticate(authtype, dn, membership):
                  cherrypy.response.headers["Status"] = 401
                  return "You are unauthorized to access this resource."
              results = func(*args, **kw)
              if content:
                  cherrypy.response.headers['Content-Type'] = str(content)
              return results
          return content_func


  def mount_instance( self, instance, location, content=None ):
    class DummyObject:
      _cp_config = {}
    do = DummyObject()
    security_obj_name = getattr(instance, "metadata", {}).get("security", \
        None)
    for command, func_name in instance.commands.items():
      try:
        func = getattr(instance, func_name)
        if security_obj_name:
            security_obj = self.globals[security_obj_name]
            security_authtype = instance.metadata["authtype"]
            security_access = instance.metadata["access"]
            func = self.wrap_function(func, content, security_obj, \
                security_authtype, security_access)
        else:
            func = self.wrap_function(func, content)
        setattr( do, command, func )
        func.__dict__['exposed'] = True
        #print "Adding function %s as %s" % (func_name, command)
      except Exception, e:
        raise e
    #print "Mounting instance %s at location %s" % (do, location)
    cherrypy.tree.mount( do, location )
 
  def load_config( self, file ):
    cherrypy.config.update( file )

  def kill(self):
    for instance in self.sub_objects:
        if hasattr(instance, 'kill'):
            instance.kill()
 
class StaticContent( XmlConfig ):

    _cp_config = {} 

    def index( self ):
        return "No index here!"
    index.exposed = True

    def parse_dom( self ):
        super( StaticContent, self ).parse_dom()
        for module_dom in self.dom.getElementsByTagName("module"):
            name = module_dom.getAttribute("name")
            mod_name_dom = module_dom.firstChild
            if not (mod_name_dom and \
                    mod_name_dom.nodeType == self.dom.TEXT_NODE):
                continue
            mod_name = str(mod_name_dom.data).strip()
            obj = StaticModule(mod_name)
            setattr(self, name, obj)
            getattr(self, name).exposed = True
        for directory_dom in self.dom.getElementsByTagName('directory'):
            name = directory_dom.getAttribute('name')
            location = directory_dom.getAttribute('location')
            if name == '':
                continue
            directory_name_dom = directory_dom.firstChild
            if not (directory_name_dom and \
                    directory_name_dom.nodeType == self.dom.TEXT_NODE):
                continue
            dir_name = str(directory_name_dom.data).strip()
            dir_name = self.expand_path(dir_name)
            if location != '':
                handler = cherrypy.tools.staticdir.handler(section=name, \
                    dir=dir_name, root=os.getcwd(), location=location)
            else:
                handler = cherrypy.tools.staticdir.handler(section=name, \
                    dir=dir_name, root=os.getcwd())
            setattr(handler, 'location', location)
            setattr(self, name, handler)


class StaticModule(object):
    _cp_config = {}
    exposed = True

    def __init__(self, module):
        self.module = module
        self.rs = __import__("pkg_resources").resource_stream
        self.mimetypes = __import__("mimetypes")
        self.mimetypes.types_map['.dwg']='image/x-dwg'
        self.mimetypes.types_map['.ico']='image/x-icon'

    def __call__(self, path):
        # Snippet from CherryPy
        # Set content-type based on filename extension
        ext = ""
        i = path.rfind('.')
        if i != -1:
            ext = path[i:].lower()
        content_type = self.mimetypes.types_map.get(ext, "text/plain")
        cherrypy.response.headers["Content-Type"] = content_type
        return self.rs(self.module, path).read()

class HelloWorld(object):

  static = cherrypy.tools.staticdir.handler(section='static', root=os.getcwd(),
                                     dir='static_content')

  def __init__( self, *args, **kw ): pass

  def condor( self, *args, **kw ):
    r = os.popen( 'condor_q -xml' )
    lines = r.readlines()
    xml_string = ''
    found_header = False
    for line in lines:
      if line.startswith('--'):
        found_header = True
        continue
      if found_header:
        if line.startswith('<!DOCTYPE'):
          continue
        xml_string += line 
        if line.startswith('<?xml version'):
          xml_string += '<?xml-stylesheet type="text/xsl" href="/static/content/condor_results.xsl"?>\n'
    cherrypy.response.headers['Content-Type'] = 'text/xml'
    return xml_string

  condor.exposed = True

  def index(self):
     return "Hello World! (Test Case)"
  index.exposed = True

