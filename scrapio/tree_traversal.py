import tree_matcher, tree_merger
import typing, style_parser, copy
from bs4 import BeautifulSoup as soup
import collections, itertools

class Dispatch:
    def __init__(self, _main = None) -> None:
        self._vals, self._children, self._c, self.main = [], {}, 0, _main
    def add_val(self, *args:typing.List[typing.Any]) -> None:
        self._vals.extend(list(args))
    def __call__(self, _main = None) -> typing.Callable:
        _c = self.__class__(_main = _main)
        self._c += 1
        self._children[self._c] = _c
        return _c
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._vals}, {self._children})'
    @classmethod
    def new_dispatch(cls, _main=None) -> typing.Callable:
        return cls(_main)


class ElemPath:
    def __init__(self, _paths=[]) -> None:
        self._path = _paths
    def __getitem__(self, _ind:int) -> typing.Callable:
        return self._path[_ind] if isinstance(_ind, int) else self.__class__(self._path[_ind.start if _ind.start is not None else 0:_ind.stop if _ind.stop is not None else len(self._path):_ind.step if _ind.step is not None else 1])
    def __len__(self) -> int:
        return len(self._path)
    def __bool__(self) -> bool:
        return bool(self._path)
    def __iter__(self) -> typing.Generator:
        yield from self._path
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({len(self._path)})'

class StructuredContent:
    def __init__(self) -> None:
        self.target_tags = {'table', 'tbody', 'thead', 'tr', 'ul', 'dl'}
    def __contains__(self, _tree) -> bool:
        return _tree.main.name in self.target_tags

class Blacklisted:
    def __init__(self) -> None:
        self.target_tags = {'button', 'input', 'form', 'script', 'style', 'link'}
    def __contains__(self, _tree) -> bool:
        return _tree.main.name in self.target_tags

class IgnoreElems:
    def __init__(self) -> None:
        self.rules = [(lambda x:x == '\n', 'new_line'), (lambda x:x.is_stylestring, 'stylestring')]
    def __getitem__(self, _elem) -> str:
        return (lambda x:'record' if not x else x[0])([b for a, b in self.rules if a(_elem)])



def quick_traverse(d, c = []) -> typing.Generator:
    _c = c+[d.tree_attrs]
    yield ElemPath(_c)
    for i in d.contents:
        if not i.is_stylestring:
            yield from quick_traverse(i, _c)


