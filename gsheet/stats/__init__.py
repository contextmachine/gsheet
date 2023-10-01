from collections import Counter


def resort(data, ks):
    yield ks
    for item in data:
        yield [item.get(k) for k in ks]



def cross_aggregate(dat, key, mask, sep=" "):
    iterkey=not isinstance(key,str)
    def gen():
        for item in filter(lambda x: x[mask] != 2, dat):
            if iterkey:
                yield sep.join(f'{item[k]}' for k in key)
            else:
                yield f'{item[key]}'

    return dict(Counter(gen()))
