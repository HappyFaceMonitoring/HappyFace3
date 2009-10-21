<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />
<title>Happy Face Plot Generator </title>
</head>
<body>
<h2><strong>Module: <?php echo $_GET["module"]?></strong></h2>
<h3>Variable: <?php echo $_GET["variable"]?></h3>
<form action="<?php echo $PHP_SELF; ?>" method="get">
<table>
	<tr>
	<td>
		Start:
	</td>
	<td>
		<input name="date0" type="text" size="10" style="text-align:center;" value="<?php echo $_GET["date0"]?>" />
		<input name="time0" type="text" size="5" style="text-align:center;" value="<?php echo $_GET["time0"]?>" />
	</td>
	<td>
		End:
	</td>
	<td>
		<input name="date1" type="text" size="10" style="text-align:center;" value="<?php echo $_GET["date1"]?>" />
		<input name="time1" type="text" size="5" style="text-align:center;" value="<?php echo $_GET["time1"]?>" />
	</td>
	<td>
		<input type="hidden" name="module" value="<?php echo $_GET["module"]?>" />
		<input type="hidden" name="variable" value="<?php echo $_GET["variable"]?>" />
		<div><button onclick="javascript: submitform()" onfocus="this.blur()">Show Plot</button></div>
	</td>
	</tr>
</table>
</form>
<img alt="" border="2" src="show_plot.php?module=<?php echo $_GET["module"]; ?>&variable=<?php echo $_GET["variable"]; ?>&date0=<?php echo $_GET["date0"]; ?>&time0=<?php echo $_GET["time0"]; ?>&date1=<?php echo $_GET["date1"]; ?>&time1=<?php echo $_GET["time1"]; ?>" />
</body>
</html>