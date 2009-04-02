import sys, os

class CategoryStatusLogic(object):

    def __init__(self):

	self.output = """
	<?php
	# $ModuleResultsArray is created before (see ModuleResultsArrayBuilder)
	# and used by the class CatStatusLogic
	# structure: [module]["status"=> ...,"mod_type"=> ...,"weight"=> ...,"category"=> ...]

	class CatStatusRating {

	    # pre-defined cat_status: -1 = noinfo
	    var $cat_status = -1;

	    # initialisation of the class (class name = function name)
	    function CatStatusRating($category, $cat_algo, $ModuleResultsArray) {

		# dynamic call of the rating algorithm function $cat_algo
		# check before if $ModuleResultsArray has data
		if ( is_array($ModuleResultsArray) ) { $this->$cat_algo($category, $ModuleResultsArray); }

	    }

	    # "worst" rating category algorithm, the worst mod_status (0.0..1.0) is the cat_status
	    function worst($category, $ModuleResultsArray) {

	        foreach ($ModuleResultsArray as $module) {

	            if ($module["category"] == $category) {

		        $mod_status = $module["status"];

			# status logic
			if ($this->cat_status == -1) { $this->cat_status = $mod_status; }
			else {
			    if ($mod_status < $this->cat_status && $mod_status >= 0) {
				$this->cat_status = $mod_status;
			    }
			}
		    }
	        }
	    }

	    # implementation of more category rating functions ($cat_algo) will follow
	    # ...

	}

	# function for the Category Status, called by the CategoryStatusSymbolLogic part
	function getCatStatus($category, $cat_algo, $ModuleResultsArray) {

	    # create instance of the class CatStatusRating
	    $cat_status_object = new CatStatusRating($category, $cat_algo, $ModuleResultsArray);

	    # return the status of the Category from the created instance
            return $cat_status_object->cat_status;
	}
	?>
	"""
