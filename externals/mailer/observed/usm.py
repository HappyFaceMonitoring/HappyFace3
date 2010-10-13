from base import Observed
import sqlobject

class UsmUser(Observed, sqlobject.SQLObject):
    """
    Example of user defined observed table
    
    SQLObject things:
      o table: table name to be observed
      o fromDatabase: load column definitions from database

    Additional:
      o hfAddress: name of the address coumn
      o getMap: retrive a map with strings to be used in the templates for mails
    """
    class sqlmeta:
        table = "usm_users"
        fromDatabase = True

    #unique identifier to associate a person to a record
    hfAddress = "email"

    @classmethod
    def getMap(self, selection):
        """
        build a map for use in the email template
        """
        result = {}
        perSite = ["du", "sitedir","site"]
        for selected in selection:
            for column in self.sqlmeta.columns.keys():
                if column in perSite:
                    result["%s_%s"%(selected.site, column)] = getattr(selected, column)
                else:
                    if column in result and not result[column] ==  getattr(selected, column):
                        raise StandardError, "supposedly parallel rows for '%s' are out of sync: '%s' != '%s'"%(column, result[column], getattr(selected, column))
                    result[column] = getattr(selected, column)
            
        return result
            
