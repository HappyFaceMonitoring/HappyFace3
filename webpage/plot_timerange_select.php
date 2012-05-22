<?php

// Convert seconds to a more appropriate unit
function convert_seconds($seconds)
{
	$value = $seconds/60.0;
	$unit = 'm';

	if($value > 180)
	{
		$value /= 60.0;
		$unit = 'h';
		if($value > 72)
		{
			$value /= 24.0;
			$unit = 'd';

			if($value > 21)
			{
				$value /= 7.0;
				$unit = 'w';

				if($value > 52)
				{
					$value /= (365/7.0);
					$unit = 'y';
				}
			}
		}
	}

	return array(round($value), $unit);
}

// Convert an options string for a <select> widget with available units
function get_options_string($unit)
{
	$result  = '<option value="m"' . ($unit[1] == 'm' ? ' selected="selected"' : '') . '>minutes</option>';
	$result .= '<option value="h"' . ($unit[1] == 'h' ? ' selected="selected"' : '') . '>hours</option>';
	$result .= '<option value="d"' . ($unit[1] == 'd' ? ' selected="selected"' : '') . '>days</option>';
	$result .= '<option value="w"' . ($unit[1] == 'w' ? ' selected="selected"' : '') . '>weeks</option>';
	$result .= '<option value="y"' . ($unit[1] == 'y' ? ' selected="selected"' : '') . '>years</option>';
	return $result;
}