class __StyleString:
    @property
    def is_stylestring(self):
        return True
    def __eq__(self, _obj) -> bool:
        return getattr(_obj, 'is_stylestring', False)
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}>'

    
def traverse_dom(tree:tree_merger.StyleTree, page_style:style_parser._StyleSheet, struct:Dispatch, search_style:bool = True, path = []):
    structured_content = StructuredContent()
    blacklisted, ignore_elems = Blacklisted(), IgnoreElems()

    class MatchedRun:
        def __init__(self, _runs:typing.List[Dispatch]) -> None:
            self.run_objs = _runs
        @classmethod
        def load_run(cls, _run:list, page_source, path) -> typing.Callable:
            _all_runs = []
            for i in _run:
                _dispatch = Dispatch.new_dispatch()
                for b in i:
                    traverse_dom(b, page_source, _dispatch, path = path)
                _all_runs.append(_dispatch)
            return cls(_all_runs)
        def __repr__(self) -> str:
            return f'<{self.__class__.__name__}>'
            

    class PatternMatcher:
        def __init__(self, runs:typing.List[MatchedRun], _dispatch:Dispatch) -> None:
            self.runs, self.struct = runs, _dispatch
        @classmethod
        def load_detected_run(cls, matched, nested:list, style_page, _path:list) -> typing.Callable:
            _runs = [MatchedRun.load_run([[j for k in nested[a:b] for j in k] for a, b in i], style_page, _path) for i in matched]
            _detached_dispatch, _start = Dispatch.new_dispatch(), 0
            for a, b in sorted([i for g in matched for i in g]):
                for l in [i for j in nested[_start:a] for i in j]:
                    traverse_dom(l, style_page, _detached_dispatch, _path)
                _start = b
            for l in [i for j in nested[_start:len(nested)] for i in j]:
                traverse_dom(l, style_page, _detached_dispatch, _path)
            return cls(_runs, _detached_dispatch)
            
        def __repr__(self) -> str:
            return f'<{self.__class__.__name__}>'

    class a_Href:
        def __init__(self, _tree, _struct:Dispatch) -> None:
            self.tree, self.struct = _tree, _struct
        @classmethod
        def load_special(cls, _tree, _page_style:style_parser._StyleSheet, _path:list) -> typing.Callable:
            _features = collections.defaultdict(list)
            _a_struct, _children = Dispatch.new_dispatch(), []
            for i in _tree.contents:
                _features[ignore_elems[i]].append(i)
            
            _a_struct.add_val(*_features.get('stylestring', []))
            for i in _features.get('record', []):
                _temp_struct = Dispatch.new_dispatch()
                _ = traverse_dom(i, _page_style, _temp_struct, path = _path)
                _children.append(_temp_struct)
            return cls(_tree, _temp_struct)
        def __repr__(self) -> str:
            return f'<{self.__class__.__name__} href="{self.tree.main.attrs.get("href")}"'
            
    class _Img:
        def __init__(self, _tree, _struct:Dispatch) -> None:
            self.tree, self.struct = _tree, _struct
        @classmethod
        def load_special(cls, _tree, _page_style:style_parser._StyleSheet, _path:list) -> typing.Callable:
            _features = collections.defaultdict(list)
            _a_struct, _children = Dispatch.new_dispatch(), []
            for i in _tree.contents:
                _features[ignore_elems[i]].append(i)
            
            _a_struct.add_val(*_features.get('stylestring', []))
            for i in _features.get('record', []):
                _temp_struct = Dispatch.new_dispatch()
                _ = traverse_dom(i, _page_style, _temp_struct, path = _path)
                _children.append(_temp_struct)
            return cls(_tree, _temp_struct)
        def __repr__(self) -> str:
            return f'<{self.__class__.__name__} src="{self.tree.main.attrs.get("src")}"'
    class SpecialElements:
        def __init__(self, *args, **kwargs) -> None:
            self.a, self.img = a_Href, _Img
        def __contains__(self, _tree) -> bool:
            return hasattr(self, _tree.main.name)
        def __call__(self, _tree, _page_style, _path) -> typing.Any:
            return getattr(self, _tree.main.name).load_special(_tree, _page_style, _path)

    special_elems = SpecialElements()

    class StructuredRecord:
        def __init__(self, _records:typing.List[Dispatch], _struct:Dispatch, _attrs:list) -> None:
            self.records, self.struct, self.attrs = _records, _struct, _attrs
        @classmethod
        def load_detected_records(cls, _records:list, _struct:Dispatch, _path:list, _page_style:style_parser._StyleSheet) -> typing.Callable:
            _features = collections.defaultdict(list)
            for i in _records:
                _features[ignore_elems[i]].append(i)
            
            _struct.add_val(*_features.get('stylestring', []))
            _rows, _attrs = [], []
            for i in _features.get('record', []):
                _row_dispatch = Dispatch.new_dispatch()
                _ = traverse_dom(i, _page_style, _row_dispatch, path=_path)
                _rows.append(_row_dispatch)
                _attrs.append(i.tree_attrs)
            
            return cls(_rows, _struct, _attrs)
        def __repr__(self) -> str:
            return f'<{self.__class__.__name__}, {len(self.records)} row{"s" if len(self.records) != 1 else ""}>'
    
   
    def record_match(_records) -> bool:
        return bool(tree_merger._basic_attrs.compute_class_score([i.tree_attrs for i in _records]))
    
    def pairwise_match(_l1:list, _l2:list) -> bool:
        return all(a == b for a, b in zip(_l1, _l2))

    
         
    def paired_groups(_contents:list) -> typing.List:
        _attrs = [__StyleString() if i.is_stylestring else i.basic_tree_attrs for i in _contents]
        return [(a, list(b)) for a, b in itertools.groupby(_contents)]
    
    def is_distinct(_contents:list) -> bool:
        return any(_contents[0].main.name != i.main.name for i in _contents[1:]) or any(len(i.basic_tree_attrs.basic_attr_header) > 1 for i in _contents) 
    
    def test_get_groups(start, end, run, _len, _splice, step = 1):
        if all(a == b for a, b in zip(_splice, run[start+step:end+step])):
            yield (start+step, end+step)
        if end + step < _len:  
            yield from test_get_groups(start, end, run, _len, _splice, step+1)
            
    def group_runs(d, start, c = []):
        print('matching against', start)
        _r = [i for i in d if all(all(l <= j or k >= d for j, d in start) for k, l in i) and i not in c]
        return _r

    def not_substring(a, b):
        return all(all(l <= j or k >= d for j, d in a) for k, l in b) 

    def pattern_match(d:list) -> list:
        _l, _results = len(d), []
        for i in range(_l):
            for b in range(i+1, _l):
                _c = [(i, b), *test_get_groups(i, b, d, _l, d[i:b])]
                if len(_c) > 1 and all(_c[i][-1] <= _c[i+1][0] for i in range(len(_c) - 1)):
                    _results.append(_c)
    
        _new_l = sorted([max(list(b), key=lambda x:max([k - j for j, k in x])) for _, b in itertools.groupby(sorted(_results, key=lambda x:x[0][0]), key=lambda x:x[0][0])], key=lambda x:sum(g - h for h, g in x), reverse=True)
        return [a for i, a in enumerate(_new_l) if all(not_substring(a, c) for c in _new_l[:i])]
 

    def handle_ind_tree(_tree1, strc, p_style, _path1) -> None:
        if p_style[ElemPath(_path1)]:
            _new_strc = strc()
            for i in _tree1.contents:
                traverse_dom(i, p_style, _new_strc, _path1)
        else:
            for i in _tree1.contents:
                traverse_dom(i, p_style, strc, _path1)

    def parse(_tree:tree_merger.StyleTree, _struct:Dispatch, _page_style, _path:list = []) -> None:
        if _tree.is_stylestring or _tree not in blacklisted:
            if _tree.is_stylestring:
                _struct.add_val(_tree)
            else:
                _new_path = _path+[_tree.tree_attrs]
                if _tree in structured_content:
                    _record_struct = Dispatch.new_dispatch()
                    _ = _struct(StructuredRecord.load_detected_records(_tree.contents, _record_struct, _new_path, _page_style)) 
                elif _tree in special_elems:
                    _struct.add_val(special_elems(_tree, _page_style, _new_path))
                elif len(_tree.contents) > 1 and record_match(_tree.contents):
                    _record_struct = Dispatch.new_dispatch()
                    _ = _struct(StructuredRecord.load_detected_records(_tree.contents, _record_struct, _new_path, _page_style)) 
                elif len(_tree.contents) > 1 and is_distinct(_tree.contents):
                    _keys, _vals = zip(*paired_groups(_tree.contents))
                    _matched = pattern_match(_keys)
                    if not _matched:
                        handle_ind_tree(_tree, _struct, _page_style, _path)
                    else:
                        _iter_content = iter(_tree.contents)
                        _nested_content = [[next(_iter_content) for _ in k] for k in _vals]
                        _ = _struct(PatternMatcher.load_detected_run(_matched, _nested_content, _page_style, _new_path))
                
                elif len(_tree.contents) > 1:
                    pass
                else: 
                    
                    if _page_style[ElemPath(_new_path)]:
                        _new_struct = _struct()
                        _ = traverse_dom(_tree, _page_style, _new_struct, search_style = _search_style, path = _new_path)
                    else:
                        pass
    
    parse(tree, struct, page_style, _path = path)
    

