$(function () {
	$('[data-toggle="tooltip"]').tooltip();
	$('[data-toggle="popover"]').popover();
	
	window.noCollapse = function(e) {
		e.stopPropagation();
	};
});