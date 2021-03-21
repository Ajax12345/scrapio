import time, typing

class _matcher_tree:
    def __init__(self, _path:typing.List[typing.List[int]], _tags:dict, _leafs:dict) -> None:
        self.path, self.tags, self.leafs = _path, _tags, _leafs
    def __iter__(self) -> typing.Iterator:
        yield from self.path
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({str(self.path)})'
 
def timeit(_f):
    def wrapper(*args, **kwargs):
        _t = time.time()
        _r = _f(*args, **kwargs)
        print(f"Executed {_f.__name__} in {abs(time.time()-_t)}")
        return _r
    return wrapper

def format_paths(_f):
    def wrapper(*args, **kwargs):
        _paths, _tags, _leafs = [], {}, {}
        for i in _f(*args, **kwargs):
            _inner_path = []
            for b in i:
                _inner_path.append(b.hash)
                _leafs[b.hash] = b.is_leaf
                _tags[b.hash] = b.tag
            _paths.append(_inner_path)
        return _matcher_tree(_paths, _tags, _leafs)
    return wrapper
        