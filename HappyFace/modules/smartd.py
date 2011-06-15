from ModuleBase import *
from LogMessages import *

#######################################
## idea: change information source
## smartctl could be useful for this

class smartd(LogMessages):

    def __init__(self,module_options):

        # inherits from LogMessages Class
        LogMessages.__init__(self,module_options)