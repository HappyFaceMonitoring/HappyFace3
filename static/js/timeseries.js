$(function() {
 
var common_constraints_enabled = true;
var curve_num = 0;

function check_common_constraint_condition()
{
    common_constraints_enabled = true;
    module = $("#curve_1_module_instance option:selected").val();
    subtable = $("#curve_1_subtable option:selected").val();
    for(var i=2; i<= curve_num; i += 1) {
        if($("#curve_"+i+"_module_instance option:selected").val() != module
            || $("#curve_"+i+"_subtable option:selected").val() != subtable) {
            common_constraints_enabled = false;
            break;
        }
    }
            
    if(common_constraints_enabled)
        $('#common_constraints_info').fadeOut(250);
    else
        $('#common_constraints_info').fadeIn(250);
}

function changed_subtable(e)
{
    curve = e.data.curve;
    var module = $("#"+curve+"_module_instance option:selected").val();
    var subtable = $("#"+curve+"_subtable option:selected").val();
   
    var html = "";
    for(var idx in module_plotable_vars[module][subtable]) {
        if(idx == 0)
            html += " <option selected=\"selected\">";
        else
            html += " <option>"
        html += module_plotable_vars[module][subtable][idx] + "</option>";
    }
    $("#"+curve+"_variable").empty().append(html);
    check_common_constraint_condition();
}

function changed_module(e)
{
    curve = e.data["curve"];
    var module = $("#"+curve+"_module_instance option:selected").val();
    var html = "";
    for(var subtable in module_plotable_vars[module]) {
        html += " <option>" + subtable + "</option>";
    }
    $("#"+curve+"_subtable").empty().append(html);
    changed_subtable(e);
    check_common_constraint_condition();
}

function changed_constraint_curve(e)
{
    constraint = e.data["constraint"];
    curve = $("#"+constraint+"_curve option:selected").val();
    if(curve == '')
        curve = "_1";
    var module = $("#curve"+curve+"_module_instance option:selected").val();
    var variable = $("#"+constraint+"_variable option:selected").val();
    var subtable = $("#curve"+curve+"_subtable option:selected").val();
    var html = "";
    for(var idx in module_all_vars[module][subtable]) {
        if(module_all_vars[module][subtable][idx] == variable)
            html += "<option selected='selected'>";
        else
            html += "<option>";
        html += module_all_vars[module][subtable][idx] + "</option>";
    }
    $("#"+constraint+"_variable").empty().append(html);
}

function add_curve(initial_mod, initial_table, initial_variable, initial_title) {
    curve_num += 1;
    html  = "<fieldset class=\"floating\" id='curve_" + curve_num +"' ><legend>Curve "+curve_num+"</legend>";
    html += "<legend><a id='curve_" + curve_num + "_remove' href=\"#\">Remove</a></legend>";
    html += " <p><label><span>Module</span><select id=\"curve_"+curve_num+"_module_instance\" name=\"curve_"+curve_num+"_module_instance\">";
    var first_mod = initial_mod;
    for(var mod in module_plotable_vars) {
        if(first_mod == "") first_mod = mod;
        if(first_mod == mod) html += " <option selected=\"selected\"";
        else html += " <option";
        html += " value=\"" + mod + "\">" + mod + " (" + module_types[mod] + ")</option>";
    }
    html += " </select></label></p>";
    html += " <p><label><span>Subtable</span><select id=\"curve_"+curve_num+"_subtable\" name=\"curve_"+curve_num+"_subtable\">";
    var found_subtable = false;
    for(var subtable in module_plotable_vars[first_mod]) {
        if(subtable == initial_table) {
            html += " <option selected=\"selected\">";
            found_subtable = true;
        }
        else
            html += " <option>";
        html += subtable + "</option>";
    }
    if(!found_subtable)
        initial_table = '';
    
    html += " </select></label></p>";
    html += " <p><label><span>Variable</span><select  id=\"curve_"+curve_num+"_variable\" name=\"curve_"+curve_num+"_variable\">";
    var plain_expression = false; // the expression is only a variable name
    for(var idx in module_plotable_vars[first_mod][initial_table]) {
        if(module_plotable_vars[first_mod][initial_table][idx] == initial_variable) {
            html += " <option selected=\"selected\">";
            plain_expression = true;
        }
        else
            html += " <option>";
        html += module_plotable_vars[first_mod][initial_table][idx] + "</option>";
    }
    html += " </select></label></p>";
    if(plain_expression)
        html += "<p><label><span>Math Expression</span><input id=\"curve_"+curve_num+"_expression\" type=\"edit\" name=\"curve_"+curve_num+"_title\" value=\"\"></label></p>";
    else
        html += "<p><label><span>Math Expression</span><input id=\"curve_"+curve_num+"_expression\" type=\"edit\" name=\"curve_"+curve_num+"_title\" value=\""+initial_variable+"\"></label></p>";
    html += " <p><label><span>Title</span><input id=\"curve_"+curve_num+"_title\" type=\"edit\" name=\"curve_"+curve_num+"_title\" value=\"";
    html += initial_title+"\"></label></p>";
    html += "</fieldset>";
    $("#curve_controls").before(html);
    var id = "curve_" + curve_num;
    $("#curve_"+curve_num+ "_remove").click(function() {$("#" + id).remove(); });
    $("#curve_"+curve_num+"_module_instance").change({'curve': "curve_"+curve_num}, changed_module);
    $("#curve_"+curve_num+"_subtable").change({'curve': "curve_"+curve_num}, changed_subtable);
    
    return false;
}

var constraint_id = 0;
function add_constraint(curve, variable, value) {
    console.debug("Constraint for curve "+curve);
    var id = "constraint_" + constraint_id;
    html  = "<fieldset id='" + id + "' class=\"floating\">";
    html += "<legend><a id='" + id + "_remove' href=\"#\">Remove</a></legend>";
    html += "<p><label><span>Apply to</span><select id='" + id + "_curve' name='" + id + "_curve'>";
    html += " <option value=''>(all)</option>";
    for(var i=1; i<= curve_num; i += 1) {
        if("_"+i == curve)
            html += " <option selected='selected' ";
        else
            html += " <option ";
        html += "value='_"+i+"'>Curve "+i+"</option>";
    }
    if(curve == "")
        curve = "_1";
    html += "</select></label></p>";
    html += "<p><label><span>Variable</span><select id='" + id + "_variable' name='" + id + "_variable'>";
    var module = $("#curve"+curve+"_module_instance option:selected").val();
    var subtable = $("#curve"+curve+"_subtable option:selected").val();
    for(var idx in module_all_vars[module][subtable]) {
        if(module_all_vars[module][subtable][idx] == variable)
            html += "<option selected='selected'>";
        else
            html += "<option>";
        html += module_all_vars[module][subtable][idx] + "</option>";
    }
    html += "</select></label></p>";
    html += "<p><label><span>Value</span><input type=\"edit\" id='" + id + "_value'";
    html += "name='" + id + "_value' value=\"" + value + "\" /></label></p>";
    html += "</fieldset>";
    $("#constraint_controls").before(html);
    $("#" + id + "_remove").click(function() { $("#" + id).remove(); });
    $("#" + id + "_curve").change({'constraint': id}, changed_constraint_curve);
    constraint_id += 1;
    
    return false;
}

$("#add_curve").click(function() {add_curve('', '', '', '') });
// $("#remove_curve").click(function() {
//     if(curve_num > 1) {
//         $("#curve_controls").prev().remove();
//         curve_num -= 1;
//     }
//     return false;
// });
$("#add_constraint").click(function() {add_constraint('', '', '') });

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

$("#update_plot").click(function() {
    var html = "";
    for(var i=1; i <= curve_num; i++)
    {	
        var id_particle = "#curve_"+i;
        var mod = $(id_particle+"_module_instance option:selected").val();
        var table = $(id_particle+"_subtable option:selected").val();
	var expression;
	var variable = $(id_particle+"_variable option:selected").val();
        var title = $(id_particle+"_title").val();
	try{
	    expression = $(id_particle+"_expression").val().replace(",", "\\,");
	    if(expression.length > 0)
            variable = expression
	    html += "<input type=\"hidden\" name=\"curve_"+i+"\" value=\""+mod+","+table+","+variable+","+title+"\" />\n";
	}
	catch(err){
	    //just skip
	}
    }
    $("#common_constraints_form fieldset").each(function(idx) {
        var constraint_id = "#"+$(this).attr('id');
        var curve = $(constraint_id + "_curve option:selected").val();
        var variable = $(constraint_id + "_variable option:selected").val();
        var value = $(constraint_id + "_value").val();
        html += "<input type=\"hidden\" name=\"filter"+curve+"\" value=\""+variable+","+value+"\" />\n";
    });
    $("#plot_inputs").empty().append(html);
    $("#plot_form").submit();
    return false;
});


for(var idx in curves) {
    add_curve(curves[idx][0], curves[idx][1], curves[idx][2], curves[idx][3]);
}

if(curve_num == 0)
    add_curve('', '', '', '');

for(var curve in constraints)
    for(var idx in constraints[curve])
        add_constraint(curve, constraints[curve][idx][1], constraints[curve][idx][2]);
});