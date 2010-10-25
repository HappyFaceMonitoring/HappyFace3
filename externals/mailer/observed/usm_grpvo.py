from base import Observed
import sqlobject

class UsmGroup(Observed, sqlobject.SQLObject):
    """
    Example of user defined observed table
    
    SQLObject things:
      o table: table name to be observed
      o fromDatabase: load column definitions from database

    Additional:
      o hfAddress: name of the address column
      o getMap: retrive a map with strings to be used in the templates for mails
    """
    class sqlmeta:
        table = "usm_grpvo"
        fromDatabase = True

    #unique identifier to associate a person to a record
    hfAddress = "adminEmail"#"admin_email"

    @classmethod
    def getMap(self, selection):
        """
        build a map for use in the email template
        """
        result = {}
        for selected in selection:
            for column in self.sqlmeta.columns.keys():
                result[column] = getattr(selected, column)
            
        return result
            
