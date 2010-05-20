<?php
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

 #=====================================
 # Array Constructor
 # Values <=> Timestamps

 $ta0 = date_parse($_GET["date0"] . " " . $_GET["time0"]);
 $ta1 = date_parse($_GET["date1"] . " " . $_GET["time1"]);

 $timestamp0 = mktime( $ta0["hour"],$ta0["minute"],0,$ta0["month"],$ta0["day"],$ta0["year"] );
 $timestamp1 = mktime( $ta1["hour"],$ta1["minute"],0,$ta1["month"],$ta1["day"],$ta1["year"] );

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
   $variables = array(verify_column_name($_GET['variable']));
 if(isset($_GET['variables']))
 {
   $variables = explode(',', $_GET['variables']);
   for($i = 0; $i < count($variables); ++$i)
     $variables[$i] = verify_column_name($variables[$i]);
 }
 $variable_str = implode(',', array_merge($variables, $constraint_vars));

 $stmt = $dbh->prepare("SELECT $timestamp_var,$variable_str FROM $module_table WHERE $timestamp_var >= :timestamp_begin AND $timestamp_var <= :timestamp_end $where_clause ORDER BY $timestamp_var");
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

   // Add data for each variable
   foreach($variables as $variable)
   {
     if(!isset($array["values"][$variable][$c_string]))
       $array["values"][$variable][$c_string] = array();
     $array["values"][$variable][$c_string][] = $data[$variable];
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

   $n_series = 0;
   foreach($variables as $index => $variable)
   {
     foreach($array["values"][$variable] as $constraint_string => $datapoints)
     {
       $serie = 'Serie' . $variable . '_' . $constraint_string;
       $DataSet->AddPoint($datapoints, $serie);
       $DataSet->AddSerie($serie);
       ++$n_series;

       if(count($constraint_vars) > 0 && count($variables) > 1)
         $name = "$variable, $constraint_string";
       else if(count($constraint_vars) > 0)
         $name = $constraint_string;
       else
         $name = $variable;
       $DataSet->SetSerieName($name, $serie);
     }
   }
 
   $DataSet->AddPoint($array["timestamps"],"SerieTime");
   $DataSet->SetAbsciseLabelSerie("SerieTime");

   if(count($variables) <= 1)
     $DataSet->SetYAxisName($variable);

   #$DataSet->SetYAxisFormat("time");
   #$DataSet->SetXAxisFormat("metric");

   // Initialise the graph   
   $Test = new pChart(900,350);
   $Test->setColorPalette(0,0,0,255); 
   $Test->setFontProperties("config/pChart/Fonts/tahoma.ttf",8);
   $Test->setGraphArea(85,30,850,250);
   $Test->drawFilledRoundedRectangle(7,7,900,350,5,240,240,240);
   $Test->drawRoundedRectangle(5,5,900,350,5,230,230,230);
   $Test->drawGraphArea(255,255,255,TRUE);
   $Test->drawScale($DataSet->GetData(),$DataSet->GetDataDescription(),SCALE_START0,150,150,150,TRUE,90,2,TRUE,$scale_factor);

   $hue = 0;
   $mod = 120;
   for($i = 0; $i < $n_series; ++$i)
   {
     $rgb = HSV_TO_RGB(fmod(($hue+240.0), 360.0)/360.0, 1.0, 1.0 - 0.3*($i%3));
     $Test->SetColorPalette($i, $rgb['R'], $rgb['G'], $rgb['B']);

     $hue += $mod;
     if($hue >= 360)
     {
       if($hue > 360)
         $mod /= 2.0;
       $hue = $mod/2.0;
     }
   }

   // show Grid if there are less than 48 timestamps
   if ( count($array["timestamps"]) < 48 ) { $Test->drawGrid(4,TRUE); }
   
   // Draw the 0 line   
   $Test->setFontProperties("config/pChart/Fonts/tahoma.ttf",10);
   $Test->drawTreshold(0,143,55,72,TRUE,TRUE);
   
   // Draw the line graph
   $Test->drawLineGraph($DataSet->GetData(),$DataSet->GetDataDescription());
   $Test->drawPlotGraph($DataSet->GetData(),$DataSet->GetDataDescription(),3,1,255,255,255);
   
   // Finish the graph
   $Test->setFontProperties("config/pChart/Fonts/tahoma.ttf",10);
   $Test->drawLegend(90,35,$DataSet->GetDataDescription(),255,255,255);
   $Test->setFontProperties("config/pChart/Fonts/tahoma.ttf",10);
   $Test->drawTitle(60,22,"Module: " . $_GET["module"],50,50,50,585);
   $Test->Stroke("plot.png");

 } else {
   echo "<h4>No Data available for Visualisation!!</h4>";
 }
?>
