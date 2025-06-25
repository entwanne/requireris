$(document).ready(function() {
    var timer = setInterval(refresh, 1000);
    refresh();
    //$("#delete").modal('show');
})
function refresh(data) {
    $.getJSON('/json/timer', function(data) {
	$("#timer").html(data.validity);
	});
    $.getJSON('/json/get/' + pattern, function(data) {
	var items = [];
	$.each(data, function(i, entry) {
	    items.push('<tr><td>' + entry.user + '</td><td>' + entry.auth + '</td><td><span class="btn" onclick="deleteEntryConfirmation(\'' + entry.user + '\');"><i class="icon-remove"></i></span></td></tr>');
	});
	$("#entries").html(items.join(''));
	});
}

function manageError(error)
{
    if (error)
	{
	    box = '<div class="alert alert-error"><button type="button" class="close" data-dismiss="alert">&times;</button>' + error + '</div>';
	    $("#content").prepend(box);
	}
}

function addEntry()
{
    var user = $("#add-user").val();
    var key = $("#add-secret-key").val();
    $.get('/add/' + user + '/' + key, manageError);
    $("#add-user").val('');
    $("#add-secret-key").val('');
    refresh();
}

var deleting_user;

function deleteEntryConfirmation(user)
{
    deleting_user = user;
    $("#delete").modal('show');
    $("#delete-entry").html(user);
}

function deleteEntry()
{
    $.get('/del/' + deleting_user, manageError);
    refresh();
}
