
import os
import sys
import logging
import logging.config

try:
    from pkg_resources import resource_filename
    has_resource = True
except:
    has_resource = False

from xml_config import XmlConfig

# Avoid the warning about no default handlers
log = logging.getLogger()
log.addHandler( logging.StreamHandler( sys.stdout ) )

class GraphToolLogging(XmlConfig):

    def __init__(self, *args, **kw):
        super(GraphToolLogging, self).__init__(*args, **kw)
        print "Started up a logging object."

    def parse_dom(self):
        super(GraphToolLogging, self).parse_dom()
        logs_dom = self.dom.getElementsByTagName("log")
        for log_dom in logs_dom:
            child_dom = log_dom.firstChild
            if child_dom.nodeType != child_dom.TEXT_NODE:
                continue
            module = log_dom.getAttribute("module")
            filename = str(child_dom.data).strip()
            if len(module) > 0 and has_resource:
                filename = resource_filename(module, filename)
            filename = os.path.expandvars(filename)
            if not os.path.exists(filename):
                print >> sys.stderr, "Error: Unable to load logging config " \
                    "file: %s." % filename
                continue
            logging.config.fileConfig(filename)
            print "Loaded logging config %s." % filename

