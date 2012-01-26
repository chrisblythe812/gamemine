var Cart = {
	init: function () {
		Cart.updateCartActions();
		Cart.init_list_actions();
		Cart.init_quantity_inputs();		
	},


	updateCartContent: function (data) {
		$('.cart-link').text('Cart (' + data.cart.size + ')');
		$('#cart-heading .total').empty().text('Total: ' + data.cart.total);
		$('#cart-index-content').empty().append(data.html);
		Cart.updateCartActions();
		Cart.init_quantity_inputs();
		$.fn.prepareLinks();
	},
	
	init_quantity_inputs: function () {
		$(".quantity-input").keydown(function(event){
			if (!(event.keyCode == 13 || event.keyCode == 46 || event.keyCode == 8 || event.keyCode == 9 || event.keyCode >= 48 && event.keyCode <= 57))
				event.preventDefault();	
		});
	},
	
	updateCartActions: function () {
		var parseAction = function(href){
			var pieces = href.split('/'),
				len = pieces.length,
				action = pieces[len - 3],
				id = pieces[len - 2];
			return {action: action, id: id};
		},
		action = function () {
			var a = parseAction($(this).data('cart-action-href'));
			if (a.action == 'Add')
				Cart.addItem(a.id);
			else if (a.action == 'Remove')
				Cart.removeItem(a.id);
			return false;
		};
		
		$('a.cart-action-remove').each(function () {
			var a = $(this);
			if (!a.data('cart_action_initialized'))
			{
				var aa = parseAction(a.attr('href'))
				a.data('cart-action-href', a.attr('href'));
				a.click(action).attr('href', '/Cart/#' + aa.action);
				a.data('cart_action_initialized', true);
			}
		});
		
		
		var	 
		ajaxFormOptions = {
			'beforeSubmit': function () { $(this).disableForm(); },
			'success': function (data, status, xhr, form) {
				if (status != 'success') {
					$(this).enableForm();
					return;
				}
				if (data.redirect_to) {
					window.location = data.redirect_to;
					return;
				}
				Cart.updateCartContent(data);
			}
		};
		$('.cart-table-form').submit(function() {
			$(this).ajaxSubmit(ajaxFormOptions);
			return false;
		});
		$('.cart-table-form .submit').click(function () {
			$(this).parents('form').submit();
			return false;
		});
	},
	
	addItem: function(id) {
	},
	
	removeItem: function(id) {
		jQuery.getJSON('/Cart/Remove/'+id+'/', function (data, status) {
			if (status != 'success')
				return;
			if (data.redirect_to) {
				window.location = data.redirect_to;
				return;
			}
			Cart.updateCartContent(data);
		});
	},
	
	init_list_actions: function () {
		$('#buy-list-grid .buy-list-action').each(function (index, a) {
			$(a)
			.data('_action', $(a).attr('href'))
			.attr('href', '#')
			.click(function () {
				var href = $(this).data('_action');
				jQuery.getJSON(href, function (data, status) {
					if (status != 'success')
						return;
					$('#buy-list-grid').empty().append(data.html);
					$('.buy-list-size').empty().text(data.buy_list.size);
          $('.lists-size').empty().text(data.lists_size);
					Cart.init_list_actions();
				});
				return false;				
			});
		});
	}
};

$(document).ready(function () {
	Cart.init();	
});
