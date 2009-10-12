<?php
 #=====================================
 # DataBase Initialisation
 # connect to SQLite database
 $dbh = new PDO("sqlite:HappyFace.db");

 #=====================================
 # Array Constructor
 # Values <=> Timestamps
  
 #echo "Start: " . $_GET["date0"] . " " . $_GET["time0"] . "</br>";
 #echo "End: " . $_GET["date1"] . " " . $_GET["time1"] . "</br>";
 #echo "Variable: ". $_GET["variable"] . "</br>";
 #echo "Module: " . $_GET["module"] . "</br>";
 
 $ta0 = date_parse($_GET["date0"] . " " . $_GET["time0"]);
 $ta1 = date_parse($_GET["date1"] . " " . $_GET["time1"]);
 
 $timestamp0 = mktime( $ta0["hour"],$ta0["minute"],0,$ta0["month"],$ta0["day"],$ta0["year"] );
 $timestamp1 = mktime( $ta1["hour"],$ta1["minute"],0,$ta1["month"],$ta1["day"],$ta1["year"] );
 
 $sql_command_strings[$_GET["module"]] = 'SELECT * FROM ' . $_GET["module"] . '_table WHERE timestamp >= ' .$timestamp0. ' AND timestamp <= ' . $timestamp1 . ' ORDER BY timestamp';

 # create empty arrays 
 $array["values"] = array();
 $array["timestamps"] = array();
 
 # fill arrays with data if available
 foreach ($dbh->query($sql_command_strings[$_GET["module"]]) as $data)
 {
   $array["values"][] = $data[$_GET["variable"]];
   $array["timestamps"][] = date( "d. M, H:i",$data["timestamp"]);
 }

 if (count($array["timestamps"]) > 48) {
   $scale_factor = floor ( count($array["timestamps"]) / 24 ) ;
 } else {
   $scale_factor = 1;
 }
 
 #=====================================
 # Plot Builder
 # start if there is data in arrays
 if (count($array["values"]) > 0 && count($array["timestamps"]) > 0) {
 
	 // Standard inclusions
	 include("config/pChart/pChart/pData.class");
	 include("config/pChart/pChart/pChart.class");
	  
	 // Dataset definition
	 $DataSet = new pData;
	 $DataSet->AddPoint($array["values"],"Serie1");

	 $DataSet->AddPoint($array["timestamps"],"Serie3");
	 $DataSet->AddSerie("Serie1");

	 $DataSet->SetAbsciseLabelSerie("Serie3");
	 $DataSet->SetSerieName($_GET["variable"],"Serie1");

	 $DataSet->SetYAxisName($_GET["variable"]);
	 
	 #$DataSet->SetYAxisFormat("time");
	 #$DataSet->SetXAxisFormat("metric");

	 // Initialise the graph   
	 $Test = new pChart(900,350);
	 $Test->setFontProperties("config/pChart/Fonts/tahoma.ttf",8);
	 $Test->setGraphArea(85,30,850,250);
	 $Test->drawFilledRoundedRectangle(7,7,900,350,5,240,240,240);
	 $Test->drawRoundedRectangle(5,5,900,350,5,230,230,230);
	 $Test->drawGraphArea(255,255,255,TRUE);
	 $Test->drawScale($DataSet->GetData(),$DataSet->GetDataDescription(),SCALE_START0,150,150,150,TRUE,90,2,TRUE,$scale_factor);
	 if ( count($array["timestamps"]) < 48 ) { $Test->drawGrid(4,TRUE); }
	 
	 // Draw the 0 line   
	 $Test->setFontProperties("config/pChart/Fonts/tahoma.ttf",10);
	 $Test->drawTreshold(0,143,55,72,TRUE,TRUE);
	  
	 // Draw the line graph
	 $Test->drawLineGraph($DataSet->GetData(),$DataSet->GetDataDescription());
	 $Test->drawPlotGraph($DataSet->GetData(),$DataSet->GetDataDescription(),3,2,255,255,255);
	  
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