import sys, os

class TimeMachineController(object):
	
    def __init__(self):

	self.output = """	
	<div class="HappyTitleBar">
	    <div class="HappyTitleBarElement"><table border="0" class="HappyTitleBarElementTable"><tr><td style="color:orange;">HappyFace Project v2</td></tr></table></div>
	    <div class="HappyTitleBarElement"><table border="0" class="HappyTitleBarElementTable"><tr><td><?php printf($time_message); ?></td></tr></table></div>
	    <div class="HappyTitleBarElement"><table border="0" class="HappyTitleBarElementTable">
	    <tr><td>
	    <form action="<?php echo $PHP_SELF; ?>" method="get">
	    <div>
		Date: <input name="date" type="text" size="12" style="text-align:center;" value="<?php echo $date_string; ?>" />
		Time: <input name="time" type="text" size="6" style="text-align:center;" value="<?php echo $time_string; ?>" />
		<input name="submit" type="submit" value="Goto" />
	    </div></form>
            </td><td>
	    <form action="<?php reset_time(); echo $PHP_SELF; ?>" method="get">
	    <div>
		 <input name="reset" type="submit" value="Now" />
	    </div>
	    </form>
	    </td><td>
	    <form action="<?php echo $PHP_SELF; ?>" method="get">
	    <div>
		 <input name="back" type="submit" value="<--" />
	    </div>
	    </form>
	    </td><td>
	    <form action="<?php echo $PHP_SELF; ?>" method="get">
	    <div>
		 <input name="fwd" type="submit" value="-->" />
	    </div>
	    </form>	   
	    </td><td>
	    <?php printf($time_error_message); ?></td></tr></table></div>
	</div>
	"""
