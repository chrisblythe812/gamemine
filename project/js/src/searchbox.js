(function ($, window) {

$.fn.searchbox = function(empty_text) {
  var $this = $(this);
  
  $this.attr('_empty_text', empty_text);
  if ($this.val() == '')
  {
    $.fn.wipeSearchBox.apply($this, []);
  }
  
  $this   
    .focus(function () {
      var v = $this.val();
      $this.removeClass('empty');
      if (v == empty_text)
        $this.val('');
    })
    .blur(function () {
      var v = $this.val();
      if (v == '')
        $.fn.wipeSearchBox.apply($this, []);
    });
  return $this;
};

$.fn.wipeSearchBox = function () {
  input = $(this); 
  input.val(input.attr('_empty_text') || '').addClass('empty');
  return input;
};

}(jQuery, this));
