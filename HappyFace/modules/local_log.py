from ModuleBase import *
from LogMessages import *


class local_log(LogMessages):

    def __init__(self,module_options):

        # inherits from LogMessages Class
        LogMessages.__init__(self,module_options)