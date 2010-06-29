<html xmlns="http://www.w3.org/1999/xhtml">
	<head>
		<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />
		<title>Happy Face Plot Generator</title>
	</head>
	<body>
		<h2><strong>Module: <?php echo $_GET["module"]?></strong></h2>
		<form action="<?php echo $PHP_SELF; ?>" method="get">

<?php

include('plot_common.php');

// Quick'n'dirty check to avoid SQL injection attacks on column names.
// Unfortunately preparated statements do not work on table or column names
// with SQLite.
// TODO: Avoid code duplication with show_plot.php
function verify_column_name($name)
{
  for($i = 0; $i < count($name); ++$i)
    if(!ctype_alnum($name[$i]) && $name[$i] != '_')
      { echo "Invalid column name: $name"; die; }
  return $name;
}

$timestamp_var = 'timestamp';
if(isset($_GET['timestamp_var']))
	$timestamp_var = verify_column_name($_GET['timestamp_var']);
?>

			<input type="hidden" name="module" value="<?php echo htmlentities($_GET["module"]); ?>" />
			<input type="hidden" name="subtable" value="<?php echo htmlentities($_GET["subtable"]); ?>" />
			<input type="hidden" name="variables" value="<?php echo htmlentities($_GET["variables"]); ?>" />
			<input type="hidden" name="timestamp_var" value="<?php echo htmlentities($timestamp_var); ?>" />
			<input type="hidden" name="constraint" value="<?php echo htmlentities($_GET['constraint']); ?>" />
			<input type="hidden" name="squash" value="<?php echo htmlentities($_GET['squash']); ?>" />
			<input type="hidden" name="renormalize" value="<?php echo htmlentities($_GET['renormalize']); ?>" />

			<table>
				<tr>
					<td>
						Start:
					</td>
					<td>
						<input name="date0" type="text" size="10" style="text-align:center;" value="<?php echo strftime('%Y-%m-%d', $timestamp0); ?>" />
						<input name="time0" type="text" size="5" style="text-align:center;" value="<?php echo strftime('%H:%M', $timestamp0); ?>" />
					</td>
					<td>
						End:
					</td>
					<td>
						<input name="date1" type="text" size="10" style="text-align:center;" value="<?php echo strftime('%Y-%m-%d', $timestamp1); ?>" />
						<input name="time1" type="text" size="5" style="text-align:center;" value="<?php echo strftime('%H:%M', $timestamp1); ?>" />
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
			<h3>Variable(s): <?php echo htmlentities(implode(', ', explode(',', $variable))); ?></h3>
<?php
if(isset($_GET['renormalize']) && intval($_GET['renormalize']) != 0)
	echo '<p><strong>Trend Plot:</strong> Note that individual variables have been scaled so that they fit into [0,1] on this plot.</p>';
?>
			<p><img alt="" border="2" src="show_plot.php?module=<?php echo htmlentities($_GET["module"]); ?>&subtable=<?php echo htmlentities($_GET["subtable"]); ?>&variables=<?php echo htmlentities($variable); ?>&date0=<?php echo htmlentities($_GET["date0"]); ?>&time0=<?php echo htmlentities($_GET["time0"]); ?>&date1=<?php echo htmlentities($_GET["date1"]); ?>&time1=<?php echo htmlentities($_GET["time1"]); ?>&timerange=<?php echo htmlentities($_GET["timerange"]); ?>&timestamp_var=<?php echo htmlentities($timestamp_var); ?>&constraint=<?php echo htmlentities($_GET['constraint']); ?>&renormalize=<?php echo htmlentities($_GET['renormalize']); ?>" /></p>

<?php

if($variable == "status")
{
	// Show statistics for status
	$dbh = new PDO("sqlite:HappyFace.db");

	$module_table = verify_column_name($_GET['module'] . '_table');
	if(isset($_GET['subtable']) && $_GET['subtable'] != '')
		$module_table = verify_column_name($_GET['subtable']);

	$stmt = $dbh->prepare("SELECT DISTINCT $timestamp_var,status FROM $module_table WHERE $timestamp_var >= :timestamp_begin AND $timestamp_var <= :timestamp_end ORDER BY $timestamp_var");
	$stmt->bindParam(':timestamp_begin', $timestamp0);
	$stmt->bindParam(':timestamp_end', $timestamp1);

	$prev_timestamp = -1;
	$prev_status = -1;
	$accum_status = 0.0;
	$accum_timestamp = 0.0;
	$availabality = 0.0;

	$stmt->execute();
	while($data = $stmt->fetch())
	{
		$timestamp = $data['timestamp'];
		$status = $data['status'];

		if($prev_timestamp != -1 && $prev_status != -1)
		{
			if($prev_status > 0.5)
				$availability += ($timestamp - $prev_timestamp);

			$accum_status += $prev_status * ($timestamp - $prev_timestamp);
			$accum_timestamp += ($timestamp - $prev_timestamp);
		}

		$prev_timestamp = $timestamp;
		$prev_status = $status;
	}

	// Add period from last timestamp to now
	if($prev_timestamp != -1 && $prev_status != -1)
	{
		$timestamp = time();
		if($prev_status > 0.5)
			$availability += ($timestamp - $prev_timestamp);
		$accum_status += $prev_status * ($timestamp - $prev_timestamp);
		$accum_timestamp += ($timestamp - $prev_timestamp);
	}

	if($accum_timestamp)
	{
		$availability_str = round($availability/$accum_timestamp * 100);
		$mean_str = round($accum_status/$accum_timestamp * 100);
	}
	else
	{
		$availability_str = 'N/A';
		$mean_str = 'N/A';
	}

	echo "Availability (> 0.5): " . $availability_str . "%<br />";
	echo "Status Mean: " . $mean_str . "%<br />";
}?>
			<hr />
<?php
}
?>

		</form>
	</body>
</html>
