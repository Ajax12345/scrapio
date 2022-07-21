import typing, bs4, itertools
import tree_merge_utilites, functools
import cssutils, logging

cssutils.log.setLevel(logging.CRITICAL)


class LookupPath:
    @classmethod
    def lookup_path(cls, path:typing.List[typing.Tuple[str, int]], _main:bs4.BeautifulSoup) -> bool:
        def _lookup(path:typing.List[typing.Tuple[str, int]], _main:bs4.BeautifulSoup) -> bool:
            _c = list(filter(lambda x:x != '\n', _main.contents))
            if len(path) == 1:
                return False if path[0][0] >= len(_c) else _c[path[0][0]] == path[0][-1]
            if path[0][0] >= len(_c):
                return False
            return False if isinstance(_c[path[0][0]], bs4.element.NavigableString) else _lookup(path[1:], _c[path[0][0]])
        return _lookup(path, _main)

    @classmethod
    def generate_path(cls, _main, *targets) -> typing.Any:
        def get_strings(d, path = []) -> typing.List:
            for i, a in enumerate(filter(lambda x:x != '\n', d.contents)):
                if isinstance(a, bs4.element.NavigableString):
                    yield path+[(i, a)]
                else:
                    yield from get_strings(a, path+[[i]])

        _result = list(get_strings(_main))
        print([[(i[-1][-1], cls.lookup_path(i, c)) for c in targets] for i in _result])
    

class _missing_elem:
    def __lt__(self, _) -> bool:
        return False

class AttrElem:
    def __init__(self, _val:typing.Any) -> None:
        self.val = _val
        
    def __lt__(self, _obj) -> bool:
        return True if isinstance(self.val, _missing_elem) and isinstance(_obj, _missing_elem) else False if isinstance(_obj, _missing_elem) else self.val < _obj.val

def objectify_elem_attr(_f:typing.Callable) -> typing.Callable:
    
    @functools.wraps(_f)
    def wrapper(*args, **kwargs) -> AttrElem:
        return AttrElem(_f(*args, **kwargs))
    
    return wrapper

class _elemn_attr_lookup:
    valid_attrs = {'id', 'class', 'href', 'src'}
    
    def attrs_eq_tag(self, a:str, b:str) -> bool:
        return a == b
    
    def attrs_eq_class(self, a:list, b:list) -> bool:
        if not a and not b:
            return True
        return bool(set(a)&set(b))
    
    def attrs_eq_id(self, a:str, b:str) -> bool:
        return a == b
    
    @classmethod
    def new_lookup(cls) -> typing.Callable:
        return cls()


class _elem_attrs:
    target_keys = {'tag', 'class', 'id'}
    def __init__(self, _tag:str, _attrs:dict) -> None:
        self.tag, self.attrs = _tag, _attrs
        
    @property
    def get_target_attrs(self):
        return [i for i in self if i in self.__class__.target_keys]
    
    def __iter__(self):
        yield from ['tag', *self.attrs]
        
    def __new_eq(self, _obj) -> bool:
        #return all((lambda x, y:x != 'N/A' and y != 'N/A' and x == y)(self[i], _obj[i]) for i in {'tag', 'class'})
        return all(self[i] == _obj[i] for i in {'tag', 'class'})
    
    @property
    def is_stylestring(self):
        return False
    
    @property
    @tree_merge_utilites.to_style_obj
    def get_styles(self):
        return [] if 'style' not in self.attrs else cssutils.parseStyle(self.attrs['style'])
    
    def __eq__(self, _obj) -> bool:
        return all(self[i] == _obj[i] for i in {*self, *_obj})
    
    def __new_eq__(self, _obj) -> bool:
        _l = _elemn_attr_lookup.new_lookup()
        return all(getattr(_l, f'attrs_eq_{i}', lambda x, y:x == y)(self(i), _obj(i)) for i in filter(lambda x:x in _l.valid_attrs, {*self, *_obj}))
    
    def __contains__(self, _descriptor) -> bool:
        return all(self.tag == i.name if i.entity_name == 'tag' else getattr(self, i.entity_name)(i.name) for i in _descriptor)
    
    def __getattr__(self, _name:str) -> typing.Callable:
        def _wrapper(_val:str) -> bool:
            _c = self(_name)
            return _c == _val if _name != 'class' else _val in _c
        return _wrapper
    
    def __call__(self, _attr:str) -> typing.Any:
        return self.tag if _attr == 'tag' else self.attrs.get(_attr, [])
    
    @tree_merge_utilites.stringify
    def __getitem__(self, _attr:str) -> typing.Any:
        return self.tag if _attr == 'tag' else self.attrs.get(_attr, 'N/A')
    
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.tag}, attrs={self.attrs})'

