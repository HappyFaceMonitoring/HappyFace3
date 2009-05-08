import sys, os

class TimeMachineController(object):
	
    def __init__(self):

	self.output = """	
	<div class="HappyTitleBar">
	    <div class="HappyTitleBarElement"><table class="HappyTitleBarElementTable"><tr><td style="color:orange;">HappyFace Project v2a</td></tr></table></div>
	    <div class="HappyTitleBarElement"><table class="HappyTitleBarElementTable"><tr><td><?php printf($time_message); ?></td><td>
	    <form action="<?php reset_time(); echo $PHP_SELF; ?>" method="get">
	    <div>
		 <input name="reset" type="submit" value="NOW!!" />
	    </div>
	    </form>
	    </td></tr></table></div>
	    <div class="HappyTitleBarElement"><table class="HappyTitleBarElementTable"><tr><td>
	    <form action="<?php echo $PHP_SELF; ?>" method="get">
	    <div>
		Date: <input name="date" type="text" size="12" style="text-align:center;" value="<?php echo $date_string; ?>" />
		Time: <input name="time" type="text" size="6" style="text-align:center;" value="<?php echo $time_string; ?>" />
		<input name="submit" type="submit" value="Jump" />
	    </div>
	    </form>

	    </td><?php printf($time_error_message); ?></tr></table></div>
	</div>
	"""
