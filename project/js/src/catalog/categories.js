jQuery(document).ready(function() {
	var toolbar = $('#catalog-toolbar');
	
	function div(id) { return '<div id="' + id + '"></div>'; }
	
	toolbar
		.wrapInner(div('catalog-toolbar-content'))
		.prepend(div('catalog-toolbar-left'))
		.append(div('catalog-toolbar-right'));

	// sidebar. subscription
	(function(){
		var sub = $('#id_sidebar_subscription');
	    var email = sub.find('input[name=email]');
	    email.searchbox('Enter Email Address');
	    sub.submit(function(){
	    	var value = email.val();
	    	if (!value || !/^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test(value)) {
	    		email.focus();
	    		alert('Please enter correct email address.');
	    		return false;
	    	}
	    	$.get('/Subscription/Subscribe/?email=' + value, function(d){
	    		if (d.success) {
	    			$(document).openWizardByUrl('/Subscription/Thank-You/');
	    		} else {
		    		email.focus();
	    			alert('Please enter correct email address.');
	    		}
	    	});
	    	return false;
	    });
    })();
});