class _basic_attrs(_elem_attrs):
    def __new_eq_class(self, _obj) -> bool:
        if getattr(_obj, 'is_stylestring', False):
            return False
        
        if self('tag') != _obj('tag'):
            return False
        
        a, b = self('class'), _obj('class')
        _result = (not any([a, b]) or bool(set(a)&set(b)))
        return _result
    
    def __eq__(self, _obj) -> bool:
        return self.__new_eq_class(_obj)
    
    @property
    def basic_attr_header(self):
        return [self[i] for i in ['tag', 'class']]
    
    @classmethod
    def compute_class_score(cls, *args:typing.List[_elem_attrs]) -> int:
        _all_classes = {i for b in args for i in b('class')}
        return sum(all(i in c('class') for c in args) for i in _all_classes)

class StyleTree(tree_merge_utilites.TreeAttrs):
    def __init__(self, _main:bs4.BeautifulSoup, _matched:typing.List[bs4.BeautifulSoup]) -> None:
        self.main, self.matched = _main, _matched
        self.contents = [i for i in self.__class__.merge_children(self.main.contents, *[i.contents for i in self.matched]) if self.is_valid_entity(i)]
    
    def __bool__(self) -> bool:
        return bool(self.contents)

    def is_valid_entity(self, _entity:typing.Any) -> bool:
        if not getattr(_entity, 'is_stylestring', False):
            return _entity.name.lower() != 'br'
        return _entity.is_empty_string

    def prune_tree(self) -> None:
        if all(i.has_matches for i in self.contents if i.is_target_entity):
            self.contents = [i for i in self.contents if not i.is_target_entity]
        for i in self.contents:
            getattr(i, 'prune_tree', lambda :None)()
        self.contents = [i for i in self.contents if i or i.is_specialelem]

    def __repr__(self) -> str:
        _joined = '\n'.join(map(repr, self.contents))
        return f"<{self.main.name} {', '.join(a+'='+(b if isinstance(b, str) else ' '.join(b)) for a, b in self.main.attrs.items())} | matched({len(self.matched)})>{_joined}</{self.main.name}>"
    
    @classmethod
    def merge_children(cls, _main:typing.List[bs4.BeautifulSoup], *targets:typing.List[typing.List[bs4.BeautifulSoup]]) -> typing.Any:
        _c = [i for b in targets for i in b]
        return [cls._merge_trees(i, *_c) for i in _main if i != '\n' and not isinstance(i, bs4.Comment)]
    
    @classmethod
    def attr_extraction(cls, _obj:bs4.BeautifulSoup) -> _elem_attrs:
        return _elem_attrs(_obj.name, _obj.attrs)
    
    @classmethod
    def basic_attr_extraction(cls, _obj:bs4.BeautifulSoup) -> _basic_attrs:
        return _basic_attrs(_obj.name, _obj.attrs)
    
    @classmethod
    @tree_merge_utilites.validate_obj
    def merge_trees(cls, _main:bs4.BeautifulSoup, *targets:typing.List[bs4.BeautifulSoup]) -> typing.Any:
        if _main.name == 'body':
            return cls(_main, targets)
        _d = [(i, a, cls.attr_extraction(a)) for i, a in enumerate([_main, *targets])]
        _all_keys = {i for *_, b in _d for i in b}
        print('all keys above', _all_keys)
        new_d = [(*a, b, [b[i] for i in _all_keys]) for *a, b in _d]
        grouped = [(a, list(b)) for a, b in itertools.groupby(sorted(new_d, key=lambda x:x[-1]), key=lambda x:x[-1])]
        _r = [{j:k for j, k, *_ in b} for _, b in grouped if any(not i[0] for i in b)][0]
        return cls(_r[0], [b for a, b in _r.items() if a])
        
    @classmethod
    @tree_merge_utilites.validate_obj
    def _merge_trees(cls, _main, *targets) -> typing.Callable:
        if _main.name == 'body':
            return cls(_main, targets)
        return cls(_main, [i for i in targets if cls.attr_extraction(_main).__new_eq__(cls.attr_extraction(i))])
        
if __name__ == '__main__':
    #tests below
    a, b, c = bs4.BeautifulSoup(open('test_input.html').read(), 'html.parser').body, bs4.BeautifulSoup(open('test_input_2.html').read(), 'html.parser').body, bs4.BeautifulSoup(open('test_input_3.html').read(), 'html.parser').body
    _r = StyleTree.merge_trees(a, b)
    t = StyleTree.merge_trees(bs4.BeautifulSoup(open('test_input_5.html').read(), 'html.parser'))
    print(_basic_attrs.compute_class_score(*[i.tree_attrs for i in t.contents[0].contents[0].contents]))
    print(_r)
  
    @tree_merge_utilites.timeit
    def merge1():
        _ = StyleTree.merge_trees(a, b, c)
    
    @tree_merge_utilites.timeit
    def merge2():
        _ = StyleTree._merge_trees(a, b, c)
    

    merge1()
    merge2()
    
    LookupPath.generate_path(a, b, c)

    
