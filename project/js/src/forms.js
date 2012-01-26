var Forms = {
	prepare_error_message: function () {
		var errorMessage = $('.errors-message');
		errorMessage
			.wrapInner('<div class="errors-message-wrapper"></div>')
			.wrapInner('<div class="errors-message-wrapper-outer"></div>')
			.wrapInner('<div class="errors-message-wrapper-outer-1"></div>')
			.prepend('<div class="errors-message-top"><div class="errors-message-top-left"></div><div class="errors-message-top-right"></div></div>')
			.append('<div class="errors-message-bottom"><div class="errors-message-bottom-left"></div><div class="errors-message-bottom-right"></div></div>');
	}
};

jQuery(document).ready(function () {
	$.fn.prepareFormWidgets();
	
	$.fn.delayChange = function (callback, timeout) {
		timeout = timeout || 500;
		
		var
		timer,
		input = $(this),
		value = input.val(),
		resetTimeout = function() {
			clearTimeout(timer);
		},
		runCallback = function() {
			if (value == input.val()) {
				return;
			}
			value = input.val();
			callback.apply(input);
		},
		delayCallback = function () {
			timer = setTimeout(runCallback, timeout);
		};
		
		input.keyup(function () {
			resetTimeout();
			delayCallback();
		});
		
		return input;
	};
	
	Forms.prepare_error_message();	

  function selectionChanged(sel) {
    $(this).prev().find('span').text($(this).find('option:selected').text());
  }

  $.fn.setupSelect = function (klass) {
    klass = klass || '';
    this.wrap('<div class="select ' + klass +'"><div class="select-inner"></div></div>').each(function(){
      $(this).parent().prepend('<div class="text"><div class="text-wrapper"><span></span></div></div>');
      selectionChanged.call(this);
    }).change(selectionChanged);
    if ($.browser.msie) this.keyup(selectionChanged);
  }

  $.fn.updateValue = function () {
	  this.change();
  }
});

