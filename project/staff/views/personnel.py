from logging import debug #@UnusedImport

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect

from django_snippets.views import simple_view

from project.staff.forms import UserForm, NewUserForm
from project.staff.views import superuser_required
from project.members.models import Profile


def staff(request, **kwargs):
    return {
        'title': 'Personnel: Staff',
        'users': User.objects.filter(is_staff=True),
    }, None


@superuser_required
@simple_view('staff/personnel/new_user.html')
def new_user(request):
    if request.method == 'POST':
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save(False)
            user.is_staff = True
            user.set_password(form.cleaned_data['password'])
            user.save()
            Profile(user=user, 
                    group=form.cleaned_data['role'],
                    dc=form.cleaned_data['dc']).save()
            return redirect('staff:page', 'Personnel/Staff')
    else:
        form = NewUserForm()
    return {
        'title': 'New User',
        'form': form,
    }


@superuser_required
@simple_view('staff/personnel/edit_user.html')
def edit_user(request, id):
    user = get_object_or_404(User, id=id, is_staff=True)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            p = user.get_profile()
            p.group = form.cleaned_data['role']
            p.dc = form.cleaned_data['dc']
            p.save()
            return redirect('staff:page', 'Personnel/Staff')
    else:
        dc = user.get_profile().dc.id if user.get_profile().dc else None
        role = user.get_profile().group
        form = UserForm(instance=user, initial={'dc': dc, 'role': role})
    return {
        'title': 'Edit user: %s' % id,
        'form': form,
        'user': user,
    }


@superuser_required
def change_user_password(request, id):
    pass
