(function ($, window) {
    var 
    defaults = {
        showDelay: 1000,
        hideDelay: 1000,
        callback: function (){}     
    },
	activeElement,
    $hint,
    $hintTop,
    $hintBottom,
    $content,

    publicMethod;

    function init() {
        if ($hint)
            return;
        $hint = $('<div id="details-hint" class=""><div id="details-hint-top"></div><div id="details-hint-middle"></div><div id="details-hint-bottom"></div><div id="details-hint-content-wrapper"><div id="details-hint-content" class="empty"></div></div></div>')
        .hide();
        $hintTop = $hint.find('#details-hint-top');
        $hintBottom = $hint.find('#details-hint-bottom');
		$content = $hint.find('#details-hint-content');
        $('body').append($hint);
    }

    function displayContent(the_content) {
		$content.empty().removeClass('empty').append(the_content);
    }

    function launch(element_to_launch) {
		activeElement = element_to_launch;
        var 
		element = element_to_launch,
        element_position = element.position(),
        element_width = element.width(),
        element_height = element.height(),
        hint_width = $hint.width(),
        hint_height = $hint.height(),
        top = element_position.top + element_height / 2 - 230,
        left = element_position.left + element_width,
        klass = '';

        var $window = $(window);
        if (left + hint_width > $window.width()) {
            klass = 'alternate';
            left = element_position.left - hint_width + 10;
        }
		else 
		  left -= 10;

        if (top + hint_height > $window.scrollTop() + $window.height()) {
            top = $window.scrollTop() + $window.height() - hint_height;
        }
        else if (top < $window.scrollTop()) {
            top = $window.scrollTop();
        } 

        $hint.css({
            top: top,
            left: left
        }).removeClass('alternate alternate-arrow').addClass(klass);
        
        var point_x = element_position.top - top + element_height / 2;

        if (point_x < 17) {
          point_x = 17; 
        } 
        else if (point_x > 279) {
            $hint.addClass('alternate-arrow');
            if (point_x > 370)
                point_x = 370;
            point_x -= 90;
        }
        
        $hintTop.css({
            height: point_x
        });
        $hintBottom.css({
            height: hint_height - 114 - point_x
        });
        
        $hint.show();
		
		var data = element.data('details_hint');
        if (data._cache !== undefined) {
            displayContent(data._cache);
        }
        else {
            var content = data.callback.apply(element, []);
            if (content)
                displayContent(content);
        }
    }

    publicMethod = $.fn['details_hint'] = $['details_hint'] = function(options, callback){
        var $this = $(this);
        
        if (!$this[0] && $this.selector) {
            return $this;
        }
        
        options = defaults;
        
        $this.each(function (index, element) {
            element = $(element);
            var 
            data = $.extend({}, element.data('details_hint') || defaults, options),
            showTimeout;

            data.callback = callback || data.callback;

            element
                .hover(function () {
                    showTimeout = setTimeout(function(){
                        launch(element);
                    }, data.showDelay);
                }, function () {
                    clearTimeout(showTimeout);
                    publicMethod.close();
                })
                .attr('title', '')
                .data('details_hint', data);
        });
        return $this;
    };
    
    publicMethod.close = function () {
        $hint.hide();
		$content.empty().addClass('empty');
    };
    
    publicMethod.setContent = function(element, content){
		if (!element || !activeElement)
		  return;
        element = $(element);
        var data = element.data('details_hint');
        data._cache = content;
        element.data('details_hint', data);
		if (activeElement[0] === element[0]) {
			displayContent(content);
		}
    }; 
    
    $(document).ready(init);

}(jQuery, this));
