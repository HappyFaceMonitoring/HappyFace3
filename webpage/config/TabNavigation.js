/* Javascript functions for the HappyFace tab navigation */

/* Initialise */
var HappyTab;
var AutoReload = true;
if (!HappyTab) HappyTab = {};
if (!HappyTab.Widget) HappyTab.Widget = {};

HappyTab.Widget.HappyPanels = function(element, defTab, defModule, initialScroll, opts)
{
	this.element = document.getElementById(element);
	this.defaultTab = document.getElementById(defTab + "_tab");
	this.defaultModule = defModule;
	this.bindings = [];
	this.tabSelectedClass = "HappyPanelsTabSelected";
	this.tabHoverClass = "HappyPanelsTabHover";
	this.tabFocusedClass = "HappyPanelsTabFocused";
	this.panelVisibleClass = "HappyPanelsContentVisible";
	this.focusElement = null;
	this.hasFocus = false;
	this.currentTab = null;
	this.enableKeyboardNavigation = true;

	HappyTab.Widget.HappyPanels.setOptions(this, opts);

	this.attachBehaviors(initialScroll);
	document.getElementById(defTab + "_panel").style.visibility = "visible";
	document.getElementById("HappyPanelsContentGroup").style.visibility = "visible";
};

HappyTab.Widget.HappyPanels.prototype.getElementChildren = function(element)
{
	var children = [];
	var child = element.firstChild;
	while (child)
	{
		if (child.nodeType == 1 /* Node.ELEMENT_NODE */)
			children.push(child);
		child = child.nextSibling;
	}
	return children;
};

HappyTab.Widget.HappyPanels.prototype.addClassName = function(ele, className)
{
	if (!ele || !className || (ele.className && ele.className.search(new RegExp("\\b" + className + "\\b")) != -1))
		return;
	ele.className += (ele.className ? " " : "") + className;
};

HappyTab.Widget.HappyPanels.prototype.removeClassName = function(ele, className)
{
	if (!ele || !className || (ele.className && ele.className.search(new RegExp("\\b" + className + "\\b")) == -1))
		return;
	ele.className = ele.className.replace(new RegExp("\\s*\\b" + className + "\\b", "g"), "");
};

HappyTab.Widget.HappyPanels.setOptions = function(obj, optionsObj, ignoreUndefinedProps)
{
	if (!optionsObj)
		return;
	for (var optionName in optionsObj)
	{
		if (ignoreUndefinedProps && optionsObj[optionName] == undefined)
			continue;
		obj[optionName] = optionsObj[optionName];
	}
};

HappyTab.Widget.HappyPanels.prototype.getTabGroup = function()
{
	if (this.element)
	{
		var children = this.getElementChildren(this.element);
		if (children.length)
			return children[0];
	}
	return null;
};

HappyTab.Widget.HappyPanels.prototype.getTabs = function()
{
	var tabs = [];
	var tg = this.getTabGroup();
	if (tg)
		tabs = this.getElementChildren(tg);
	return tabs;
};

// Return the category name for the given tab
HappyTab.Widget.HappyPanels.prototype.getTabCategory = function(tab)
{
	return tab.id.slice(0,-4);
}

// Return the panel which belongs to the given tab
HappyTab.Widget.HappyPanels.prototype.getPanelForTab = function(tab)
{
	return document.getElementById(this.getTabCategory(tab) + "_panel");
}

HappyTab.Widget.HappyPanels.prototype.getContentPanelGroup = function()
{
	if (this.element)
	{
		var children = this.getElementChildren(this.element);
		if (children.length > 1)
			return children[1];
	}
	return null;
};

HappyTab.Widget.HappyPanels.prototype.getContentPanels = function()
{
	var panels = [];
	var pg = this.getContentPanelGroup();
	if (pg)
		panels = this.getElementChildren(pg);
	return panels;
};

HappyTab.Widget.HappyPanels.prototype.getHappyPanelCount = function(ele)
{
	return Math.min(this.getTabs().length, this.getContentPanels().length);
};

HappyTab.Widget.HappyPanels.addEventListener = function(element, eventType, handler, capture)
{
	try
	{
		if (element.addEventListener)
			element.addEventListener(eventType, handler, capture);
		else if (element.attachEvent)
			element.attachEvent("on" + eventType, handler);
	}
	catch (e) {}
};

