def paged(paged_list_name, per_page=30):
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            result = func(request, *args, **kwargs)
            if not isinstance(result, dict):
                return result
            try:
                page = int(request.GET.get('page', 1))
            except ValueError:
                page = 1
            from django.core.paginator import Paginator, InvalidPage
            
            result['request'] = request
            try:
                real_per_page = per_page
                paginator = Paginator(result['paged_qs'], real_per_page)
                try:
                    result[paged_list_name] = paginator.page(page).object_list
                except InvalidPage:
                    page = 1
                    result[paged_list_name] = paginator.page(page).object_list
                result['counter_offset'] = (per_page * (page-1))
                result['count'] = paginator.count
                result['page'] = page
                result['pages'] = paginator.num_pages
            except:
                pass
            return result
        return wrapper
    return decorator
