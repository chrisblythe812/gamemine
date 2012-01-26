var catalogItem = {
  init: function () {
    catalogItem.prepare_also_on_urls();
    catalogItem.prepare_get_more_description_url();
    catalogItem.prepare_get_more_reviews_url();
    catalogItem.update_member_reviews_list();
    catalogItem.prepare_screenshots();
    catalogItem.update_review_links();

    $('#catalog-item-sidebar .screenshots ul').jcarousel({itemFallbackDimension: 40});
  },

  update_review_links: function (the_item) {
    var item = the_item;
    $('a.review-vote-button').click(function () {
      var href = $(this).attr('href');
      jQuery.get(href);
      return false;
    });

    //		$('a.goto-write-review').click(function () {
    //            $('body').animate({scrollTop: $('#write-review').attr('offsetTop')}, 500);
    //			return false;
    //		});

    if (item) {
      var a = $('.member-reviews-list-actions a.get-more'),
      href = a.attr('href');
      if (!href)
        return;
      var parts = href.split('/');
      href = item.url + parts[parts.length - 2] + '/';
      a.attr('href', href);
    }

    $('a.reviews-filter').each(function () {
      var a = $(this),
      href = a.attr('href');
      if (item) {
	var parts = href.split('/');
	href = item.url + parts[parts.length - 2] + '/';
	a.attr('href', href);
      }
      a.unbind('click');
      a.click(function () {
	jQuery.getJSON(href, function (data, status) {
	  if (status != 'success')
	    return;
	  var reviews = $('.member-reviews-list');
	  reviews.empty();
	  for (var i in data.reviews) {
	    reviews.append(catalogItem.create_review(data.reviews[i]));
	  }
	  catalogItem.update_review_links();
	  if (!data.has_more_reviews){
	    $('.member-reviews-list-actions a.get-more').hide();
	  }
	  else{
	    $('.member-reviews-list-actions a.get-more').show();
	  }
	});
	return false;
      });
    });
  },

  update_member_reviews_list: function () {
    $('.member-reviews-list.not-authenticated li').fadeTo(0, 0.3);
  },

  prepare_also_on_urls: function () {
    $('.catalog-item-details .catalog-item-also-on a').each(function (index, item) {
      $(item).click(function(){
	var a = $(this),
	href = a.attr('href');
	jQuery.getJSON(href + 'details/', function (item, status) {
	  if (status == 'success')
	    catalogItem.display_catalog_item(item);
	});
	return false;
      });
    });
  },

  prepare_get_more_description_url: function () {
    $('.catalog-item-description .get-more').click(function () {
      var a = $(this),
      href = a.attr('href');
      jQuery.getJSON(href, function (data, status) {
	if (status == 'success')
	{
	  a.hide();
	  var div = $('.catalog-item-muze-description').empty().hide();
	  if (data.description.expanded) {
	    div.append(data.description.expanded).slideDown();
	  }
	}
      });
      return false;
    });
  },

  create_review: function (review) {
    var res =
      $($.LI({Class: 'member-review', id: 'member-review-' + review.id},
	     $.DIV({Class: 'review-usericon'},
		   $.IMG({src: review.user.icon, width: '60', height: '60'})
		  ),
	     $.DIV({Class: 'review-content'},
		   $.DIV({Class: 'review-comment'}),
		   $.DIV({Class: 'review-meta'},
			 $.DIV({Class: 'catalog-item-rating'},
			       $.DIV({Class: 'catalog-item-rating-content'}, review.ratio + '\u00a0of\u00a0100')
			      ),
			 $.DIV({Class: 'review-author'},
			       review.posted_by
			      )
			)
		  )
	    ));
    if (!review.own_review) {
      res.find('.review-meta').append(
        $.DIV({Class: 'review-helpful'},
              'Was this helpful?', ' ',
              $.A({Class: 'review-vote-button small-yes-button', href: '/Review/Vote/' + review.id + '/yes/'}, 'Yes'), ' ',
              $.A({Class: 'review-vote-button small-no-button', href: '/Review/Vote/' + review.id + '/no/'}, 'No')
             ));
    }
    if (review.title)
      res.find('.review-content').prepend('<h4>' + review.title + '</h4>');
    res.find('.review-comment').append('<p>' + review.comment + '</p>');
    res.find('.catalog-item-rating-content').css({width: review.ratio + '%'});
    return res;
  },

  prepare_get_more_reviews_url: function () {
    $('.member-reviews-items .member-reviews-list-actions .get-more').click(function () {
      var a = $(this),
      href = a.attr('href'),
      id = $('.member-reviews-list li:last').attr('id').split('-');
      id = id[id.length - 1];
      jQuery.getJSON(href, {'id': id}, function (data, status) {
	if (status != 'success')
	  return;
	var reviews = $('.member-reviews-list');
	for (var i in data.reviews) {
	  reviews.append(catalogItem.create_review(data.reviews[i]));
	}
	catalogItem.update_review_links();
	if (!data.has_more_reviews){
	  a.hide();
	}
	else{
	  a.show();
	}
      });
      return false;
    });
  },

  set_review_count: function (count) {
    $('.catalog-item-details .review-count').text(count);
  },

  set_item_ratio: function (item) {
    var $d = $('.catalog-item-details'),
    $s = $('#catalog-item-sidebar');

    $('.catalog-item-stars .rating').removeClass('stars1 stars2 stars3 stars4 stars5').addClass('stars' + parseInt(item.ratio.percents / 20));
    $('.my.rating').removeClass('stars0 stars1 stars2 stars3 stars4 stars5').addClass('stars' + item.my_rate);

    $('.rating').each(function () {
      $(this).find('a').each(function (index, a) {
	$(a).attr('href', '/Rate/' + item.id + '/' + (index + 1) + '/');
      });
    });

    var rating = $d.find('.catalog-item-stars .catalog-item-rating-content')
      .text('Ratio: ' + item.ratio + '\u00a0of\u00a0100');
    var w = item.ratio.percents / 100 * rating.parent().width();
    rating.animate({width: w});

    var $r = $s.find('.overall-rating-content');
    $r.find('.overall-rating-value').text(item.ratio.ratio);

    var rating_count;
    if (item.votes.amount == 0)
      rating_count = 'No review found';
    else if (item.votes.amount == 1)
      rating_count = 'Based on 1 review';
    else
      rating_count = 'Based on ' + item.votes.amount + ' reviews';
    $r.find('.overall-rating-count').text(rating_count);
    $('.voters-amount').text(item.votes.amount);

    function setOverallRating($rd, stars, value)
    {
      var p = 1.0 * value / (item.votes.amount || 1);
      var bar = $rd.find('.overall-rating-details-' + stars);
      var w = $rd.find('.ratio-bar').width() * p;
      var rdc = bar.find('.ratio-bar-content').animate({width: w});
      bar.find('span').text(value);
    }
    var $rd = $r.find('.overall-rating-details');
    for (var index in item.votes.details)
      setOverallRating($rd, 5 - index, item.votes.details[4 - index]);
  },

  update_main_item_properties: function (item) {
    var $d = $('.catalog-item-details'),
    $p = $d.find('.catalog-item-params'),
    setValue = function (t, v) {
      $p.find('.catalog-item-params-' + t + ' span').empty().append(v);
    };


    if (item.publisher.name)
      setValue('publisher', '<a href="' + item.publisher.url + '">' + item.publisher.name + '</a>');
    else
      setValue('publisher', '--');

    setValue('platform', '<a href="' + item.platform.url + '">' + item.platform.name + '</a>');
    setValue('release', item.release_date);

    if (item.genres.length > 0) {
      var val = '';
      for (var i in item.genres) {
	if (i != 0)
	  val += ', ';
	var g = item.genres[i];
	val += '<a href="' + g.url + '">' + g.name + '</a>';
      }
      setValue('genres', val);
    }
    else
      setValue('genres', '--');

    setValue('esrb', item.esrb || '--');
    setValue('players', item.number_of_players || '--');
    setValue('online-players', item.number_of_online_players || '--');

    if (item.tags.length > 0) {
      var val = '';
      for (var i in item.tags) {
	if (i != 0)
	  val += ', ';
	var t = item.tags[i];
	val += '<a href="' + t.url + '">' + t.name + '</a>';
      }
      setValue('tags', val);
    }
    else
      setValue('tags', '--');
  },

  display_screen_shots: function (screenshots, media_details) {
    var container = $('#catalog-item-sidebar .screenshots').empty(),
    div,
    mediaUrl = catalogConfig.mediaUrl;
    if (screenshots.length) {
      container.show();
      div = $(
	$.DIV({id: "id_screenshots_inner"},
	      $.IMG({
		Class: 'main-image',
		width: 330,
		height: 200,
		src: mediaUrl + 'media/thumbs/muze/330x200/' + screenshots[0].file_name,
		title: screenshots[0].caption
	      }),
	      $.UL({})));
      if (media_details) {
	div.find('.main-image').after('<a href="' + media_details + '" class="link-dialog media-details v2">View clip</a>');
      }
      var ul = div.find('ul');
      container.append(div);
      catalogItem.prepare_screenshots(div);

      ul.jcarousel({size: screenshots.length, itemFallbackDimension: 40});
      var c = ul.data('jcarousel');
      c.reset();
      for (var i in screenshots) {
	var s = screenshots[i];
	c.add(i, '<li><a href="#' + s.file_name + '"><img src="' + mediaUrl + 'media/thumbs/muze/40x25/' + s.file_name + '" width="40" height="25" /></a></li>');
      }

      catalogItem.prepare_screenshots(div);
    }
    else {
      container.hide();
    }
  },

  update_catalog_item_actions: function (item) {
    var ul = $('.catalog-item-actions'),
    actions = item.actions || {};

    ul.empty();

    if (actions.buy) {
      var li = $(
	$.LI({Class: 'catalog-item-action-buy'},
	     $.A({href: actions.buy.url, Class: 'action link-dialog', title: 'Buy'}, "Buy"),
	     $.P({}, $.STRONG({}, 'PRICE'), $.SPAN({Class: 'price'}))
	    ));
      li.find('span').html(actions.buy.price);
      ul.append(li);
    }
    if (actions.trade) {
      var li = $(
	$.LI({Class: 'catalog-item-action-trade'},
	     $.A({href: actions.trade.url, Class: 'action link-dialog', title: 'Trade'}, "Trade"),
	     $.P({}, $.STRONG({}, 'VALUE'), $.SPAN({Class: 'price'}))
	    ));
      li.find('span').html(actions.trade.price);
      ul.append(li);
    }
    if (actions.rent) {
      var li = $(
	$.LI({Class: 'catalog-item-action-rent'},
	     $.A({href: actions.rent.url, Class: 'action link-dialog', title: 'Rent'}, "Rent"),
	     $.P({Class: 'message'})
	    ));
      li.find('.message').html(actions.rent.price);
      ul.append(li);
    }
    $.fn.prepareLinks();
  },

  display_catalog_item: function (item) {
    var $d = $('.catalog-item-details'),
    $p = $d.find('.catalog-item-params'),
    $s = $('#catalog-item-sidebar');

    $d.find('h1.catalog-item-title').text(item.title);
    catalogItem.set_item_ratio(item);
    catalogItem.update_main_item_properties(item);
    catalogItem.update_catalog_item_actions(item);
    catalogItem.display_screen_shots(item.screenshots, item.media_details);
    catalogItem.updateAdvertisement();

    var cover = $('.catalog-item-image img').hide();
    if (item.cover)
      cover.attr('src', item.cover).show();

    var also_on = $d.find('.catalog-item-also-on')
      .empty()
      .append('<strong>Also on:</strong> ');
    for(var index in item.also_on)
    {
      var i = item.also_on[index];
      if (index != 0)
	also_on.append(', ');
      also_on.append('<a href="' + i.url + '">' + i.name + '</a>');
    }

    $d.find('.catalog-item-description')
      .empty()
      .append(item.description)
      .append(' <a href="' + item.url + 'muze-description" class="get-more">Read Full Description</a>');

    catalogItem.prepare_also_on_urls();

    catalogItem.set_review_count(item.reviews.count);
    var member_reviews_items = $d.find('.member-reviews-items').empty();
    if (item.reviews.items.length > 0) {
      var klass = 'member-reviews-list';
      if (!item.authenticated)
	klass += ' not-authenticated';
      var member_reviews_list = $('<ul class="' + klass + '" />');
      for (var i in item.reviews.items) {
	member_reviews_list.append(catalogItem.create_review(item.reviews.items[i]));
      }
      member_reviews_items.append(member_reviews_list);
      if (item.authenticated && item.reviews.items.length < item.reviews.count) {
	member_reviews_items.append(
	  $.DIV({Class: 'member-reviews-list-actions'},
		$.A({Class: 'get-more', href: item.url + 'get-more-reviews/'}, 'View more reviews...'))
	);
      }
      catalogItem.update_member_reviews_list();
      catalogItem.prepare_get_more_reviews_url();
    }
    else {
      member_reviews_items.append('<div class="item-reviews-be-first">Be The First To Write A Review!</div>');
    }

    $('.catalog-item-muze-description').empty();
    catalogItem.prepare_get_more_description_url();

    if (item.reviews.form)
      reviewForm.setContent(item.reviews.form);

    catalogItem.update_review_links(item);
    $.fn.prepareLinks();
  },

  create_item_thumb: function (item) {
    var li = $($.LI({},
		    $.DIV({Class: 'catalog-item empty'},
			  $.A({href: item.url}, item.short_name)
			 )
		   ));
    if (item.thumb_image) {
      li.find('.catalog-item').removeClass('empty');
      li.find('.catalog-item a').empty().append($.IMG({
	src: item.thumb_image,
	width: 55,
	height: 70
      }));
    }
    return li;
  },

  previewScreenshot: function () {
    var a = $(this),
    img = a.find('img'),
    src = catalogConfig.mediaUrl + '/media/thumbs/muze/330x200/' + a.attr('href').substring(1);
    $('#catalog-item-sidebar .main-image')
      .attr('src', img.attr('src'))
      .attr('src', src);
    return false;
  },

  prepare_screenshots: function () {
    var block = $('#catalog-item-sidebar .screenshots');

    block.find('li a')
      .click(catalogItem.previewScreenshot)
      .mouseenter(function () {
	var a = $(this);
	a.attr('__timeout', setTimeout(function () {
	  catalogItem.previewScreenshot.apply(a, []);
	}, 1000));
      })
      .mouseleave(function () {
	var a = $(this);
	clearTimeout(a.attr('__timeout'));
      });
  },

  updateAdvertisement: function () {
    var a = $('#sidebar-advertisement');
    if (a.size() == 0)
      return;
    var s = $('#catalog-item-sidebar .screenshots ul').size();
    if (s) {
      a.data('nivo:vars').stop = true;
      a.hide();
    }
    else {
      a.show();
      a.data('nivo:vars').stop = false;
    }
  },

  prepareMediaDialog: function () {
    $('#item-media-details-sidebar .videos a').each(function (index, a) {
      var a = $(a);
      a.click(function () {
	$('#media-viewer').hide();
	$('#media-player').show();
	$('#media-player-hilo').show();

	$('#media-player-hilo a').removeClass('checked');
	$('#media-player-lo').addClass('checked');

	var href = $(this).attr('href');
	href = href.split('-');
	currentVideoClip = href[href.length - 1];

	$f().stop();
	$f().play(videoClips[currentVideoClip].f1);
	//var swf = swfobject.getObjectById('video-player');
	//swf.playClip(videoClips[index].f1, videoClips[index].f2);

	return false;
      });
    });

    $('#media-player-lo').click(function () {
      $('#media-player-hilo a').removeClass('checked');
      $(this).addClass('checked');
      $f().play(videoClips[currentVideoClip].f1);
      return false;
    });

    $('#media-player-hi').click(function () {
      $('#media-player-hilo a').removeClass('checked');
      $(this).addClass('checked');
      $f().play(videoClips[currentVideoClip].f2);
      return false;
    });

    $('#item-media-details-sidebar .screenshots a').each(function (index, a) {
      var a = $(a);
      a.click(function () {
	if ($('#item-media-details-sidebar .videos a').size()) {
	  $f().stop();
	}
	var href = $(this).attr('href');
	$('#media-player').hide();
	$('#media-player-hilo').hide();
	$('#media-viewer').css('background-image', 'url(' + href + ')').show();
	return false;
      });
    });

    var a = $('#item-media-details-sidebar .videos a:first');
    if (a.size()) {
      a.click();
      ////			$('#media-viewer').hide();
      //			$('#media-player').show();
      ////			$f().play(a.attr('href'));
    }
    else {
      a = $('#item-media-details-sidebar .screenshots a:first');
      if (a.size()) {
	a.click();
        ////				$('#media-player').hide();
        ////				$('#media-viewer').css('background-image', 'url(' + a.attr('href') + ')').show();
      }
    }
  }
};

