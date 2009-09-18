from ModuleBase import *

class get_started(ModuleBase):

    def __init__(self,category,timestamp,storage_dir):

        # inherits from the ModuleBase Class
        ModuleBase.__init__(self,category,timestamp,storage_dir)

        # read additional config settings
        self.answer = self.mod_config.get('setup','answer')

        # definition of the database keys and pre-defined values
        # possible format: StringCol(), IntCol(), FloatCol(), ...
        self.db_keys["message"] = StringCol()
        self.db_values["message"] = ""

       

    def run(self):

        # run the "test" ;-)
        message = self.answer + " is the answer of everything!!!"

        # define module status 0.0..1.0 or -1 for error
        self.status = 1.0 # always happy

        # define the output value for the database
        self.db_values["message"] = message

    def output(self):

        # create output sting, will be executed by a printf('') PHP command
        # all data stored in DB is available via a $data[key] call
        module_content = """
	<?php
		printf('
			<h3>' . $data["message"] . '</h3>
			<br />
			And this is the css-modified part of this message:
			<br /><br />
			<h3 class="get_startedHeader">' . $data["message"] . '</h3>
		');
	?>
	"""

        return self.PHPOutput(module_content)
