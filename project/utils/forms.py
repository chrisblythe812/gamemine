from django import forms as django_forms
from django.forms import *
from django.utils.safestring import mark_safe


def _set_error_msg(form):
    if not form.is_valid() and form.errors:
        if form.errors.get("__all__"):
            try:
                form._error = form.errors.get("__all__")[0]
            except IndexError:
                form._error = form.errors.get("__all__")
        else:
            error_field = [f for f in form.fields.keys() if f in form.errors.keys()][0]
            form._error = mark_safe(u"Error &mdash; %s is incorrect" % form[error_field].label)
            form._error_message = form.errors[error_field][0]


class Form(django_forms.Form):
    def full_clean(self, *args, **kwargs):
        super(Form, self).full_clean(*args, **kwargs)
        self.set_error_msg()

    @property
    def error(self):
        if not hasattr(self, "_error"):
            self.set_error_msg()
        return self._error

    @property
    def error_message(self):
        if not hasattr(self, "_error_message"):
            self.set_error_msg()
        return self._error_message

    def set_error_msg(self):
        _set_error_msg(self)


class ModelForm(django_forms.ModelForm):
    def full_clean(self, *args, **kwargs):
        super(ModelForm, self).full_clean(*args, **kwargs)
        self.set_error_msg()

    @property
    def error(self):
        if not hasattr(self, "_error"):
            self.set_error_msg()
        return self._error

    @property
    def error_message(self):
        if not hasattr(self, "_error_message"):
            self.set_error_msg()
        return self._error_message

    def set_error_msg(self):
        _set_error_msg(self)
