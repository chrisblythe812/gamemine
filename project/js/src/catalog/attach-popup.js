$.fn.attachPopup = function (popupSelector, config) {
	config = config || {};
	
	var 
	$link = $(this),
	$popup = $(popupSelector),
	timer,
	
	beforeOpen = config.beforeOpen || function() { return true; },
	afterClose = config.afterClose || function() { return true; },
	timeout = config.timeout || 1000,
	
	resetTimer = function () {
		clearTimeout(timer);
	},
	
	close = function () {
		resetTimer();
		$popup.hide();
		afterClose($link); 
	},
	
	delayedClose = function (){
		timer = setTimeout(close, timeout);
	},
	
	open = function() {
		$popup.show();
	};
	
	$popup
		.hide()
		.css('position', 'absolute')
		.mouseenter(resetTimer)
		.mouseleave(delayedClose);
	
	$popup.find('.popop-title a').click(function () {
		close();
		return false;
	});
	
	$link.click(function () {
		var res = beforeOpen($link, $popup);
		if (res != undefined && !res)
			return false;
		
		open();	
		return false;
	});
	
	return $(this);
};
