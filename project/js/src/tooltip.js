function setupCCVTooltip($link, $hint, $cardtype) {
  $link.click(function(){return false;}).tooltip({
	relative: true,
    onBeforeShow: function() {
	  var cardtype = $cardtype.val();
      if (cardtype == 'visa' || cardtype == 'master-card') {
        $hint.find('.picture').css('background', '0 0 url(' + siteConfig.mediaUrl + 'img/ccv-explained.png)');
        $hint.find('.description').text('The CVV number is the last three digits listed in the signature area on the back of the card.');
      } else if (cardtype == 'american-express') {
        $hint.find('.picture').css('background', '0 -69px url(' + siteConfig.mediaUrl + 'img/ccv-explained.png)');
        $hint.find('.description').text('The CVV number is listed above the credit card number on the front of the card.');
      } else {
        return false;
      }
    }
  });
}