var reviewForm = {
  init: function () {
    reviewForm.getForm().ajaxForm(reviewForm.options);
  },

  getForm: function () {
    return $('.item-reviews-form form');
  },

  setContent: function (form) {
    $('.item-reviews-form')
      .empty()
      .append(form);
    $.fn.prepareFormWidgets(reviewForm.getForm());
    Forms.prepare_error_message();
    reviewForm.init();
  },

  options: {
    beforeSubmit: function () {
      var f = reviewForm.getForm(),
      v = f.find('textarea').val();
      if ($.trim(v) === '') {
	alert('Please write a review before continue.');
	f.find('textarea').focus();
	return false;
      }
      v = f.find('.rating-field input').val();
      if (v == 0) {
        alert('Please rate the game before continue.');
        return false;
      }
      reviewForm.getForm().disableForm();
    },
    success: function (response, status, xhr, form) {
      reviewForm.getForm().enableForm();
      if (status != 'success') {
	return;
      }
      reviewForm.setContent(response.form);
      if (response.status != 'errors') {
	var review = response.review;

	if ($('#member-review-' + review.id).size() == 0) {
	  if ($('.member-reviews-list').size() == 0) {
	    $('.member-reviews-items')
	      .empty()
	      .append('<ul class="member-reviews-list"></ul>');
	  }

	  $('.member-reviews-list').prepend(catalogItem.create_review(review));
	  catalogItem.update_review_links();
	}
	catalogItem.set_review_count(response.review_count);
	catalogItem.set_item_ratio(response.item);

	var target = $('#member-review-' + review.id);
	$('body').animate({scrollTop: target.attr('offsetTop')}, 500);
      }
    }
  }
};

jQuery(document).ready(function () {
  catalogItem.init();
  reviewForm.init();

  $('.popular-games-by a').each(function (index, a) {
    var a = $(a);
    a.click(function () {
      var href = $(this).attr('href');
      jQuery.getJSON(href, function (data, status) {
	if (status != 'success')
	  return;
	var ul = $('.popular-games .games-thumb-list')
	  .empty();
	for (var i in data.items) {
	  ul.append(catalogItem.create_item_thumb(data.items[i]));
	}
	Catalog.initDetailsHint();
      });
      return false;
    });
  });

  $('#sidebar-advertisement').nivoSlider({
    pauseTime: 8000,
    directionNav: false,
    controlNav: false
  });

  catalogItem.updateAdvertisement();

  $('ul.rating a').click(function(){
    $.get($(this).attr('href'), function(data){
      catalogItem.set_item_ratio(data);
    });
    return false;
  });
});
