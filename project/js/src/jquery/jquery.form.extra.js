(function($) {

	function setFormState(form, state)
	{
		// TODO: It would be great to remember state before disabling and 
		// restore it after them become enabled
		form.find('input, select, textarea, button').attr("disabled", !state);		
	}
	
	$.fn.enableForm = function () {
		setFormState(this, true);
	};
	
	$.fn.disableForm = function () {
		setFormState(this, false);
	};
	
	$.fn.prepareFormWidgets = function (selector) {
		selector = selector || 'body';

		function div(cl) {
			return '<div class="' + cl + '" />';
		}
		
		function wrap_input(index, input) {
			if ($(input).hasClass('wrapped-input')) {
				return;
			}
			$(input).addClass('wrapped-input');
			var input_wrapper = $(input).wrap(div("input-wrapper")).parent();
			input_wrapper.prepend(div("icon"));
			var wrapper = input_wrapper.wrap(div("input form-textbox-wrapper")).parent();
			wrapper.append(div("right-box"));
		}	
		
	    $(selector).find('input[type=text]:not(.do_not_wrap), input[type=password], .readonly-textbox').each(wrap_input);
		
		$('textarea').each(function (index, textarea) {
            textarea = $(textarea);
            if (!(/^[0-9]+$/.test(textarea.attr("maxlength"))))
                return;

            var len = parseInt(this.getAttribute("maxlength"), 10);
            var rest = this.getAttribute("id-for-rest");
            if (rest) rest = $('#' + rest);
            var func = function() {
        		var r = len - this.value.length;
            	if (rest) rest.text(r < 0 ? 0 : r);
                if (r < 0) {
					this.value = this.value.substr(0, len);
					return false;
				}
            } 

            textarea.keyup(func).blur(func);
        });
	};

})(jQuery);
