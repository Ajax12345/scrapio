import typing, bs4, functools, re
from urllib.parse import urlparse
import collections


def _merge_url(a:str, b:str) -> str:
    return b if urlparse(b).netloc else urlparse(a).netloc+b

def filter_urls(remove = []) -> typing.Callable:
    def outer(_f) -> typing.Callable:
        @functools.wraps(_f)
        def wrapper(cls, *_urls) -> typing.Tuple:
            return _f(cls, *[i for i in _urls if all(j not in i for j in remove)])
        return wrapper
    return outer

def load_urls(_f:typing.Callable) -> typing.Callable:
    @functools.wraps(_f)
    def wrapper(cls, _base_url:str, _block:typing.Any) -> typing.Any:
        return _f(cls, _merge_url(_base_url, _block)) if not isinstance(_block, bs4.BeautifulSoup) else _f(cls, *[_merge_url(_base_url, i['href']) for i in _block.head.find_all('link', {'rel':'stylesheet'})])
    return wrapper

def contextualize_idents(_f:typing.Callable) -> typing.Callable:
    @functools.wraps(_f)
    def wrapper(_self, _descriptor:list) -> typing.Any:
        _ = _f(_self, _descriptor)
        _all_ents = collections.defaultdict(list)
        for i in _descriptor:
            for b in i:
                #print(b, b.entity_name, b.name)
                _all_ents[b.entity_name].append(b.name)
        _self.ent_groups = dict(_all_ents)
    return wrapper

def filter_non_essential(_f:typing.Callable) -> typing.Callable:
    @functools.wraps(_f)
    def wrapper(_self, _listing:list) -> None:
        _target_keys = re.findall('[\w\-]+', _self.__class__.__doc__)
        _t = [i for i in _listing if any(c in {j.key for j in i.rules} for c in _target_keys)]
        print(len(_listing), len(_t))
        return _f(_self, _t)
    return wrapper
