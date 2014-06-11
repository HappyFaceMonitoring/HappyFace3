$(function() {
    // 
    $("[id$='_info_link']").click(function() {
        var patt=new RegExp('_link$');
        var box_id = '#'+$(this).attr('id').replace(patt, '_box')
        $(box_id).toggle()
        if($(this).text().search("Show") != -1)
            $(this).text("Hide module information")
        else
            $(this).text("Show module information")
        return false;
    });
});