/* Provide sorting functionality for a table */

function makeTableSortable(table_id, fetch_and_sort)
{
	// Allow table to be sorted by each column; make header clickable to do so.
	var table = document.getElementById(table_id).getElementsByTagName('tbody')[0];
	var rows = table.rows;

	var sortIndicator = document.createElement('span');
	sortIndicator.setAttribute('class', 'SortIndicator');
	var sortIndicatorText = document.createTextNode('');
	sortIndicator.appendChild(sortIndicatorText);

	for(var i = 0; rows[i]; ++i)
	{
		columns = rows[i].cells;

		if(rows[i].getAttribute('class') != 'TableHeader') continue;
		rows[i].setAttribute('class', 'TableHeader SortHeader');
		rows[i].sortHeader = true;

		for(var j = 0; columns[j]; ++j)
		{
			var fetchfunc = fetch_and_sort[j];
			var sortfunc = null;
			if(typeof(fetchfunc) == 'object')
			{
				fetchfunc = fetch_and_sort[j][0];
				sortfunc = fetch_and_sort[j][1];
			}

			// We need to use a "function maker function" since otherwise j and sortfunc would be bound into the closure by reference not by value
			columns[j].onclick = function(header, j, fetchfunc, sortfunc) {
				return function() {
					if(sortIndicator.parentNode == header)
					{
						tableRevert(table);
						if(sortIndicatorText.nodeValue == '\u00A0\u25BC')
							sortIndicatorText.nodeValue = '\u00A0\u25B2';
						else
							sortIndicatorText.nodeValue = '\u00A0\u25BC';
					}
					else
					{
						tableSort(table, j, fetchfunc, sortfunc);
						header.appendChild(sortIndicator);
						sortIndicatorText.nodeValue = '\u00A0\u25BC';
					}
				}
			}(columns[j], j, fetchfunc, sortfunc);

			columns[j].style.cursor = 'pointer';
		}
	}
}

// Sort table by column with the given index
function tableSort(table, index, fetchfunc, sortfunc)
{
	rows = table.rows;
	new_rows = [];
	for(var i = 0; rows[i]; ++i)
	{
		if(rows[i].sortHeader) continue;
		new_rows[new_rows.length] = [fetchfunc(rows[i].cells[index]), rows[i]];
	}

	if(sortfunc)
	{
		new_rows.sort(function(a,b) {
			return sortfunc(a[0],b[0]);
		});
	}
	else
	{
		new_rows.sort(function(a,b) {
			if(a[0] > b[0]) return -1;
			if(a[0] < b[0]) return 1;
			return 0;
		});
	}

	for(var i = 0; i < new_rows.length; ++i)
		table.appendChild(new_rows[i][1]);
}

function tableRevert(table)
{
	var new_rows = [];
	for(var i = 0; rows[i]; ++i)
	{
		if(rows[i].sortHeader) continue;
		new_rows[new_rows.length] = rows[i];
	}

	for(var i = 0; i < new_rows.length; ++i)
		table.appendChild(new_rows[new_rows.length - i - 1]);
}

function sortFetchText(cell)
{
	var result = '';
	for(var child = cell.firstChild; child; child = child.nextSibling)
		if(child.nodeType == 3)
			result += child.nodeValue;

	return result;
}

function sortFetchNumeric(cell)
{
	return parseFloat(sortFetchText(cell));
}

function sortFetchTime(cell)
{
	var days = 0;
	var secs = 0;

	var text = sortFetchText(cell);

	var num = text.indexOf('d');
	if(num != -1) days = parseInt(text.substr(0, num), 10);

	prevnum = num+1;
	num = text.indexOf(':', prevnum);
	if(num != -1) secs = parseInt(text.substr(prevnum, num - prevnum), 10);

	prevnum = num+1;
	num = text.indexOf(':', prevnum);
	if(num != -1) { secs *= 60; secs += parseInt(text.substr(prevnum, num - prevnum), 10); }

	prevnum = num+1;
	secs *= 60;
	secs += parseInt(text.substr(prevnum), 10);
	return days*86400+secs;
}
