jQuery.fn.topPopup = function (link) {
	var popup = $(this);
	if (popup.size() == 0)
		return;

	var 
	timer,
	showPopup = function () {
		popup.show();
		popup.animate({
			top: '0px'
		});
	},
	hidePopup = function () {
		clearTimeout(timer);
		popup.animate({
			top: -popup.height()
		}, popup.hide);
	};
	
	popup
		.css('top', -popup.height())
		.mouseleave(function () {
			// timer = setTimeout(hidePopup, 1000);
		})
		.mouseenter(function () {
			clearTimeout(timer);
		})
		.find('.top-popup-header a.close-action').click(function () {
			hidePopup();
			return false;		
		});
	
	$(link).click(function () {
		showPopup();
		return false;		
	});
};
