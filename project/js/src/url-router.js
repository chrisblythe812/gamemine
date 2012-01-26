(function (window, undefined) {

var 
urlRouter = {
	init: function () {
	},
	
	routes: {},

	currentLocation: '',
	
	timer: null,
	
	checkLocation: function (userdata) {
		var location = window.location.toString();
		if (location != urlRouter.currentLocation)
		{
			urlRouter.currentLocation = location;
			var parts = urlRouter.splitLocation(location);
			if (parts[1] != '') {
				var callback = urlRouter.routes[parts[1]] || function() {};
				callback.apply(null, [parts[1], parts[2], userdata]);
			}
		}
		urlRouter.timer = setTimeout(urlRouter.checkLocation, 100);
	},
	
	add: function (anchor, callback) {
		urlRouter.routes[anchor] = callback;
		return this;
	},
	
	quiteInvoke: function (callback) {
		clearTimeout(urlRouter.timer);
		callback.apply(null);
		urlRouter.currentLocation = location;
		urlRouter.startRoute();
	},
	
	startRoute: function () {
		clearTimeout(urlRouter.timer);
		//urlRouter.currentLocation = window.location.toString();
		urlRouter.timer = setTimeout(urlRouter.checkLocation, 100);
	},
	
	anchor: function (location) {
		location = location || urlRouter.currentLocation;
		return urlRouter.splitLocation(location)[1];
	},
	
	objectToUrlParams: function (o) {
		var oo = [];
		for (var key in o)
		{
			oo.push(key + '=' + o[key]);
		}
		return oo.join('&');
	},

	splitLocation: function (location) {
		location = location.toString();
		
		var base, anchor, params;
		var parts = location.split('#');
		
		base = parts[0];
		parts = parts.slice(1).join('#');
		if (parts != '')
		{
			parts = parts.split('?');
			anchor = parts[0];
			parts = parts.slice(1).join('?');
			if (parts != '')
			{
				parts = parts.split('&');
				params = new Object;
				for(var i = 0; i < parts.length; ++i)
				{
					var p = parts[i].split('=');
					params[p[0]] = p.slice(1).join('=') || true;
				}
			}
		}
		return [base, anchor || '', params];
	}
};

urlRouter.init();

window.urlRouter = urlRouter;

})(window);
