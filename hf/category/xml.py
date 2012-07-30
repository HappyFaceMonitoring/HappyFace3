import hf, logging, traceback, os
import cherrypy as cp
from mako.template import Template

logger = logging.getLogger(__name__)

def renderXmlOverview(run, template_context):
    '''
    Create a summary of the status of all categories
    and their modules in an XML format.
    
    Useful for the HappyFace Firefox Icon or the
    HappyFace AndroidApp.
    '''
    try:
        filename = os.path.join(hf.hf_dir, hf.config.get("paths", "hf_template_dir"), "overview.xml")
        template = Template(filename=filename, lookup=hf.template_lookup)
    except Exception, e:
        logger.error("Cannot load XML overview template: %s" % str(e))
        logger.debug(traceback.format_exc())
        return u''
    cp.response.headers['Content-Type'] = "text/xml"
    template_context['protocol_host'] = cp.request.base
    return template.render(**template_context)
