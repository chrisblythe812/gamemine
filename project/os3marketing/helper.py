def monta_query_string(dic,remove=None):
    q = dic.copy()
    if remove:
        for s in remove:
            if s in q:
                del q[s]
    return '?%s' %  q.urlencode()