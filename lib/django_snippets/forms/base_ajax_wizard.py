from logging import debug  #@UnusedImport

from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template import loader
from django.http import HttpResponse
from django.utils import simplejson as json
from django.contrib.formtools.wizard import FormWizard
from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.utils.safestring import mark_safe


class BaseAjaxWizard(FormWizard):
    def __init__(self, template_name, form_list, initial=None, title=None, form_kwargs=None,
                 context={}):
        super(BaseAjaxWizard, self).__init__(form_list, initial)

        self.regular_template_name = template_name
        parts = template_name.split('.')
        parts.insert(-1, 'dialog')
        self.ajax_template_name = '.'.join(parts)
        self.form_kwargs = form_kwargs or {}
        self.title = title
        self.context = context

    def get_form(self, step, data=None):
        "Helper method that returns the Form instance for the given step."
        return self.form_list[step](data, 
                                    prefix=self.prefix_for_step(step), 
                                    initial=self.initial.get(step, None),
                                    **self.form_kwargs.get(step, {}))

    def get_template(self, step, request=None):
        return self.ajax_template_name if request.is_ajax() else self.regular_template_name

    def prepare_context(self, request, form, previous_fields, step, context):
        context = context or {}
        context.update(self.extra_context)
        context = dict(context, step_field=self.step_field_name, 
            step0=step, 
            step=step + 1, 
            step_count=self.num_steps(), 
            form=form, 
            previous_fields=previous_fields,
            wizard=self)
        context_instance = RequestContext(request, self.context)
        return context, context_instance

    def render_ajax_response(self, request, form, step, context, context_instance):
        template_name = self.get_template(step, request)
        result = loader.render_to_string(template_name, context, 
            context_instance=context_instance)
        content = json.dumps({'form': result})
        return HttpResponse(content, mimetype='application/json')

    def render_template(self, request, form, previous_fields, step, context=None):
        context, context_instance = self.prepare_context(request, form, previous_fields, step, context)


        secret_option = request.REQUEST.get('secret_option') == 'naturlich'

        if request.method == 'POST' and request.is_ajax() and not secret_option:
            return self.render_ajax_response(request, form, step, context, context_instance)
        else:
            return render_to_response(self.get_template(step, request),  
                                      context, 
                                      context_instance=RequestContext(request, self.context))

    def determine_step(self, request, *args, **kwargs):
        step = super(BaseAjaxWizard, self).determine_step(request, *args, **kwargs)
        return step if step >= 0 else 0

    @method_decorator(csrf_protect)
    def __call__(self, request, *args, **kwargs):
        """
        Main method that does all the hard work, conforming to the Django view
        interface.
        """
        if 'extra_context' in kwargs:
            self.extra_context.update(kwargs['extra_context'])
        current_step = self.determine_step(request, *args, **kwargs)
        self.parse_params(request, *args, **kwargs)

        # Sanity check.
        if current_step >= self.num_steps():
            raise Http404('Step %s does not exist' % current_step)

        # For each previous step, verify the hash and process.
        # TODO: Move "hash_%d" to a method to make it configurable.
        for i in range(current_step):
            form = self.get_form(i, request.POST)
            if request.POST.get("hash_%d" % i, '') != self.security_hash(request, form):
                return self.render_hash_failure(request, i)
            self.process_step(request, form, i)


        backward = True if request.POST.get('__backward') else False

        # Process the current step. If it's valid, go to the next step or call
        # done(), depending on whether any steps remain.
        if request.method == 'POST':
            if backward:
                current_step = (current_step - 1) if current_step > 0 else 0
                form = self.get_form(current_step, request.POST)
            else:
                form = self.get_form(current_step, request.POST)
        else:
            form = self.get_form(current_step)
        form_error = None
        form_error_message = None
        if not backward:
            if form.is_valid():
                self.process_step(request, form, current_step)
                next_step = current_step + 1

                # If this was the last step, validate all of the forms one more
                # time, as a sanity check, and call done().
                num = self.num_steps()
                if next_step == num:
                    final_form_list = [self.get_form(i, request.POST) for i in range(num - 1)]

                    # Validate all the forms. If any of them fail validation, that
                    # must mean the validator relied on some other input, such as
                    # an external Web site.
                    for i, f in enumerate(final_form_list):
                        if not f.is_valid():
                            return self.render_revalidation_failure(request, i, f)
                    final_form_list.append(form)
                    return self.done(request, final_form_list)

                # Otherwise, move along to the next step.
                else:
                    form = self.get_form(next_step)
                    self.step = current_step = next_step
            else:
                errors = []
                error_messages = []
                for n, f in form.fields.items():
                    if form.errors.get(n):
                        errors.append(mark_safe(u'Error &mdash; %s is incorrect' % f.label))
                        error_messages.append(mark_safe(form.errors[n][0]))
                e = form.errors.get('__all__')
                if e:
                    errors.append(e[0])
                form_error = (errors or [None])[0]
                form_error_message = (error_messages or [None])[0] 
                if hasattr(form, 'correction_data'):
                    prefix=self.prefix_for_step(current_step)
                    correction_data=dict(map(lambda x: ('-'.join((prefix, x[0])), x[1]), form.correction_data.items()))
                    form = self.get_form(current_step, correction_data)
                    form.correction_warning = True
        setattr(form, 'form_error', form_error)
        setattr(form, 'form_error_message', form_error_message)
        return self.render(form, request, current_step)
