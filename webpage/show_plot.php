<?php

 # This parses $_GET parameters to obtain timerange to plot
include('plot_common.php');
include('evalmath.class.php');

 #=====================================
 # DataBase Initialisation
 # connect to SQLite database
 $dbh = new PDO("sqlite:HappyFace.db");

 // Quick'n'dirty check to avoid SQL injection attacks on column names.
 // Unfortunately preparated statements do not work on table or column names
 // with SQLite.
 function verify_column_name($name)
 {
   for($i = 0; $i < count($name); ++$i)
     if(!ctype_alnum($name[$i]) && $name[$i] != '_')
       { echo "Invalid column name: $name"; die; }
   return $name;
 }

 // from http://www.actionscript.org/forums/archive/index.php3/t-50746.html
 function HSV_TO_RGB($H, $S, $V) // HSV Values: Number 0-1
 {                               // RGB Results: Number 0-255
   $RGB = array();

   if($S == 0)
   {
     $R = $G = $B = $V * 255;
   }
   else
   {
     $var_H = $H * 6;
     $var_i = floor( $var_H );
     $var_1 = $V * ( 1 - $S );
     $var_2 = $V * ( 1 - $S * ( $var_H - $var_i ) );
     $var_3 = $V * ( 1 - $S * (1 - ( $var_H - $var_i ) ) );

     if ($var_i == 0) { $var_R = $V ; $var_G = $var_3 ; $var_B = $var_1 ; }
     else if ($var_i == 1) { $var_R = $var_2 ; $var_G = $V ; $var_B = $var_1 ; }
     else if ($var_i == 2) { $var_R = $var_1 ; $var_G = $V ; $var_B = $var_3 ; }
     else if ($var_i == 3) { $var_R = $var_1 ; $var_G = $var_2 ; $var_B = $V ; }
     else if ($var_i == 4) { $var_R = $var_3 ; $var_G = $var_1 ; $var_B = $V ; }
     else { $var_R = $V ; $var_G = $var_1 ; $var_B = $var_2 ; }

     $R = $var_R * 255;
     $G = $var_G * 255;
     $B = $var_B * 255;
   }

   $RGB['R'] = $R;
   $RGB['G'] = $G;
   $RGB['B'] = $B;

   return $RGB;
 }

 $renormalize = isset($_GET['renormalize']) && intval($_GET['renormalize']) != 0;

 # Get timestamp variable to show
 $timestamp_var = 'timestamp';
 if(isset($_GET['timestamp_var']) && $_GET['timestamp_var'] != '')
   $timestamp_var = verify_column_name($_GET['timestamp_var']);
 $module_table = verify_column_Name($_GET['module'] . '_table');
 if(isset($_GET['subtable']) && $_GET['subtable'] != '')
   $module_table = verify_column_name($_GET['subtable']);

 # Apply additional constraint
 $where_clause = "";
 $constraint_vars = array();
 $constraint_values = array();
 if(isset($_GET['constraint']) && $_GET['constraint'] != '')
 {
   $comp = explode('=', $_GET['constraint'], 2);
   if(count($comp) == 2 && $comp[1] != '')
   {
     $constraint_var = verify_column_name($comp[0]);
     $comp = explode(',', $comp[1]);

     // If constraint is on one column only then just select it via a WHERE clause
     // Otherwise exclude manually later.
     if(count($comp) == 1)
     {
       $constraint_value = $comp[0];
       $where_clause = "AND $constraint_var = :constraint_value";
     }
     else
     {
       $constraint_vars[] = $constraint_var;
       $constraint_values[$constraint_var] = $comp; // constrain this var to the given values
     }
   }
   else
   {
     // make a separate plot for each value of this var but don't constrain
     if(count($comp) == 2)
       $constraint_vars[] = verify_column_name($comp[0]);
     else
       $constraint_vars[] = verify_column_name($_GET['constraint']);
   }
 }

 # Get variables to plot
 if(isset($_GET['variable']))
   $variables = array($_GET['variable']);
 if(isset($_GET['variables']))
 {
   $variables = explode(',', $_GET['variables']);
 }

 // Get legend
 $legend = 'bottom';
 if(isset($_GET['legend']) && $_GET['legend'] != '')
   $legend = $_GET['legend'];

 $stmt = $dbh->prepare("SELECT * FROM $module_table WHERE $timestamp_var >= :timestamp_begin AND $timestamp_var <= :timestamp_end $where_clause ORDER BY $timestamp_var");
 $stmt->bindParam(':timestamp_begin', $timestamp0);
 $stmt->bindParam(':timestamp_end', $timestamp1);
 if(isset($constraint_value))
   $stmt->bindParam(':constraint_value', $constraint_value);

 # create empty arrays 
 $array["values"] = array();
 $array["timestamps"] = array();
 foreach($variables as $variable)
   $array["values"][$variable] = array();
 
 # fill arrays with data if available
 $stmt->execute();
 $avail_columns = array();
 for($i = 0; $i < $stmt->columnCount(); ++$i)
 {
   $meta = $stmt->getColumnMeta($i);
   if($meta['native_type'] == 'integer' || $meta['native_type'] == 'float' || $meta['native_type'] == 'double')
     $avail_columns[] = $meta['name'];
 }

 $meval = new EvalMath;
 $meval->suppress_errors = true;
 while($data = $stmt->fetch())
 {
   // Check constraints
   $c_array = array();
   $constrained = false;
   foreach($constraint_vars as $constraint_var)
   {
     if(isset($constraint_values[$constraint_var]))
       if(array_search($data[$constraint_var], $constraint_values[$constraint_var]) === false)
         { $constrained = true; break; }
     $c_array[] = $data[$constraint_var];
   }

   if($constrained) continue;
   $c_string = implode(',', $c_array);

   foreach($avail_columns as $column)
   {
     if(!isset($data[$column]) || $data[$column] == '')
       $meval->Evaluate($column . '= -1'); // value not available in DB
     else
       $meval->Evaluate($column . '=' . floatval($data[$column]));
   }

   // Add data for each variable
   foreach($variables as $variable)
   {
     if(!isset($array["values"][$variable][$c_string]))
       $array["values"][$variable][$c_string] = array();
     $value = $meval->Evaluate($variable);
     if($value !== false)
       $array["values"][$variable][$c_string][] = $value;
     else
       $array["values"][$variable][$c_string][] = -2; // value not computable (division by zero, ...)
   }

   $date = date( "d. M, H:i",$data[$timestamp_var]);
   if(count($array['timestamps']) == 0 || $array['timestamps'][count($array['timestamps'])-1] != $date)
     $array["timestamps"][] = $date;
 }

 if (count($array["timestamps"]) > 48) {
   $scale_factor = floor ( count($array["timestamps"]) / 24 ) ;
 } else {
   $scale_factor = 1;
 }
 
 #=====================================
 # Plot Builder
 # start if there is data in arrays
 if (count($array["timestamps"]) > 0) {
 
   // Standard inclusions
   include("config/pChart/pChart/pData.class");
   include("config/pChart/pChart/pChart.class");
    
   // Dataset definition
   $DataSet = new pData;

   $series = array();
   $serie_names = array();
   foreach($variables as $index => $variable)
   {
     foreach($array["values"][$variable] as $constraint_string => $datapoints)
     {
       if($renormalize)
       {
         $min = min($datapoints);
         $max = max($datapoints);
	 foreach($datapoints as &$value)
	   if(abs($min - $max) > 0.0001)
	     $value = ($value - $min) / ($max - $min);
	   else
	     $value = 0.5;
       }

       $serie = 'Serie' . $variable . '_' . $constraint_string;
       $series[] = $serie;
       $DataSet->AddPoint($datapoints, $serie);
       $DataSet->AddSerie($serie);

       if(count($constraint_vars) > 0 && count($variables) > 1)
         $name = "$variable, $constraint_string";
       else if(count($constraint_vars) > 0)
         $name = $constraint_string;
       else
         $name = $variable;

       $serie_names[] = $name;
       $DataSet->SetSerieName($name, $serie);
     }
   }
 
   $DataSet->AddPoint($array["timestamps"],"SerieTime");
   $DataSet->SetAbsciseLabelSerie("SerieTime");

   if(count($variables) <= 1)
     if($renormalize)
       $DataSet->SetYAxisName($variable . " [arb. units]");
     else
       $DataSet->SetYAxisName($variable);

   #$DataSet->SetYAxisFormat("time");
   #$DataSet->SetXAxisFormat("metric");

   // Test graph to measure some metrics
   $Test = new pChart(1,1);

   // Preferred plot size
   $plot_width = 900;
   $plot_height = 350;

   // g graph area
   $gleft = 50;
   $gright = 890;
   $gtop = 30;
   $gbottom = 250;

   $Test->setFontProperties("config/pChart/Fonts/tahoma.ttf",10);
   $LegendLimit = count($series);
   if($legend == 'inside')
   {
     $gheight = $gbottom - $gtop;
     $LegendSize = $Test->getLegendBoxSize($DataSet->GetDataDescription());
     $LegendHeight = $LegendSize[1];

     // Make sure legend fits into plot
     while($LegendHeight > $gheight - 10)
     {
       --$LegendLimit;
       $DataSet->RemoveSerie($series[$LegendLimit]);
       $DataSet->removeSerieName($series[$LegendLimit]);
       $LegendTemp = $Test->getLegendBoxSize($DataSet->GetDataDescription());
       $LegendHeight = $LegendTemp[1];
     }

     for($j = $LegendLimit; $j < count($series); ++$j)
     {
       $DataSet->AddSerie($series[$j]);
       $DataSet->SetSerieName($serie_names[$j], $series[$j]);
     }

     // The two extra entries will be used for dummy entries ("+ N more")
     if($LegendLimit < count($series))
       $LegendLimit -= 2;
   }
   else if($legend == 'right')
   {
     $LegendSize = $Test->getLegendBoxSize($DataSet->GetDataDescription());
     $gright = $gright - $LegendSize[0] - 20;
     $plot_height = max($plot_height, $LegendSize[1] + 35);
   }
   else if($legend == 'bottom')
   {
     //$LegendSize = $Test->getLegendBoxSize($DataSet->GetDataDescription());
     $LegendBoxes = array();
     $LegendEntryHeight = 0; // The size of the largest legend entry. We make all entries this height so that the entries are not shifted against each other.

     // Deactivate all series
     for($j = 0; $j < count($series); ++$j)
     {
       $DataSet->RemoveSerie($series[$j]);
       $DataSet->removeSerieName($series[$j]);
     }

     // Measure each legend entry
     for($j = 0; $j < count($series); ++$j)
     {
       $DataSet->AddSerie($series[$j]);
       $DataSet->SetSerieName($serie_names[$j], $series[$j]);
       $LegendBoxes[] = $Test->getLegendBoxSize($DataSet->GetDataDescription());
       $LegendEntryHeight = max($LegendHeight, $LegendBoxes[count($LegendBoxes)-1][1]);
       $DataSet->RemoveSerie($series[$j]);
       $DataSet->removeSerieName($series[$j]);
     }

     // Activate all series again
     for($j = 0; $j < count($series); ++$j)
     {
       $DataSet->AddSerie($series[$j]);
       $DataSet->SetSerieName($serie_names[$j], $series[$j]);
     }

     // Check how many columns we can show simultaneously
     $PrevLegendWidth = 0;
     $PrevLegendHeight = 0;
     for($columns = 1; $columns <= count($series); ++$columns)
     {
       // Examine each column
       $LegendWidth = $LegendHeight = 0;
       $ColumnPos = array(0);
       for($column = 0; $column < $columns; ++$column)
       {
         $ColumnWidth = 0;
         $rows = floor( (float)(count($series) + $columns - 1 - $column) / $columns);
         for($row = 0; $row < $rows; ++$row)
	   $ColumnWidth = max($ColumnWidth, $LegendBoxes[$row*$columns+$column][0]);
	 $LegendWidth += $ColumnWidth;
	 $ColumnPos[] = $LegendWidth;
	 $LegendHeight = max($LegendHeight, $LegendEntryHeight * $rows);
       }

       // horizontal graph area is fixed in bottom mode so we can determine
       // l metrics already at this point - and need to do so to determine
       // the area that can be occupied by legend columns.
       $lleft = $gleft - 40;
       $lright = $gright;

       if($LegendWidth > $lright - $lleft && $PrevLegendWidth > 0 && $PrevLegendHeight > 0)
       {
         break;
       }
       else
       {
         $PrevLegendWidth = $LegendWidth;
	 $PrevLegendHeight = $LegendHeight;
	 $PrevColumnPos = $ColumnPos;
       }
     }

     $columns = $columns - 1;
     $LegendWidth = $PrevLegendWidth;
     $LegendHeight = $PrevLegendHeight;
     $ColumnPos = $PrevColumnPos;

     // Make place for legend on the bottom
     //$gbottom = $gbottom - $LegendHeight - 10;
     $plot_height += $LegendHeight;
   }

   // More metrics based on the g metrics: l=graph area including axis labels
   $lleft = $gleft - 40;
   $lright = $gright;
   $ltop = $gtop - 20;
   $lbottom = $gbottom + 90;

   // Create final output plot
   $Test = new pChart($plot_width, $plot_height);

   // Create color palette
   $hue = 0;
   $mod = 120;
   $palette = array();
   for($i = 0; $i < count($series); ++$i)
   {
     $rgb = HSV_TO_RGB(fmod(($hue+240.0), 360.0)/360.0, 1.0, 1.0 - 0.3*($i%3));
     $Test->SetColorPalette($i, $rgb['R'], $rgb['G'], $rgb['B']);
     $palette[] = $rgb;

     $hue += $mod;
     if($hue >= 360)
     {
       if($hue > 360)
         $mod /= 2.0;
       $hue = $mod/2.0;
     }
   }

   $Test->setFontProperties("config/pChart/Fonts/tahoma.ttf",8);
   $Test->setGraphArea($gleft,$gtop,$gright,$gbottom);
 
   // For a trend plot make sure the min and max values don't
   // stick to the border
   if($renormalize)
     $Test->setFixedScale(-0.00, 1.00);

   // show Grid if there are less than 48 timestamps
   $Test->drawScale($DataSet->GetData(),$DataSet->GetDataDescription(),SCALE_START0,0,0,0,TRUE,90,2,TRUE,$scale_factor);
   if(count($array["timestamps"]) < 48) $Test->drawGrid(4,FALSE, 220, 220, 220);
   // Don't use drawGraphArea because this chooses strange colors
   $Test->drawLine($gleft, 30, $gright, 30, 0,0,0);
   $Test->drawLine($gright, 30, $gright, $gbottom, 0,0,0);
   // Draw the 0 line
   $Test->setFontProperties("config/pChart/Fonts/tahoma.ttf",10);
   $Test->drawTreshold(0,143,55,72,TRUE,TRUE);
   
   // Draw the line graph
   $Test->drawLineGraph($DataSet->GetData(),$DataSet->GetDataDescription());
   $Test->drawPlotGraph($DataSet->GetData(),$DataSet->GetDataDescription(),3,1,255,255,255);

   // Draw the legend
   if($legend == 'inside')
   {
     if($LegendLimit < count($series))
     {
       for($j = $LegendLimit; $j < count($series); ++$j)
       {
         $DataSet->RemoveSerie($series[$j]);
         $DataSet->removeSerieName($series[$j]);
       }

       $DataSet->AddSerie("dummy1");
       $DataSet->AddSerie("dummy2");
       $DataSet->SetSerieName("¨¨", "dummy1"); // Use diaeresis instead of ldots, otherwise the row gets squashed together with the row below
       $DataSet->SetSerieName(sprintf("+ %d more", count($series)-$LegendLimit), "dummy2");
     }

     $Test->SetColorPalette($LegendLimit, 255,255,255);
     $Test->SetColorPalette($LegendLimit+1, 255,255,255);

     $Test->drawLegend(90,35,$DataSet->GetDataDescription(), 255,255,255, -1,-1,-1, -1,-1,-1, TRUE);

     if($LegendLimit < count($series))
     {
       for($j < $LegendLimit; $j < count($series); ++$j)
       {
         $DataSet->AddSerie($series[$j]);
         $DataSet->SetSerieName($serie_names[$j], $series[$j]);
       }

       $DataSet->removeSerieName("dummy1");
       $DataSet->removeSerieName("dummy2");
       $DataSet->RemoveSerie("dummy1");
       $DataSet->RemoveSerie("dummy2");
     }
   }
   else if($legend == 'right')
   {
     // TODO: LegendLimit
     $Test->drawLegend($lright+20,35,$DataSet->GetDataDescription(), -1,-1,-1, -1,-1,-1, -1,-1,-1, FALSE);
   }
   else if($legend == 'bottom')
   {
     for($j = 0; $j < count($series); ++$j)
     {
       $DataSet->RemoveSerie($series[$j]);
       $DataSet->removeSerieName($series[$j]);
     }

     for($j = 0; $j < $LegendLimit; ++$j)
     {
       $DataSet->AddSerie($series[$j]);
       $DataSet->SetSerieName($serie_names[$j], $series[$j]);

       $row = floor($j / $columns);
       $column = $j % $columns;
       $Test->SetColorPalette(0, $palette[$j]['R'], $palette[$j]['G'], $palette[$j]['B']);
       $sx = $lleft + (($lright - $lleft) - $LegendWidth)/2;
       $sy = $lbottom + 10;
       $Test->drawLegend($sx + $ColumnPos[$column], $sy + $row*$LegendEntryHeight, $DataSet->GetDataDescription(), -1,-1,-1, -1,-1,-1, -1,-1,-1, FALSE);

       $DataSet->RemoveSerie($series[$j]);
       $DataSet->removeSerieName($series[$j]);
     }
 
     for($j = 0; $j < count($series); ++$j)
     {
       $DataSet->AddSerie($series[$j]);
       $DataSet->SetSerieName($serie_names[$j], $series[$j]);
     }
   }

   // Finish the graph
   $Test->drawTitle(60,22,"Module: " . $_GET["module"],50,50,50,585);
   $Test->Stroke("plot.png");

 } else {
   echo "<h4>No Data available for Visualisation!!</h4>";
 }
?>
