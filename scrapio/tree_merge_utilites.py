import typing, bs4, functools
import time, style_parser, re
import converter_objs

class new_stylestring:
    def __init__(self, _val:bs4.element.NavigableString, _matches:typing.List[bs4.element.NavigableString]) -> None:
        self.val, self.matches = _val, _matches

    def __eq__(self, _obj) -> bool:
        if not getattr(_obj, 'is_stylestring', False):
            return False
        return self.val == _obj.val
    @property
    def is_stylestring(self) -> bool:
        return True
    def to_dict(self, **kwargs) -> dict:
        return repr(self)
    def to_list(self) -> str:
        return repr(self)
    @property
    def main(self):
        class _main:
            def __init__(self) -> None:
                self.name = '__stylestring__'
        return _main()
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.val}) | matched({len(self.matches)})'

class StyleString:
    def __init__(self, _val:bs4.element.NavigableString, _matches:typing.List[bs4.element.NavigableString]) -> None:
        self.val, self.matches = _val, _matches
    def __iter__(self) -> typing.Generator:
        yield from [self.val]
    @property
    def has_matches(self) -> bool:
        return bool(self.matches)
    @property
    def is_target_entity(self) -> bool:
        return True
    @property
    def strip_val(self) -> str:
        if re.findall('\<img|\<a|\<div|\<span|\<li|\<ul|\<iframe', self.val):
            return ''
        #return re.sub('^[\s\n]+|[\s\n\.,:]+$', '', self.val)
        return re.sub('^[\s\n\-\/]+|[\s\n\.,:\-\/]+$', '', self.val)
    @property
    def is_empty_string(self):
        return bool(self.strip_val)
    def __eq__(self, _obj) -> bool:
        if not getattr(_obj, 'is_stylestring', False):
            return False
        return self.val == _obj.val
    @property
    def is_specialelem(self) -> bool:
        return False
    def __bool__(self) -> bool:
        return True
    @property
    def is_stylestring(self) -> bool:
        return True
    def to_dict(self, **kwargs) -> dict:
        #return repr(self)
        return self.strip_val
    def to_list(self) -> str:
        return self
    @property
    def main(self):
        class _main:
            def __init__(self) -> None:
                self.name = '__stylestring__'
        return _main()
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.val}) | matched({len(self.matches)})'

    def format_payload(self, **kwargs) -> converter_objs.StyleString_payload:
        return converter_objs.StyleString_payload(self.strip_val, **kwargs)



def nav_string_eq(a:bs4.element.NavigableString, b:bs4.element.NavigableString) -> bool:
    return re.sub('^[\s\n]+|[\s\n\.,:]+$', '', a) == re.sub('^[\s\n]+|[\s\n\.,:]+$', '', b)

def validate_obj(_f:typing.Callable) -> typing.Callable:
    @functools.wraps(_f)
    def wrapper(cls, _main, *targets) -> typing.Any:
        if not isinstance(_main, bs4.element.NavigableString):
            #{'link', 'script', 'noscript', 'iframe'}
            return _f(cls, _main, *[i for i in targets if not isinstance(i, bs4.element.NavigableString) and not isinstance(i, bs4.Comment)])
        return StyleString(_main, [i for i in targets if isinstance(i, bs4.element.NavigableString) and nav_string_eq(i, _main)])

    return wrapper

def stringify(_f:typing.Callable) -> typing.Callable:
    @functools.wraps(_f)
    def wrapper(cls, *args, **kwargs) -> typing.Any:
        _r = _f(cls, *args, **kwargs)
        return _r if not isinstance(_r, list) else ' '.join(_r)
    return wrapper


def timeit(_f:typing.Callable) -> typing.Callable:
    @functools.wraps(_f)
    def wrapper(*args, **kwargs) -> typing.Any:
        _t = time.time()
        _r = _f(*args, **kwargs)
        print(f"'{_f.__name__}' ran in :{abs(time.time()-_t)}")
        return _r
    return wrapper

def to_style_obj(_f:typing.Callable) -> typing.Callable:
    @functools.wraps(_f)
    def wrapper(*args, **kwargs) -> typing.Any:
        return [style_parser.StyleRule(i.name, i.value) for i in _f(*args, **kwargs)]
    return wrapper

def filter_attrs(targets:list = [], retain=False) -> typing.Callable:
    def outer(_f:typing.Callable) -> typing.Callable:
        @functools.wraps(_f)
        def wrapper(_self, _tag:str, _attrs:dict) -> None:
            return _f(_self, _tag, {a:b for a, b in _attrs.items() if (a not in targets if not retain else a in targets)})
        return wrapper
    return outer

class TreeAttrs:
    @property
    def has_matches(self) -> bool:
        return bool(self.matched)
    @property
    def target_value(self) -> bool:
        return self.main.name in {'a', 'img', 'button'}
    @property
    def is_target_entity(self) -> bool:
        return self.is_specialelem
    @property
    def is_specialelem(self) -> bool:
        return self.main.name in {'a', 'img'}
    @property
    def is_stylestring(self) -> bool:
        return False
    @property
    def tree_attrs(self):
        return self.__class__.attr_extraction(self.main)
    @property
    def basic_tree_attrs(self):
        return self.__class__.basic_attr_extraction(self.main)
    @property
    def name(self) -> str:
        return self.main.name
    @property
    def hook(self) -> str:
        return 'default' if not self.target_value else self.target_value