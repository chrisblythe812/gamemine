jQuery(document).ready(function () {

  function showSpacefighters() {
    var cb = $('#colorbox'),
    cbOffset = cb.offset();

    function show_obj(obj, ox, oy) {
      obj = $(obj);
      if (obj.size() != 0) {
        obj.detach();
        $('body').append(obj);
        obj.css({
          top: cbOffset.top + oy,
          left: cbOffset.left + ox
        });
      }
    }

    show_obj('#wizard-starfighters', cb.width() - 257, -67);
    show_obj('#wizard-subs-decor-1', 7, cb.height() - 88);
    show_obj('#wizard-subs-decor-2', 210, -2);
    show_obj('#wizard-subs-decor-3', 520, cb.height() - 70);
    show_obj('#wizard-subs-decor-4', 679, 100);
  }

  function hideSpacefighters() {
    $('#wizard-starfighters').remove();
    $('#wizard-subs-decor-1').remove();
    $('#wizard-subs-decor-2').remove();
    $('#wizard-subs-decor-3').remove();
    $('#wizard-subs-decor-4').remove();
  }

  $.fn.setWizardContent = function(data) {
    hideSpacefighters();
    var w = $(data).attr('width');
    if (w) {
      $.fn.colorbox.resize({width: w});
      $.fn.colorbox.setContent(data);
    }
    else {
      $.fn.colorbox.setContent(data);
      $.fn.colorbox.resize();
    }
    prepareAjaxForm();
    prepareAjaxLinks();
    showSpacefighters();
  }

  function getForm() {
    return $('#cboxLoadedContent form');
  }

  function prepareAjaxForm() {
    var form = getForm();
    form.submit(function(){
      var validate = $(this).get(0).validate;
      if (!validate || validate()) {
	$(this).ajaxSubmit(ajaxFormOptions);
        hideSpacefighters();
      }
      return false;
    });
    form.find('.wizard-back-button').click(function () {
      form.get(0).validate = null;
      form.append('<input type="hidden" name="__backward" value="true" />');
    });
    // Forms.prepare_error_message();
    $.fn.prepareLinks();
    $.fn.prepareFormWidgets(getForm());
    Helpers.boxed(form.find('.boxed'));

    var cb = $('#colorbox');
    cb.removeClass('refresh-after-dialog-close');
    if ($('#cboxLoadedContent .refresh-after-dialog-close').size())
      cb.addClass('refresh-after-dialog-close');
  }

  function prepareAjaxLinks() {
    $('.wizard-navigate-button').click(function(){
      $.get($(this).attr('href'), function(data){
	$.fn.setWizardContent(data);
      });
      return false;
    });
  }

  var ajaxFormOptions = {
    'beforeSubmit': function () { getForm().disableForm(); },
    'success': function (response, status, xhr, form) {
      if (status != 'success')
      {
	getForm().enableForm();
	return;
      }
      if (response.redirect_to) {
	window.location = response.redirect_to;
      }
      else if (response.goto_url) {
	$.fn.openWizardByUrl(response.goto_url);
      }
      else if (response.close) {
	$.fn.colorbox.close();
      }
      else {
        if (response.form)
	  $.fn.setWizardContent(response.form);
        else
          $.fn.setWizardContent(response);
      }
    }
  };

  var getColorBoxOptions = function (onClose) {
    onClose = onClose || function (element) {
      if ($('#colorbox').hasClass('refresh-after-dialog-close') || $(this).hasClass('refresh-after-dialog-close')) {
	window.location = window.location;
      }
      //window.location = window.location;
    };
    return {
      initialWidth: 200,
      initialHeight: 100,
      overlayClose: false,
      onComplete: function() {
        var cb = $('#colorbox');
        if ($(this).hasClass('v2')) {
          cb.addClass('v2');
        } else {
          cb.removeClass('v2');
        }
        prepareAjaxForm();
  	prepareAjaxLinks();

	showSpacefighters();
      },
      onClosed: function(){
	hideSpacefighters();
	onClose.apply(this, []);
      }
    };
  }

  $.fn.getColorBoxOptions = getColorBoxOptions;

  $.fn.prepareLinks = function () {
    $('a.link-dialog:not(.prepared-link-dialog)').each(function () {
      $(this).addClass('prepared-link-dialog').click(hideSpacefighters).colorbox(getColorBoxOptions());
    });
    $('form.link-dialog:not(.prepared-link-dialog-form)').each(function () {
      $(this).submit(function(){
        // Validates then invokes ajax wizard (colorbox)
	var form = $(this).get(0),
	$form = $(this);
	var validate = form.validate;
	if (!validate || validate()) {
	  var o = getColorBoxOptions();
	  o.href = $form.attr('action');
	  o.post_data = $form.serializeArray();
	  $.colorbox(o);
	}
	return false;
      }).addClass('prepared-link-dialog-form');
    });

    $('a.dialog-close-button, a.close-button').click(function () {
      $.fn.colorbox.close();
      return false;
    });
  };

  $.fn.prepareLinks();

  $.fn.openWizardByUrl = function (href, onClose) {
    var o = getColorBoxOptions(onClose);
    o.href = href;
    $.colorbox(o);
  }

  $('.link-dialog.autotrigger').click();
});
