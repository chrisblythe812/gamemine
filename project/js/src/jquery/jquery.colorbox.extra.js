(function ($) {

	var 
	colorboxPublicMethods = $.fn['colorbox'];
	
	colorboxPublicMethods.setContent = function (content) {
		$('#cboxLoadedContent').empty();
		$('#cboxLoadedContent').append('<div>' + content + '</div>');
		$.fn.colorbox.resize();
	};

}(jQuery));
