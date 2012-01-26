var Helpers = {
  boxed: function (object, suffix) {
    suffix = suffix || 'boxed';
    object
      .wrapInner('<div class="' + suffix + '-wrapper"></div>')
      .wrapInner('<div class="' + suffix + '-wrapper-outer"></div>')
      .wrapInner('<div class="' + suffix + '-wrapper-outer-1"></div>')
      .prepend('<div class="' + suffix + '-top"><div class="' + suffix + '-top-left"></div><div class="' + suffix + '-top-right"></div></div>')
      .append('<div class="' + suffix + '-bottom"><div class="' + suffix + '-bottom-left"></div><div class="' + suffix + '-bottom-right"></div></div>');
  }	
};

jQuery(document).ready(function() {
  
  var ul = $('#content ul.heading');
  
  ul.find('li')
    .wrapInner('<div class="wrapper-inner">')
    .wrapInner('<div class="wrapper">');
  ul.find('.wrapper')
    .prepend('<div class="left-decoration">')
    .append('<div class="right-decoration">');
  
  ul.wrap('<div class="ul-heading">');
  ul.parent()
    .prepend('<div class="left-decoration">')
    .append('<div class="right-decoration">');
  
  $('#header-search-box input[type=text]').searchbox('Search');
  $('.what-is-my-game-worth-page .search-area input[type=text]').searchbox('Title, Publisher, UPC');
  
  $('#header-user-popup').topPopup('#header-user-block-profile');
  $('#header-login-popup').topPopup('#header-user-block-login');
  $('#header-signup-popup').topPopup('#header-user-block-signup');
  
  $('#page-heading').prepend('<div id="page-heading-decor" />');
  
  $('.autoboxed').each(function () { Helpers.boxed($(this)); });
});
