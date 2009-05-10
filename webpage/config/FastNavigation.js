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

/* Functiony to jump to the different modules and move content 
 * layer to the proper position.
 */
function goto(target) {
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
	window.scrollTo(0,targetY);
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
