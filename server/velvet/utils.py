def all_w_dict(iterable_dict):
    for i in iterable_dict.values():
        if i is None:
            return False
    return True
