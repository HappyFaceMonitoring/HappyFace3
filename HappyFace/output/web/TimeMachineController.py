import sys, os, popen2

class TimeMachineController(object):
	
    def __init__(self, logo_image):

	self.output = """	
	<div class="HappyTitleBar">
	    <div class="HappyTitleBarElement">
		<table border="0" class="HappyTitleBarElementTable">
			<tr><td>
				<img style="border:solid 1px #000;height:35px;" alt="" src='""" + logo_image + """' />
			</td></tr>
		</table>
	    </div>
	    <div class="HappyTitleBarElement">
		<table border="0" class="HappyTitleBarElementTable">
			<tr><td colspan="2" style="color:#FF9900;vertical-align:top;text-align:left;">The Happy Face</td></tr>
			<tr><td style="color:#FF9900;vertical-align:middle;text-align:left;">Project</td>
			    <td style="font-size:0.7em;color:#FFFFFF;vertical-align:middle;text-align:right;">Rev.%s</td>
			</tr>
		</table>
	    </div>
	    <div class="HappyTitleBarElement">
		<table border="0" class="HappyTitleBarElementTable">
			<tr><td><?php printf($time_message); ?></td></tr>
		</table>
	    </div>
	    <div class="HappyTitleBarElement">
		<table border="0" class="HappyTitleBarElementTable">
			<form id="HistoForm1" action="<?php echo $PHP_SELF; ?>" method="get">
			<tr><td>
	    			<div><button onclick="javascript:HappyHistoNav('back','<?php echo $timestamp; ?>')" onfocus="this.blur()">&lt;--</button></div>
			</td><td>
				<input type="text" id="HistoStep" name="s" size="5" style="text-align:center;" value="<?php echo $histo_step; ?>" />
                                <input type="hidden" id="HistoNavDate" name="date" value="<?php echo $date_string; ?>" />
                                <input type="hidden" id="HistoNavTime" name="time" value="<?php echo $time_string; ?>" />
                                <input type="hidden" id="HistoReloadTab1" name="t" value="<?php echo $selectedTab; ?>" />
                                <input type="hidden" id="HistoReloadMod1" name="m" value="<?php echo $selectedMod; ?>" />
			</td><td>
	    			<div><button onclick="javascript:HappyHistoNav('fwd','<?php echo $timestamp; ?>')" onfocus="this.blur()">--&gt;</button></div>
			</td></tr>
			</form>
		</table>
	    </div>
	    <div class="HappyTitleBarElement">
		<table border="0" class="HappyTitleBarElementTable">
			<form id="HistoForm2" action="<?php echo $PHP_SELF; ?>" method="get">
	    		<tr><td>
	    			<div>
					 <input name="date" type="text" size="10" style="text-align:center;" value="<?php echo $date_string; ?>" />
					 - <input name="time" type="text" size="5" style="text-align:center;" value="<?php echo $time_string; ?>" />
                                         <input type="hidden" id="HistoReloadTab2" name="t" value="<?php echo $selectedTab; ?>" />
                                         <input type="hidden" id="HistoReloadMod2" name="m" value="<?php echo $selectedMod; ?>" />
			  	         <button onclick="javascript:submit()" onfocus="this.blur()">Goto</button>
		  		</div>
	    		</td></tr>
			</form>
		</table>
	    </div>
	    <div class="HappyTitleBarElement">
		<table border="0" class="HappyTitleBarElementTable">
			<form action="<?php reset_time(); echo $PHP_SELF; ?>" method="get">
			<tr><td>
		    		<div>
		 			<button onclick="javascript:document.getElementById('ReloadForm').submit()" onfocus="this.blur()">Reset</button>
	    			</div>
			</td></tr>
			</form>
		</table>
	    </div>
            <?php
		if($time_error_message != "") {
			printf('
			    <div class="HappyTitleBarElement">
				<table border="0" class="HappyTitleBarElementTable">
					<tr><td>
						</div>
	    						'.$time_error_message.'
						<div>
					</td></tr>
				</table>
	    		    </div>
			');
		};
	    ?>
	</div>
	""" % popen2.popen2('svnversion %s' % "../")[0].read().strip()
