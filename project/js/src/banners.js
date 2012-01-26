(function($) {
	$.fn.balalaykaBanner = function (options) {
		var 
		settings = $.extend({}, $.fn.balalaykaBanner.defaults, options || {}),
		cls = settings.balalaykaClass;
		
		var Balalayka = function (banner) {
			var timer,
			balalayka = {
				buidSidebarItem: function (d) {
					var res = $('<li class="' + cls + '-sidebar-item" style="background-image: url(' + d.images[1] + ')"></li>');
					res.data('balalayka:object', d);
					return res;
				},
				
				setBannerContent: function (d) {
					var back = banner.find('.' + cls + '-banner-background'),
						fore = banner.find('.' + cls + '-banner-foreground');
					
					back.css('background-image', 'url(' + d.images[0] + ')');
					fore.fadeOut(settings.animationSpeed, function () {
						fore.empty().css('background-image', 'url(' + d.images[0] + ')').show();
						for (var i = 0; i < d.links.length; ++i) {
							var klass = d.banner_class + ' ' + cls + '-banner-link ' + cls + '-banner-link-' + i;
							if (d.links[i][1]) 
								klass += ' ' + d.links[i][1];
							var a = $('<a href="' + d.links[i][0] + '" class="' + klass + '"> </a>');
							if (d.links[i][0] == '#')
								a.click(function () { return false; });
							fore.append(a);
						}
						$.fn.prepareLinks();
					});
				},
				
				start: function () {
					if (timer) 
						clearInterval(timer);
					timer = setInterval(balalayka.next, settings.pauseTime);
				},
				
				next: function () {
					balalayka.pause();
					var sidebar = banner.find('.' + cls + '-sidebar-items'),
						first = sidebar.find('.' + cls + '-sidebar-item:first');
					
					balalayka.setBannerContent(first.data('balalayka:object'));
					
					sidebar.animate({
						marginTop: '-' + settings.itemHeight + 'px'
					}, settings.animationSpeed, function () {
						sidebar.css('margin-top', '0px');
						first.appendTo('.' + cls + '-sidebar-items');
						balalayka.resume();
					});
				},
				
				pause: function () {
					clearInterval(timer);
					timer = null;
				},
				
				resume: function () {
					balalayka.start();
				},
				
				preload: function (d) {
					(new Image()).src = d.images[0];
					(new Image()).src = d.images[1];
				}
 			};
			return balalayka;
		};
			
		return this.each(function () {
			var 
			banner = $(this),
			vars = {
				balalayka: Balalayka(banner),
				paused: false
			};
			
			banner.data('balalayka:vars', vars);
			banner.addClass(cls);
			banner.empty().append('<div class="banner-header"></div><div class="' + cls + '-content"><div class="' + cls + '-banner"><div class="' + cls + '-banner-background"><div class="' + cls + '-banner-foreground"></div></div></div><div class="' + cls + '-sidebar"></div><a href="#" class="' + cls + '-sidebar-next-link"></a></div>');
			
			var content = banner.find('.' + cls + '-content');
			content.hide();
			
			$.get(settings.url + '?' + Math.floor(10000000 * Math.random()), function (data, status) {
				if (status != 'success')
					return;
				
				var sidebarItems = $('<ul class="' + cls + '-sidebar-items"></ul>')
				for (var i = 0; i < data.banners.length; ++i) {
					vars.balalayka.preload(data.banners[i]);
					sidebarItems.append(vars.balalayka.buidSidebarItem(data.banners[i]));
				}
				banner.find('.' + cls + '-sidebar').empty().append(sidebarItems);
				var next_link = banner.find('.' + cls + '-sidebar-next-link').click(function () {
					vars.balalayka.next();
					return false;
				}).hide();
				next_link
					.mouseenter(function () { next_link.addClass('mouse-over'); })
					.mouseleave(function () { next_link.removeClass('mouse-over'); });
				banner.find('.' + cls + '-sidebar-items')
					.mouseenter(function () {
							next_link.fadeIn(); 
						})
					.mouseleave(function () {
							setTimeout(function () {
								if (!next_link.hasClass('mouse-over'))
									next_link.fadeOut(); 
							}, 500);
						});
				
				vars.balalayka.setBannerContent(data.banners[data.banners.length - 1], data.banners[0]);
				
				content.fadeIn(settings.animationSpeed, function () {
					vars.balalayka.start();
				});
			});
		});
	};
	
	$.fn.balalaykaBanner.defaults = {
		pauseTime: 8500,
		balalaykaClass: 'balalayka',
		itemHeight: 115,
		animationSpeed: 500
	};
})(jQuery);
