def calc_paginator_ranges(paginator, page_num, on_each_side=3, en_ends=2):
    left_end = None
    right_end = None

    if paginator.num_pages <= 1:
        r = []
    elif paginator.num_pages <= 10:
        r = range(1, paginator.num_pages + 1)
    else:
        if page_num - 1 > (on_each_side + en_ends):
            left_end = range(1, on_each_side)
            b = page_num - on_each_side
        else:
            b = 1

        if page_num < (paginator.num_pages - on_each_side - en_ends):
            e = page_num + on_each_side + 1
            right_end = range(paginator.num_pages - en_ends + 1, paginator.num_pages + 1)
        else:
            e = paginator.num_pages + 1

        r = range(b, e)

    return {'left_end': left_end, 'range': r, 'right_end': right_end}

