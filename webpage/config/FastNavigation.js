/* Preload the two arrows to show/hide the fast nav bar */
var pic1 = new Image();
pic1.src = "config/images/leftarrow.png";
var pic2 = new Image();
pic2.src = "config/images/rightarrow.png";

/* Function to show/hide the navigation bar 
 *
 * Alert: offsetLeft in IE is reported with totally different
 * values compared to e.g. Firefox. Therefore this strange
 * number of '42'.
 */
function movenav(navid) {
	if (document.getElementById(navid).offsetLeft >= -42) {
		document.getElementById(navid).style.left="-192px";
		document.getElementById(navid + "arrow").src="config/images/rightarrow.png";
	} else {
		document.getElementById(navid).style.left="8px";
		document.getElementById(navid + "arrow").src="config/images/leftarrow.png";
	}
};

/* Function to jump to the different modules and move content 
 * layer to the proper position.
 */
function goto(target) {
	var i;
	for(i = 0; i < document.images.length; i++) {
		if (document.images[i].height == 0 && !document.images[i].complete) {
			if(typeof(target) == 'number')
				setTimeout("goto(" + target + ")", 100);
			else
				setTimeout("goto(\"" + target + "\")", 100);
			return;
		}
	}

	if(typeof(target) == 'number')
	{
		scroll(0, target);
	}
	else
	{
		var browser = getBrowser();
		if (browser == "FF") {
			var targetY = document.getElementById(target).offsetTop+15;
		} 
		else if (browser == "IE7") {
			var targetY = document.getElementById(target).offsetTop-140;
		} 
		else {
			var targetY = document.getElementById(target).offsetTop;
		}
		document.getElementById('ReloadMod').value=target;
		document.getElementById('HistoReloadMod1').value=target;
		document.getElementById('HistoReloadMod2').value=target;
		window.scrollTo(0,targetY);
	}
	if (selectedMod != "") {
		document.getElementById('FNImage_'+selectedMod).style.border="solid 1px #696969";
	}
	document.getElementById('FNImage_'+target).style.border="solid 1px #000000";
	selectedMod = target;
};

/* Get browser type */
function getBrowser() {
	var browser = "UNKNOWN";
	if (navigator.userAgent.search(/Firefox/) > -1) {
		browser = "FF";
	}
	if (navigator.userAgent.search(/MSIE 7/) > -1) {
		browser = "IE7";
	}
	if (navigator.userAgent.search(/MSIE 8/) > -1) {
		browser = "IE8";
	}
	if (navigator.userAgent.search(/Opera/) > -1) {
		browser = "OP";
	}
	return browser;
};

/* Calculate size of FastNav bar */
function getFNSize(fn_id) {
	var browser = getBrowser();
	
	if (browser == "IE7" | browser == "IE8") {
		var fnSize=document.documentElement.clientHeight-150;
	} else {	
		var fnSize=window.innerHeight-150;
	}

	/* Set a minimum size for the FastNav bar */
	if (fnSize < 50) {
		fnSize=50
	}

	document.getElementById(fn_id).style.height=fnSize+'px';
}
