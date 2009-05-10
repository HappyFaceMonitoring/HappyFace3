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
		 Date: <input name="date" type="text" size="10" style="text-align:center;" value="<?php echo $date_string; ?>" />
		 Time: <input name="time" type="text" size="4" style="text-align:center;" value="<?php echo $time_string; ?>" />
  	         <button onclick="javascript:this.submit()" onfocus="this.blur()">Goto</button>
	    </div></form>
            </td><td>
	    <form action="<?php reset_time(); echo $PHP_SELF; ?>" method="get">
	    <div>
		 <button onclick="javascript:this.submit()" onfocus="this.blur()">Now</button>
	    </div>
	    </form>
	    </td><td>
	    <form action="<?php echo $PHP_SELF; ?>" method="get">
	    <div>
  	         <button onclick="javascript:this.submit()" onfocus="this.blur()">&lt;--</button>
	    </div>
	    </form>
	    </td><td>
	    <form action="<?php echo $PHP_SELF; ?>" method="get">
	    <div>
  	         <button onclick="javascript:this.submit()" onfocus="this.blur()">--&gt;</button>
	    </div>
	    </form>	   
	    </td><td>
	    <?php printf($time_error_message); ?></td></tr></table></div>
	</div>
	"""
