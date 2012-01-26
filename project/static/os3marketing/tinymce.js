var editor = null;
function add_button_callback(ed, e) {
    // Add a contact button
    ed.addButton('contactButtom', {
        title : 'Adds first name',
        image : '/m/os3marketing/first-name.gif',
        onclick : function() {
			ed.focus();
			ed.selection.setContent('{{contact.first_name}}');
        }
    });
    // Add a contact button
    ed.addButton('contactLastName', {
        title : 'Adds last name',
        image : '/m/os3marketing/last-name.gif',
        onclick : function() {
			ed.focus();
			ed.selection.setContent('{{contact.last_name}}');
        }
    });    
    
    // Add a template button
    ed.addButton('templateButtom', {
        title : 'Adds a template',
        image : '/m/os3marketing/template.gif',
        onclick : function() {        	
			editor = ed;
			$('#form_template_content').load('/area51/os3marketing/newsletter/load-template-options',function(){$('#form_template').dialog('open');});			
        }
    });    
}




function select_template(){
	if($('#template_id').val() != -1){
		$.ajax({
		  url: '/area51/os3marketing/newsletter/load-template',
	      type: "GET",
	      data: ({template:$('#template_id').val()}),		
	      dataType : "json",	  
		  success: function(data) {
			editor.setContent(data.content);
			$('#form_template').dialog('close');		  
		  },
		  error:function (xhr, ajaxOptions, thrownError){
			alert('error to load templates');								  	
		  }  				  				   				  
		});	  	
	}else{alert('choose a template');}
}