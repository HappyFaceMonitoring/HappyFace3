# this is a singleton class, which will be created only once

import thread

class DataBaseLock(object):
    def __new__(type, *args):

        if not '_the_instance' in type.__dict__:
            type._the_instance = object.__new__(type)
        return type._the_instance

    def __init__(self):
        if not '_ready' in dir(self):
	    self.lock = thread.allocate_lock()
            self._ready = True


