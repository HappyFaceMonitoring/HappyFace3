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
function movenav (navid) {
	if (document.getElementById(navid).offsetLeft >= -42) {
		document.getElementById(navid).style.left="-192px";
		document.getElementById(navid + "arrow").src="config/images/rightarrow.png";
	} else {
		document.getElementById(navid).style.left="8px";
		document.getElementById(navid + "arrow").src="config/images/leftarrow.png";
	}
}
