from GetData import *

#############################################
# class to donwload plots (via WGET command)
# self.url has to be defined by the inhereting module
#############################################
class Plot(GetData):

    def __init__(self, category, timestamp, archive_dir):
        GetData.__init__(self, category, timestamp, archive_dir)

        # read class config file
	config = self.readConfigFile('./happycore/Plot') # empty

        # definition of the database table keys and pre-defined values
	self.db_keys['url'] = StringCol()
	self.db_keys['filename'] = StringCol()
	
	self.db_values['url'] = ""
	self.db_values['filename'] = ""

    def run(self):

        # run the test
        success = self.getDataWget(self.url, self.archive_dir, self.__module__) # return True or False
	if success == True:
	    self.status = 1.0
	    filename = "archive/" + str(self.timestamp) + "/" + self.__module__
	else:
	    filename = ""

	# definition fo the database table values
	self.db_values['url'] = self.url.replace('&','&amp;').replace('%','%%') # the replacement ensures the XHTML validation by W3C / printf() PHP command
	self.db_values['filename'] = filename

    def output(self):

        # this module_content string will be executed by a printf('') PHP command
        # all information in the database are available via a $data["key"] call
        module_content = """
        <?php
        printf('
        <a href="' .$data["url"]. '"><img alt="" src="' .$data["filename"]. '" style="border: 0px solid;" /></a>
        ');
        ?>
        """
        
        return self.PHPOutput(module_content)
