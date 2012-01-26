from django.conf import settings
from django.forms.widgets import SelectMultiple, CheckboxInput, RadioSelect
from django.utils import simplejson
from django.utils.encoding import StrAndUnicode, force_unicode
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe
from itertools import chain
from tinymce.widgets import TinyMCE

class CustomTinyMCEWidget(TinyMCE):
    def __init__(self, content_language=None, attrs=None, mce_attrs={}):
        mce_attrs = settings.TINYMCE_DEFAULT_CONFIG.copy()
        buttons_str = mce_attrs['theme_advanced_buttons4'] + ',|,contactButtom,contactLastName,contactCompanyName'
        mce_attrs['theme_advanced_buttons4'] = buttons_str
        mce_attrs['setup'] = 'add_button_callback'
        mce_attrs['relative_urls'] = False
        mce_attrs['remove_script_host'] = False
        mce_attrs['convert_urls'] = True
        super(CustomTinyMCEWidget, self).__init__(content_language, attrs, mce_attrs)
        
    class Media:
        try:
            js = [
            'os3marketing/tinymce.js',
            ]
        except AttributeError:
            pass
        
class TemplateButtonMCEWidget(TinyMCE):
    def __init__(self, content_language=None, attrs=None, mce_attrs={}):
        mce_attrs = settings.TINYMCE_DEFAULT_CONFIG.copy()
        buttons_str = mce_attrs['theme_advanced_buttons4'] + ',|,contactButtom,contactLastName,contactCompanyName,templateButtom'
        mce_attrs['theme_advanced_buttons4'] = buttons_str
        mce_attrs['setup'] = 'add_button_callback'
        mce_attrs['relative_urls'] = False
        mce_attrs['remove_script_host'] = False
        mce_attrs['convert_urls'] = True
        super(TemplateButtonMCEWidget, self).__init__(content_language, attrs, mce_attrs)
  
    class Media:
        try:
            js = [
            'os3marketing/tinymce.js',
            ]
        except AttributeError:
            pass
                            
class CustomCheckboxSelectMultiple(SelectMultiple):
    def __init__(self,  *args, **kwargs):
        if 'div_style' in kwargs:
            self.div_style = kwargs['div_style']
            del kwargs['div_style'] 
            
        if 'li_style' in kwargs:
            self.li_style = kwargs['li_style']
            del kwargs['li_style']  
                       
        super(CustomCheckboxSelectMultiple,self).__init__(*args, **kwargs)
    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<div style="%s overflow:auto;"><ul style="margin:0;padding:0;">' % (self.div_style and self.div_style or '')]
        # Normalize to strings
        str_values = set([force_unicode(v) for v in value])
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = u' for="%s"' % final_attrs['id']
            else:
                label_for = ''

            cb = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_unicode(option_value)
            rendered_cb = cb.render(name, option_value)
            option_label = conditional_escape(force_unicode(option_label))
            output.append(u'<li style="float:left; list-style:none; %s">' % (self.li_style and self.li_style or ''))
            output.append('%s %s</li>' % (rendered_cb,option_label)) #(label_for, rendered_cb, option_label))
        output.append(u'</ul></div>')
        return mark_safe(u'\n'.join(output))

    def id_for_label(self, id_):
        # See the comment for RadioSelect.id_for_label()
        if id_:
            id_ += '_0'
        return id_
    id_for_label = classmethod(id_for_label)      
    
class HorizRadioRenderer(RadioSelect.renderer):
    """ this overrides widget method to put radio buttons horizontally
        instead of vertically.
    """
    def render(self):
        """Outputs radios"""
        return mark_safe(u'\n'.join([u'%s\n' % w for w in self]))


             