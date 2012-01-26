from project.staff.urls import staff_main_menu


def common(request):
    if request.user.is_staff:
        if not request.user.is_superuser:
            main_menu = staff_main_menu.filter(request.user.get_profile().group)
        else:
            main_menu = staff_main_menu
    else:
        main_menu = None
    return {
        'staff_main_menu': main_menu,
        'is_superuser': request.user.is_superuser,
    }