class TraverseDom:
    @classmethod
    def parse_tree(cls, _tree:tree_merger.StyleTree, _page_style:style_parser._StyleSheet, search_style:bool = True) -> typing.Callable:
        _struct = Dispatch.new_dispatch()
        traverse_dom(_tree, _page_style, _struct, search_style = search_style)
        return _struct




if __name__ == '__main__':
    import requests
    #r = list(quick_traverse(tree_merger.StyleTree.merge_trees(soup(requests.get('https://www.premierleague.com/players/10905/Che-Adams/overview').text, 'html.parser').body)))
    #print(tree_merger.StyleTree.merge_trees(soup(open('test_input_5.html').read(), 'html.parser').body))
    #r = list(quick_traverse(tree_merger.StyleTree.merge_trees(soup(open('test_input_5.html').read(), 'html.parser').body)))
    #print(r)
    #_styles = style_parser._StyleSheet.load_string(open('test_css.css').read())
    #print(_styles)
    #print(_styles[r[-1]])
    #print(_styles)
    #print(r[1]._path)
    def test_get_groups(start, end, run, _len, _splice, step = 1):
        if all(a == b for a, b in zip(_splice, run[start+step:end+step])):
            yield (start+step, end+step)
        if end + step < _len:  
            yield from test_get_groups(start, end, run, _len, _splice, step+1)
            
    def group_runs(d, start, c = []):
        print('matching against', start)
        _r = [i for i in d if all(all(l <= j or k >= d for j, d in start) for k, l in i) and i not in c]
        return _r

    def not_substring(a, b):
        return all(all(l <= j or k >= d for j, d in a) for k, l in b) 

    def pattern_match():
        #d = [100, 1, 2, 3, 1, 2, 3, 5, 6, 7, 5, 6, 7, 500, 10, 11, 12, 13, 14, 10, 11, 12, 13, 14]
        #d = [60, 61, 60, 61, 1, 2, 3, 1, 2, 3, 60, 61, 60, 61]
        d = [60, 1, 60, 1, 50, 50, 50]
        _l, _results = len(d), []
        for i in range(_l):
            for b in range(i+1, _l):
                _c = [(i, b), *test_get_groups(i, b, d, _l, d[i:b])]
                if len(_c) > 1 and all(_c[i][-1] <= _c[i+1][0] for i in range(len(_c) - 1)):
                    _results.append(_c)
    
        _new_l = sorted([max(list(b), key=lambda x:max([k - j for j, k in x])) for _, b in itertools.groupby(sorted(_results, key=lambda x:x[0][0]), key=lambda x:x[0][0])], key=lambda x:sum(g - h for h, g in x), reverse=True)
        return [a for i, a in enumerate(_new_l) if all(not_substring(a, c) for c in _new_l[:i])]
        #print(group_runs(_new_l, _new_l[3]))
     
                    

    print(pattern_match())
   
 

    
