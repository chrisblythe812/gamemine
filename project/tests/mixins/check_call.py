class CheckCallMixin(object):
    def __call__(self, *args, **kwargs):
        super(CheckCallMixin, self).__call__(*args, **kwargs)
        if getattr(self, "_check_call_results", None):
            del self._check_call_results

    def check_call_decorator(self, check_args_func=None):
        """
        Checks args and kwargs passed to function with ``check_args_func``
        and stores result in ``self._check_call_results`` dict.
        If no ``check_args_func`` provided just checks function call.
        """
        if not getattr(self, "_check_call_results", None):
            self._check_call_results = {}

        def wrapper_wrapper(func):
            self._check_call_results[func] = False

            def wrapper(*args, **kwargs):
                if check_args_func is None or check_args_func(args, kwargs):
                    self._check_call_results[func] = True
                return func(*args, **kwargs)
            return wrapper

        return wrapper_wrapper

    def assertCheckCall(self):
        """
        Raises ``AssertionError`` if there are unsuccessful results
        in ``self._check_call_results`` dict
        """
        for func, success in self._check_call_results.items():
            if not success:
                raise AssertionError("%s call check failed" % func)
