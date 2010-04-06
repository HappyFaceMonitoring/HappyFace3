<html xmlns="http://www.w3.org/1999/xhtml">
	<head>
		<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />
		<title>Happy Face Plot Generator</title>
	</head>
	<body>
		<h2><strong>Module: <?php echo $_GET["module"]?></strong></h2>
		<form action="<?php echo $PHP_SELF; ?>" method="get">

<?php
$timestamp_var = 'timestamp';
if(isset($_GET['timestamp_var']))
	$timestamp_var = $_GET['timestamp_var'];
?>

			<input type="hidden" name="module" value="<?php echo htmlentities($_GET["module"]); ?>" />
			<input type="hidden" name="subtable" value="<?php echo htmlentities($_GET["subtable"]); ?>" />
			<input type="hidden" name="variables" value="<?php echo htmlentities($_GET["variables"]); ?>" />
			<input type="hidden" name="timestamp_var" value="<?php echo htmlentities($timestamp_var); ?>" />
			<input type="hidden" name="constraint" value="<?php echo htmlentities($_GET['constraint']); ?>" />
			<input type="hidden" name="squash" value="<?php echo htmlentities($_GET['squash']); ?>" />

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
						<div><button onfocus="this.blur()">Show Plot</button></div>
					</td>
				</tr>
			</table>

<?php
if(isset($_GET['squash']) && intval($_GET['squash']) != 0)
  $variables = array($_GET['variables']);
else
  $variables = explode(',', $_GET['variables']);

foreach($variables as $variable)
{
?>
			<h3>Variable(s): <?php echo htmlentities($variable); ?></h3>
			<img alt="" border="2" src="show_plot.php?module=<?php echo htmlentities($_GET["module"]); ?>&subtable=<?php echo htmlentities($_GET["subtable"]); ?>&variables=<?php echo htmlentities($variable); ?>&date0=<?php echo htmlentities($_GET["date0"]); ?>&time0=<?php echo htmlentities($_GET["time0"]); ?>&date1=<?php echo htmlentities($_GET["date1"]); ?>&time1=<?php echo htmlentities($_GET["time1"]); ?>&timestamp_var=<?php echo htmlentities($timestamp_var); ?>&constraint=<?php echo htmlentities($_GET['constraint']); ?>" />
			<hr />

<?php
}
?>

		</form>
	</body>
</html>