HappyTab.Widget.HappyPanels.prototype.onTabClick = function(e, tab)
{
	if (selectedMod != "") {
		document.getElementById('FNImage_'+selectedMod).style.border="solid 1px #696969";
		selectedMod = '';
	}
	this.showPanel(tab);

	document.getElementById('ReloadTab').value=this.getTabCategory(tab);
	document.getElementById('ReloadMod').value='';
	document.getElementById('HistoReloadTab1').value=this.getTabCategory(tab);
	document.getElementById('HistoReloadMod1').value='';
	document.getElementById('HistoReloadTab2').value=this.getTabCategory(tab);
	document.getElementById('HistoReloadMod2').value='';
	window.scroll(0,0);
};

HappyTab.Widget.HappyPanels.prototype.onTabDblClick = function(e, tab)
{
	HappyReloadPage(this.getTabCategory(tab), null);
}

HappyTab.Widget.HappyPanels.prototype.onTabMouseOver = function(e, tab)
{
	this.addClassName(tab, this.tabHoverClass);
};

HappyTab.Widget.HappyPanels.prototype.onTabMouseOut = function(e, tab)
{
	this.removeClassName(tab, this.tabHoverClass);
};

HappyTab.Widget.HappyPanels.prototype.onTabFocus = function(e, tab)
{
	this.hasFocus = true;
	this.addClassName(this.element, this.tabFocusedClass);
};

HappyTab.Widget.HappyPanels.prototype.onTabBlur = function(e, tab)
{
	this.hasFocus = false;
	this.removeClassName(this.element, this.tabFocusedClass);
};

HappyTab.Widget.HappyPanels.ENTER_KEY = 13;
HappyTab.Widget.HappyPanels.SPACE_KEY = 32;

HappyTab.Widget.HappyPanels.prototype.onTabKeyDown = function(e, tab)
{
	var key = e.keyCode;
	if (!this.hasFocus || (key != HappyTab.Widget.HappyPanels.ENTER_KEY && key != HappyTab.Widget.HappyPanels.SPACE_KEY))
		return true;

	this.showPanel(tab);

	if (e.stopPropagation)
		e.stopPropagation();
	if (e.preventDefault)
		e.preventDefault();

	return false;
};

HappyTab.Widget.HappyPanels.prototype.preorderTraversal = function(root, func)
{
	var stopTraversal = false;
	if (root)
	{
		stopTraversal = func(root);
		if (root.hasChildNodes())
		{
			var child = root.firstChild;
			while (!stopTraversal && child)
			{
				stopTraversal = this.preorderTraversal(child, func);
				try { child = child.nextSibling; } catch (e) { child = null; }
			}
		}
	}
	return stopTraversal;
};

HappyTab.Widget.HappyPanels.prototype.addPanelEventListeners = function(tab, panel)
{
	var self = this;
	HappyTab.Widget.HappyPanels.addEventListener(tab, "click", function(e) { return self.onTabClick(e, tab); }, false);
	HappyTab.Widget.HappyPanels.addEventListener(tab, "dblclick", function(e) { return self.onTabDblClick(e, tab); }, false);
	HappyTab.Widget.HappyPanels.addEventListener(tab, "mouseover", function(e) { return self.onTabMouseOver(e, tab); }, false);
	HappyTab.Widget.HappyPanels.addEventListener(tab, "mouseout", function(e) { return self.onTabMouseOut(e, tab); }, false);

	if (this.enableKeyboardNavigation)
	{
		// XXX: IE doesn't allow the setting of tabindex dynamically. This means we can't
		// rely on adding the tabindex attribute if it is missing to enable keyboard navigation
		// by default.

		// Find the first element within the tab container that has a tabindex or the first
		// anchor tag.
		
		var tabIndexEle = null;
		var tabAnchorEle = null;

		this.preorderTraversal(tab, function(node) {
			if (node.nodeType == 1 /* NODE.ELEMENT_NODE */)
			{
				var tabIndexAttr = tab.attributes.getNamedItem("tabindex");
				if (tabIndexAttr)
				{
					tabIndexEle = node;
					return true;
				}
				if (!tabAnchorEle && node.nodeName.toLowerCase() == "a")
					tabAnchorEle = node;
			}
			return false;
		});

		if (tabIndexEle)
			this.focusElement = tabIndexEle;
		else if (tabAnchorEle)
			this.focusElement = tabAnchorEle;

		if (this.focusElement)
		{
			HappyTab.Widget.HappyPanels.addEventListener(this.focusElement, "focus", function(e) { return self.onTabFocus(e, tab); }, false);
			HappyTab.Widget.HappyPanels.addEventListener(this.focusElement, "blur", function(e) { return self.onTabBlur(e, tab); }, false);
			HappyTab.Widget.HappyPanels.addEventListener(this.focusElement, "keydown", function(e) { return self.onTabKeyDown(e, tab); }, false);
		}
	}
};

