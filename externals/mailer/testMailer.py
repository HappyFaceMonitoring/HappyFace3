#!/usr/bin/env python
from ConfigParser import ConfigParser
import unittest
import sqlobject
import mailer

class generalTests(unittest.TestCase):
    def setUp(self):
        from os import remove, path
        self.config = ConfigParser()
        self.config.read("unittest/unittest.ini")
        mailer.dbConnect(self.config)
    
    def tearDown(self):
        pass

    def testConnection(self):
        conn = sqlobject.sqlhub.getConnection()
        print "connecting to: ",conn.uri()
        tables = ["usm_table","usm_users"]
        for table in tables:
            self.assertTrue(conn.tableExists(table),"'%s' not found"%table)
    
    def testTableClass(self):
        test = {"T2_DE_RWTH":3017.2,
                "T2_DE_DESY":0.0}
        from observed.usm import UsmUser
        self.assertTrue( UsmUser.hfAddress == "email", "hfAddress set to '%s' not 'email'"%( UsmUser.hfAddress ))
        edelhoff = UsmUser.selectBy(dirname = "edelhoff")
        for entry in  edelhoff:
            self.assertTrue( test[entry.site] == entry.du,"du mismatch found for '%s': %s != %s"%(
                entry.site, test[entry.site], entry.du ) )
            
    def testObservers(self):
        observers = mailer.makeObservers(self.config)
        for observerName, observer in observers.iteritems():         
            uri = observer._connection.uri()
            self.assertTrue( uri.endswith( self.config.get("general","stateDbURI") ) )
            observer.update()
            print "---"
            observer.update()
            
    def testGetNotifyList(self):
        from observed.usm import UsmUser
        condition = self.config.get("mail_observer:dcmsUser","condition")
        UsmUser.getNotifyList(condition)
        
if __name__ == '__main__':
    import os
    config = ConfigParser()
    config.read("unittest/unittest.ini")
    statePath = config.get("general","stateDbURI")
    if os.path.exists(statePath):
        os.remove(statePath)

    unittest.main()
    
