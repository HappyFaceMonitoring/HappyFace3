#import sqlobject
class Observed:
    """
    Base calss for observe tables.
    
    Implements:
      o definition of the observedAddress Property
      o ...
      
    Dervide calsses have to set
      o hfAddress to the name of the mail address column of the observed
        table
    """
    hfAddress = None

    @property
    def observedAddress(self):
        """
        get the address of an observed row.
        """
        return getattr(self, self.hfAddress)

    @classmethod
    def getNotifyList(self, selection, initTime = 0):
        """
        get a dict which maps the address to a SelectResult for
          o the last occurance of a match to the configured condition
            AND no later entry which does not match the condition
        """
        import sqlobject
        from time import time
        if initTime > time():
            print "ERROR: initTime '%s' after actual time '%s'"%(initTime, time())
            raise StandardError, "initTime '%s' after actual time '%s'"%(initTime, time())
        selectionVariables = {
            "NOT": sqlobject.NOT,
            "AND": sqlobject.AND,
            "OR": sqlobject.OR,
            }
        for columnName in self.sqlmeta.columns:
            selectionVariables[columnName] = getattr(self.q, columnName)
        #TODO: add class properties/variables too
        onNotice = {}
        checked = []
        selResult = self.select(eval(selection, selectionVariables))
        notSelResult = self.select(eval("NOT(%s)"%selection, selectionVariables))
        for observed in selResult:
            address = observed.observedAddress
            if not address in checked:
                lastNot = notSelResult.filter( sqlobject.AND( getattr(self.q, self.hfAddress) == address, self.q.timestamp > initTime ) ).max("timestamp")
                if lastNot == None:
                    lastNot = initTime
                first = selResult.filter( sqlobject.AND( getattr(self.q, self.hfAddress) == address, self.q.timestamp > lastNot ) ).min("timestamp")
                #print address, timedist, "last:",last, "lastNot:",lastNot
                checked.append(address)
                if not first == None:
                    onNotice[observed.observedAddress] = selResult.filter(
                        sqlobject.AND( getattr(self.q, self.hfAddress) == address,
                                       self.q.timestamp == first
                                      )
                        )
        return onNotice
