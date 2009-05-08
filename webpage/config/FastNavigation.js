/* function to show/hide the navigation bar */
function movenav() {
	if (document.getElementById("nav").offsetLeft >= 0) {
		document.getElementById("nav").style.left="-192px";
		document.getElementById("navarrow").src="config/images/rightarrow.png";
		//document.getElementById("TabbedPanelsContentGroup1").style.left="-202px";
	} else {
		document.getElementById("nav").style.left="8px";
		document.getElementById("navarrow").src="config/images/leftarrow.png";
		//document.getElementById("TabbedPanelsContentGroup1").style.left="0px";
	}
}
