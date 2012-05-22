<?php
$debug_msg_prefix = "plot_generator ".$_SERVER["REMOTE_ADDR"]." ".$_SERVER["REQUEST_TIME"].":";
$config = array();
$debug_call_counter = 0;
if(file_exists("plot_config.php"))
	include("plot_config.php");

function debug($msg)
{
	global $config, $debug_msg_prefix, $debug_call_counter;
	if(isset($config["debug_logging"]) and $config["debug_logging"] === True)
	{
		$debug_call_counter++;
		$msg = "($debug_call_counter)$msg";
		if(isset($config["debug_logpath"]) and strlen($config["debug_logpath"]) > 0)
			file_put_contents($config["debug_logpath"], $debug_msg_prefix." ".$msg."\n", FILE_APPEND);
		if(isset($config["debug_weblog"]) and $config["debug_weblog"] === True)
			echo $msg."<br />\n";
	}
}
debug("start plot generator");
?>
<html xmlns="http://www.w3.org/1999/xhtml">
	<head>
		<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />
		<title>Happy Face Plot Generator</title>
	</head>
	<body>
		<h2><strong>Module: <?php echo $_GET["module"]?></strong></h2>

<?php
include('plot_common.php');
include('plot_timerange_select.php');

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

// use presets for get-data
$timestamp_var = 'timestamp';
$module = '';
$subtable = '';
$constraint = '';
$squash = 0;
$renormalize = '';
$legend = '';
$variables = '';
$extra_title = '';
debug("\"verify\" input data");
// now insert actuall,verified get-data if available
if(isset($_GET['timestamp_var']) && $_GET['timestamp_var'] != '')
	$timestamp_var = verify_column_name($_GET['timestamp_var']);

if(isset($_GET['module']) && $_GET['module'] != '')
    $module = verify_column_name($_GET['module']);

$module_table = verify_column_name($_GET['module'] . '_table');
if(isset($_GET['subtable']) && $_GET['subtable'] != '')
    $module_table = verify_column_name($_GET['subtable']);

if(isset($_GET['constraint']) && $_GET['constraint'] != '')
    $constraint = $_GET['constraint'];

if(isset($_GET['renormalize']) && $_GET['renormalize'] != '')
    $renormalize = $_GET['renormalize'];

if(isset($_GET['legend']) && $_GET['legend'] != '')
    $legend = $_GET['legend'];

if(isset($_GET['variables']))
    $variables = $_GET['variables'];

if(isset($_GET['extra_title']))
    $extra_title = $_GET['extra_title'];

if(isset($_GET['squash']) && intval($_GET['squash']) != 0)
{
    $squash = intval($_GET['squash']);
}

print_plot_timerange_selection($module, $module_table, $timestamp_var, $constraint, $squash, $renormalize, $legend, null, $variables, $timestamp0, $timestamp1, $timestamp_now, $timestamp_timerange, false, $extra_title);

# create the variables array just now, the previous function call expects the raw string
if($squash != 0)
    $variables = array($variables);
else
    $variables = explode(',', $variables);

foreach($variables as $variable)
{
?>
			<h3>Variable(s): <?php echo htmlentities(implode(', ', explode(',', $variable))); ?></h3>
<?php
if(isset($_GET['renormalize']) && intval($_GET['renormalize']) != 0)
	echo '<p><strong>Trend Plot:</strong> Note that individual variables have been scaled so that they fit into [0,1] on this plot.</p>';
?>
			<p><img border="0" alt="<?php echo htmlentities($variable); ?> plot" src="show_plot.php?module=<?php echo htmlentities($_GET["module"]); ?>&subtable=<?php echo htmlentities($_GET["subtable"]); ?>&variables=<?php echo htmlentities(str_replace('+', '%2B', $variable)); ?>&date0=<?php echo htmlentities($_GET["date0"]); ?>&time0=<?php echo htmlentities($_GET["time0"]); ?>&date1=<?php echo htmlentities($_GET["date1"]); ?>&time1=<?php echo htmlentities($_GET["time1"]); ?>&timerange=<?php echo htmlentities($_GET["timerange"]); ?>&timestamp_var=<?php echo htmlentities($timestamp_var); ?>&constraint=<?php echo htmlentities($_GET['constraint']); ?>&renormalize=<?php echo htmlentities($_GET['renormalize']); ?>&legend=<?php echo htmlentities($_GET['legend']);?>&extra_title=<?php echo htmlentities($extra_title); ?>" /></p>

<?php

if($variable == "status")
{
	// Show statistics for status
	include("database.inc.php");


	$stmt = $dbh->prepare("SELECT DISTINCT $timestamp_var,status FROM $module_table WHERE $timestamp_var >= :timestamp_begin AND $timestamp_var <= :timestamp_end ORDER BY $timestamp_var");
	$stmt->bindParam(':timestamp_begin', $timestamp0);
	$stmt->bindParam(':timestamp_end', $timestamp1);

	$prev_timestamp = -1;
	$prev_status = -1;
	$accum_status = 0.0;
	$accum_timestamp = 0.0;
	$availability = 0.0;

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

	</body>
</html>
