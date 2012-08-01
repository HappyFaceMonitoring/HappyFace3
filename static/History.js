
$(function() {
    function moveInHist(direction) {
        var dateString = $('#HistoNavDate').val() + ' ' + $('#HistoNavTime').val();
        var pattDate = new RegExp('([0-9]{4})-([0-9]{1,2})-([0-9]{1,2}) ([0-9]{1,2}):([0-9]{1,2})');
        var pattHistoStep = new RegExp('([0-9]+):([0-9]+)');
        
        // build date object
        match = pattDate.exec(dateString);
        // f*** JavaScript, month starts at 0
        date = new Date(match[1], match[2]-1, match[3], match[4], match[5], 0, 0);
        match = pattHistoStep.exec($('#HistoStep').val());
        var timeDiff = (match[1]*3600e3 + match[2]*60e3);
        
        // create new date
        var newDate = new Date(date.getTime() + timeDiff*direction);
        
        // update form, get Date() is form 1-31 unlike getMonth...
        $('#HistoNavDate').val(newDate.getFullYear()+'-'+(newDate.getMonth()+1)+'-'+(newDate.getDate()));
        $('#HistoNavTime').val(newDate.getHours()+':'+newDate.getMinutes());
        $('#HistoForm1').submit()
    }
    $('#HistoBack').click(function() {
        moveInHist(-1);
    });
    
    $('#HistoFwd').click(function() {
        moveInHist(1);
    });
});