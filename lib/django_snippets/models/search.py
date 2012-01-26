import operator

from django.db.models.query_utils import Q


def search(qs, q, fields, distinct=None):
    qq = q.split()
    filters = []
    for q in qq:
        ff = []
        for f in fields:
            ff.append(Q(**{f + '__icontains': q}))
        filters.append(reduce(operator.or_, ff))
    qs = qs.filter(reduce(operator.and_, filters))
    if distinct:
        qs = qs.distinct(*distinct)
    return qs
