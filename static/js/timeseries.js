$(function() {

function changed_subtable(e)
{
    curve = e.data.curve;
    var module = $("#"+curve+"_module_instance option:selected").val();
    var subtable = $("#"+curve+"_subtable option:selected").val();
   
    var html = "";
    for(var idx in modules[module][subtable]) {
        if(idx == 0)
            html += " <option selected=\"selected\">";
        else
            html += " <option>"
        html += modules[module][subtable][idx] + "</option>";
    }
    $("#"+curve+"_variable").empty().append(html);
}

function changed_module(e)
{
    curve = e.data["curve"];
    var module = $("#"+curve+"_module_instance option:selected").val();
   
    var html = "";
    for(var subtable in modules[module]) {
        html += " <option>" + subtable + "</option>";
    }
    $("#"+curve+"_subtable").empty().append(html);
    changed_subtable(e);
}

var curve_num = 0;
function add_curve() {
    curve_num += 1;
    html  = "<fieldset class=\"floating\"><legend>Curve "+curve_num+"</legend>";
    html += " <p><label><span>Module</span><select id=\"curve_"+curve_num+"_module_instance\" name=\"curve_"+curve_num+"_module_instance\">";
    var first_mod = "";
    for(var mod in modules) {
        if(first_mod == "")
            first_mod = mod;
        html += " <option>" + mod + "</option>";
    }
    html += " </select></label>";
    html += " <label><span>Subtable</span><select id=\"curve_"+curve_num+"_subtable\" name=\"curve_"+curve_num+"_subtable\">";
    for(var subtable in modules[first_mod]) {
        html += " <option>" + subtable + "</option>";
    }
    html += " </select></label>";
    html += " <label><span>Variable</span><select  id=\"curve_"+curve_num+"_variable\" name=\"curve_"+curve_num+"_variable\">";
    for(var idx in modules[first_mod]['']) {
        html += " <option>" + modules[first_mod][''][idx] + "</option>";
    }
    html += " </select></label>";
    html += " <label><span>Title</span><input type=\"edit\" name=\"curve_"+curve_num+"_title\"></label></p>";
    html += "</fieldset>";
    $("#curve_controls").before(html);
    $("#curve_"+curve_num+"_module_instance").change({'curve': "curve_"+curve_num}, changed_module);
    $("#curve_"+curve_num+"_subtable").change({'curve': "curve_"+curve_num}, changed_subtable);
    
    return false;
}

$("#add_curve").click(add_curve);
$("#remove_curve").click(function() {
    if(curve_num > 1) {
        $("#curve_controls").prev().remove();
        curve_num -= 1;
    }
    return false;
});

$("#show_curve_form").click(function() {
    $("#curve").slideDown();
    $("#show_curve_form").hide();
    $("#hide_curve_form").show();
    return false;
});
$("#hide_curve_form").click(function() {
    $("#curve").slideUp();
    $("#show_curve_form").show();
    $("#hide_curve_form").hide();
    return false;
});

add_curve();

});