// Prints a form to select a timerange and variable to plot
// variable_list may be empty if $variables is set. if variable_list is given
// then $variables should be a single variable only.
function print_plot_timerange_selection($module, $subtable, $timestamp_var, $constraint, $squash, $renormalize, $legend, $variable_list, $variables, $timestamp_begin, $timestamp_end, $timestamp_now, $timestamp_timerange, $new_window, $extra_title='')
{
	debug("print_plot_timerange_selection()");
	// Construct unit and variable selection widgets
	$variables_arr = explode(',', $variables);
	$variable_str = $variables_arr[0];
	debug("if-statement");
	if($variable_list)
	{
		$variable_out = '<select id="' . htmlentities($module) . '_variable_list">';
		$variable_out .= '<option value="all">all variables (trend plot)</option>';
		debug("if-1");
		foreach($variable_list as $variable)
			$variable_out .= '<option value="' . htmlentities($variable) . '"' . ($variable == $variable_str ? ' selected="selected"' : '') . '>' . htmlentities($variable) . '</option>';
		debug("if-2");
		$variable_out .= '</select>';
	}
	else
	{
		debug("else-1");
		$variable_out = '<strong>' . htmlentities($variable_str) . '</strong>';
		if(count($variables_arr) > 1)
			$variable_out .= " +" . (count($variables_arr)-1) . " more";
	}
	debug("conversion 1");
	// Construct unit selection
	$seconds = $timestamp_end - $timestamp_begin;
	$timerange_now_unit = convert_seconds(time() - $timestamp_begin);
	debug("conversion 2");
	$timerange_fix_unit = convert_seconds($seconds);

	// Default
	if($legend == '') $legend = 'bottom';
	debug("output-block");
	echo '<script type="text/javascript">' . "\n";
	echo 'function ' . $module . '_plot_submit(module)' . "\n";
	echo '{' . "\n";
	echo '  if(document.getElementById(module + "_variable_list"))' . "\n";
	echo '  {' . "\n";
	echo '    if(document.getElementById(module + "_variable_list").value != "all")' . "\n";
	echo '    {' . "\n";
	echo '      document.getElementById(module + "_plot_variables").value = document.getElementById(module + "_variable_list").value;' . "\n";
	echo '      document.getElementById(module + "_plot_squash").value = "0";' . "\n";
	echo '      document.getElementById(module + "_plot_renormalize").value = "0";' . "\n";
	echo '    }' . "\n";
	echo '    else' . "\n";
	echo '    {' . "\n";
	echo '      document.getElementById(module + "_plot_variables").value = "' . implode(',', $variable_list ? $variable_list  : array()) . '";' . "\n";
	echo '      document.getElementById(module + "_plot_squash").value = "1";' . "\n";
	echo '      document.getElementById(module + "_plot_renormalize").value = "1";' . "\n";
	echo '    }' . "\n";
	echo '  }' . "\n";
	echo '  if(document.getElementById(module + "_direct").checked)' . "\n";
	echo '  {' . "\n";
	echo '    document.getElementById(module + "_date0").value = document.getElementById(module + "_direct_date0").value;' . "\n";
	echo '    document.getElementById(module + "_time0").value = document.getElementById(module + "_direct_time0").value;' . "\n";
	echo '    document.getElementById(module + "_date1").value = document.getElementById(module + "_direct_date1").value;' . "\n";
	echo '    document.getElementById(module + "_time1").value = document.getElementById(module + "_direct_time1").value;' . "\n";
	echo '  }' . "\n";
	echo '  else if(document.getElementById(module + "_timerange_now").checked)' . "\n";
	echo '  {' . "\n";
	echo '    document.getElementById(module + "_timerange").value = document.getElementById(module + "_timerange_now_interval").value + document.getElementById(module + "_timerange_now_unit").value;' . "\n";
	echo '    document.getElementById(module + "_date0").value = "";' . "\n";
	echo '    document.getElementById(module + "_time0").value = "";' . "\n";
	echo '    document.getElementById(module + "_date1").value = "";' . "\n";
	echo '    document.getElementById(module + "_time1").value = "";' . "\n";
	echo '  }' . "\n";
	echo '  else if(document.getElementById(module + "_timerange_fix").checked)' . "\n";
	echo '  {' . "\n";
	echo '    document.getElementById(module + "_timerange").value = document.getElementById(module + "_timerange_fix_interval").value + document.getElementById(module + "_timerange_fix_unit").value;' . "\n";
	echo '    document.getElementById(module + "_date0").value = "";' . "\n";
	echo '    document.getElementById(module + "_time0").value = "";' . "\n";
	echo '    document.getElementById(module + "_date1").value = document.getElementById(module + "_timerange_fix_date1").value;' . "\n";
	echo '    document.getElementById(module + "_time1").value = document.getElementById(module + "_timerange_fix_time1").value;' . "\n";
	echo '  }'. "\n";
	echo '}' . "\n";
	echo '</script>';
	echo '<form action="plot_generator.php" method="get"' . ($new_window ? ' onsubmit="javascript: submitFormToWindow(this)"' : '') . '>';
	echo ' <table cellspacing="0" cellpadding="2">';
	echo '  <tr>';
	echo '   <td style="padding-right: .3em;">';
	echo '    <input type="hidden" name="module" value="' . htmlentities($module) . '" />';
	echo '    <input type="hidden" name="subtable" value="' . htmlentities($subtable) . '" />';
	echo '    <input type="hidden" name="timestamp_var" value="' . htmlentities($timestamp_var) . '" />';
	echo '    <input type="hidden" name="constraint" value="' . htmlentities($constraint) . '" />';
    echo '    <input type="hidden" name="extra_title" value="' . htmlentities($extra_title) . '" />';
	echo '    <input type="hidden" name="squash" id="' . $module . '_plot_squash" value="' . htmlentities($squash) . '" />';
	echo '    <input type="hidden" name="renormalize" id="' . $module . '_plot_renormalize" value="' . htmlentities($renormalize) . '" />';
	echo '    <input type="hidden" name="variables" id="' . $module . '_plot_variables" value="' . htmlentities($variables) . '" />';
	echo '    <input type="hidden" name="timerange" id="' . $module . '_timerange" />';
	echo '    <input type="hidden" name="date0" id="' . $module . '_date0" />';
	echo '    <input type="hidden" name="time0" id="' . $module . '_time0" />';
	echo '    <input type="hidden" name="date1" id="' . $module . '_date1" />';
	echo '    <input type="hidden" name="time1" id="' . $module . '_time1" />';
        echo '    <input id="' . $module . '_direct" type="radio" name="group"' . (!$timestamp_timerange ? ' checked="checked"' : '') . ' />';
	echo '    Start:';
	echo '   </td>';
	echo '   <td style="padding-right: .9em;"><input id="' . $module . '_direct_date0" type="text" size="10" style="text-align: center;" value="' . strftime('%Y-%m-%d', $timestamp_begin) . '" onchange="javascript:document.getElementById(\'' . $module . '_direct\').checked=true" /> <input id="' . $module . '_direct_time0" type="text" size="5" style="text-align: center;" value="' . strftime('%H:%M', $timestamp_begin) . '" onchange="javascript:document.getElementById(\'' . $module . '_direct\').checked=true" /></td>';
	echo '   <td style="padding-right: .3em;">Stop:</td>';
	echo '   <td style="padding-right: .4em; border-right: 1px solid grey;"><input id="' . $module . '_direct_date1" type="text" size="10" style="text-align: center;" value="' . strftime('%Y-%m-%d', $timestamp_end) . '" onchange="javascript:document.getElementById(\'' . $module .'_direct\').checked=true" /> <input id="' . $module . '_direct_time1" type="text" size="5" style="text-align: center;" value="' . strftime('%H:%M', $timestamp_end) . '" onchange="javascript:document.getElementById(\'' . $module . '_direct\').checked=true" /></td>';
	echo '   <td style="padding-left: .4em;">Variable: ' . $variable_out . '</td>';
	echo '  </tr>';
	echo '  <tr>';
	echo '   <td style="padding-right: .3em;"><input id="' . $module . '_timerange_now" type="radio" name="group"' . (($timestamp_timerange && $timestamp_now) ? ' checked="checked"' : '') . ' />Interval:</td>';
	echo '   <td style="padding-right: .9em;">';
	echo '    <input id="' . $module . '_timerange_now_interval" type="text" size="3" style="text-align: center;" value="' . $timerange_now_unit[0] . '" onchange="javascript:document.getElementById(\'' . $module . '_timerange_now\').checked=true" />';
	echo '    <select id="' . $module . '_timerange_now_unit" onchange="javascript:document.getElementById(\'' . $module . '_timerange_now\').checked=true" >';
	echo '     ' . get_options_string($timerange_now_unit);
	echo '    </select>';
	echo '   </td>';
	echo '   <td style="padding-right: .3em;">Stop:</td>';
	echo '   <td style="padding-right: .4em; border-right: 1px solid grey;">now</td>';
	echo '   <td style="padding-left:  .4em;">Legend:';
	echo '    <input type="radio" name="legend" value="bottom"' . (($legend == 'bottom') ? ' checked="checked"' : '') . ' />bottom';
	echo '    <input type="radio" name="legend" value="inside"' . (($legend == 'inside') ? ' checked="checked"' : '') . ' />inside';
	echo '    <input type="radio" name="legend" value="right"' . (($legend == 'right') ? ' checked="checked"' : '') . ' />right';
	echo '   </td>';
	echo '  </tr>';
	echo '  <tr>';
	echo '   <td style="padding-right: .3em;"><input id="' . $module . '_timerange_fix" type="radio" name="group"' . (($timestamp_timerange && !$timestamp_now) ? ' checked="checked"' : '') . ' />Interval:</td>';
	echo '   <td style="padding-right: .9em;">';
	echo '    <input id="' . $module . '_timerange_fix_interval" type="text" size="3" style="text-align: center;" value="' . $timerange_fix_unit[0] . '" onchange="javascript:document.getElementById(\'' . $module . '_timerange_fix\').checked=true" />';
	echo '    <select id="' . $module . '_timerange_fix_unit" onchange="javascript:document.getElementById(\'' . $module . '_timerange_fix\').checked=true">';
	echo '     ' . get_options_string($timerange_fix_unit);
	echo '    </select>';
	echo '   </td>';
	echo '   <td style="padding-right: .3em;">Stop:</td>';
	echo '   <td style="padding-right: .4em; border-right: 1px solid grey;"><input id="' . $module . '_timerange_fix_date1" type="text" size="10" style="text-align: center;" value="' . strftime('%Y-%m-%d', $timestamp_end) . '" onchange="javascript:document.getElementById(\'' . $module . '_timerange_fix\').checked=true" /> <input id="' . $module . '_timerange_fix_time1" type="text" size="5" style="text-align: center;" value="' . strftime('%H:%M', $timestamp_end) . '" onchange="javascript:document.getElementById(\'' . $module . '_timerange_fix\').checked=true" /></td>';
	echo '   <td style="padding-left: .4em;"><button onfocus="this.blur()" onclick="javascript:' . $module . '_plot_submit(\'' . $module . '\')">Show Plot</button></td>';
	echo '  </tr>';
	echo ' </table>';
	echo '</form>';
	debug("end: print_plot_timerange_selection()");
}

?>
