import functools
def single_class(cls, *args, **kwargs):
    instance={}
    @functools.wraps(cls)
    def _single_instance(*args, **kwargs):
        if cls not in instance:
            instance[cls]=cls(*args, **kwargs)
        return instance[cls]
    return _single_instance