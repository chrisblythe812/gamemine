import re


class BaseLegacyTransformationForm(object):
    """
    Helper class to handle legacy forms
    """
    new_form = None

    transform_hash = {}

    def __init__(self, data=None, *args, **kwargs):
        original_kwargs = kwargs.copy()
        _initial = kwargs.pop("initial", {})
        self.instances = kwargs.pop("instances", None)
        self.instance = kwargs.pop("instance", None)
        super(BaseLegacyTransformationForm, self).__init__(data, *args, **kwargs)

        kwargs.pop("activate_correction", None)
        kwargs.pop("request", None)
        kwargs.pop("melissa", None)
        kwargs.pop("aim", None)
        kwargs.pop("shipping_address", None)
        kwargs.pop("email", None)
        kwargs.pop("card_verification_callback", None)
        kwargs.pop("request", None)

        kwargs.update(self.get_new_form_kwargs(data=data, *args, **original_kwargs))
        model_data = data
        if data is not None:
            model_data = self.transform_data(data)
        self.model_form = self.new_form(
            model_data, *args, **kwargs
        )

    def get_new_form_kwargs(self, data=None, *args, **kwargs):
        return {}

    def transform_data(self, data):
        """
        Renames data keys to match ``model_form``
        """
        _data = {}
        for key, value in data.items():
            no_prefix_key = re.sub(r"^%s-" % self.prefix, "", key)
            if no_prefix_key in self.transform_hash:
                prefix = self.prefix and "%s-" % self.prefix or ""
                key = "%s%s" % (prefix, self.transform_hash[no_prefix_key])
            _data[key] = value
        return _data

    def untransform_data(self, data):
        """
        Renames data keys to match this legacy form
        """
        _data = {}
        transform_hash = dict((v,k) for k, v in self.transform_hash.iteritems())
        for key, value in data.items():
            if key in transform_hash:
                key = transform_hash[key]
            _data[key] = value
        return _data

    def full_clean(self):
        self.model_form.full_clean()
        super(BaseLegacyTransformationForm, self).full_clean()
        cleaned_data = getattr(self.model_form, "cleaned_data", None)
        if cleaned_data and not self._errors:
            if getattr(self, "cleaned_data", None) is None:
                self.cleaned_data = {}
            self.cleaned_data.update(self.model_form.cleaned_data)

    def get_initial(self):
        data = self.untransform_data(self.model_form.initial)
        data.update(self._initial)
        return data

    def set_initial(self, initial):
        self._initial = initial

    initial = property(get_initial, set_initial)

    def save(self, commit=True):
        return self.model_form.save(commit)