// Show the panel which belongs to the given tab
HappyTab.Widget.HappyPanels.prototype.showPanel = function(tab)
{
	var panel = this.getPanelForTab(tab)

	var tabs = this.getTabs();
	var panels = this.getContentPanels();

	var numHappyPanels = this.getHappyPanelCount();

	for (var i = 0; i < numHappyPanels; i++)
	{
		if (!tabs[i] || tabs[i] != tab)
		{
			if (tabs[i])
				this.removeClassName(tabs[i], this.tabSelectedClass);
				tabs[i].style.visibility = "visible";
			if (panels[i])
			{
				this.removeClassName(panels[i], this.panelVisibleClass);
				panels[i].style.visibility = "visible";
				panels[i].style.display = "none";
			}
		}
	}

	this.addClassName(tab, this.tabSelectedClass);
	this.addClassName(panel, this.panelVisibleClass);
	panel.style.display = "block";

	this.currentTab = tab
};

HappyTab.Widget.HappyPanels.prototype.attachBehaviors = function(scroll)
{
	var tabs = this.getTabs();
	var panels = this.getContentPanels();
	var panelCount = this.getHappyPanelCount();

	for (var i = 0; i < panelCount; i++)
		this.addPanelEventListeners(tabs[i], panels[i]);

	if(this.defaultTab)
		this.showPanel(this.defaultTab);
	else
		this.showPanel(tabs[0]);

	if(scroll != -1)
		goto(scroll);
	else if(this.defaultModule != '')
		goto(this.defaultModule);
};

function GetScrollY()
{
	if(typeof(window.pageYOffset) == 'number')
		return window.pageYOffset;
	else
		return document.body.scrollTop; /* IE? */
}

/* reload page and show given category+module */
function HappyReloadPage(category, module)
{
	var get = new Array();
	query = window.location.search.substring(1);
	kvpairs = query.split('&');
	for(i=0; i < kvpairs.length; ++i)
	{
		kv = kvpairs[i].split('=');
		get[kv[0]] = kv[1];
	}

	var params = new Array()
	if(get['date']) params.push('date=' + get['date'])
	if(get['time']) params.push('time=' + get['time'])
	params.push('expand=' + document.getElementById("ReloadExpand").value)
	params.push('t=' + category)
	if(module) params.push('m=' + module)

	url = window.location.protocol + '//' + window.location.hostname;
	if(window.location.port) url += ':' + window.location.port;
	url += window.location.pathname + '?';
	url += params.join('&');

	window.location.href = url;
}

/* function to set the right values before auto-reloading */
function HappyReload(time) {
	if(AutoReload) {
		refresh = setTimeout(function() {
			document.getElementById('ReloadManualRefresh').value = "";
			document.getElementById('ReloadScroll').value = GetScrollY();
			document.getElementById('ReloadForm').submit();
		}, time*1000);
	}
}

/* function to navigate the histo bar with the arrows */
function HappyHistoNav(direction, timestamp) {
	var step 		= document.getElementById('HistoStep').value;	
	var theStep  		= step.split(":");

	if((step.length != 5) || (theStep[0].length != 2) || (theStep[1].length != 2)) {
		document.getElementById('HistoStep').value="";
		document.getElementById('HistoForm1').submit();
		exit;
	}

	timestamp		= Number(timestamp);

	if(direction == "back") {
		timestamp 	= timestamp - (Number(theStep[0])*60 + Number(theStep[1]))*60;
	}
	if(direction == "fwd") {
		timestamp	= timestamp + (Number(theStep[0])*60 + Number(theStep[1]))*60;
	}

	var theDate 		= new Date(timestamp * 1000);

	var std = theDate.getHours();
	var min = theDate.getMinutes();
	var day = theDate.getDate();
	var mth = Number(theDate.getMonth());
	mth += 1;
	var stdPrint = ((std < 10) ? "0" + std : std);
	var minPrint = ((min < 10) ? "0" + min : min);
	var dayPrint = ((day < 10) ? "0" + day : day);
	var mthPrint = ((mth < 10) ? "0" + mth : mth);

	var theNewDate		= theDate.getFullYear() + "-" + mthPrint + "-" + dayPrint;
	var theNewTime		= stdPrint + ":" + minPrint;

	document.getElementById('HistoNavDate').value=theNewDate;
	document.getElementById('HistoNavTime').value=theNewTime;
	document.getElementById('HistoForm1').submit();
}
