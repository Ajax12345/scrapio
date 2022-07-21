import bs4, matcher_utilites
import requests, typing, itertools

def create_graph(d:soup, _graph:nx.Graph, _start = None) -> None:
    for i in getattr(d, 'contents', []):
        if i != '\n':
            _val = next(f) if i.name is not None else getattr(i, 'text', i)
            _graph.add_edge(0 if _start is None else _start, _val)
            if i.name is not None and hasattr(i, 'contents'):
                create_graph(i, _graph, _val)
        
class Matcher:
    @classmethod
    def combinations(cls, d:list, _l:int, _c:list = []) -> typing.List:
        if len(_c) == _l:
            yield [_c, [i for i in d if i not in _c]]
        else:
            for i in d:
                if i not in _c:
                    yield from cls.combinations(d, l, _c+[i])

    @classmethod
    def compute_length(cls, _node) -> int:
        _k = [i for i in _node.contents if not isinstance(i, bs4.element.NavigableString)]
        return 1 + (0 if not _k else sum(map(cls.compute_length, _k)))

    @classmethod
    def equal_length_comp(cls, _c1, _c2, a) -> int:
        if not _c1 and not _c2:
            return 0
        _start = [sum([cls.compute_score(j, k) for j, k in zip(_c1, _c2)])]
        for i, h in enumerate(_c2):
            _start.append(1+sum(cls.compute_length(k) for k in _c2[:i])+cls.compute_score(a, h)+sum(cls.compute_length(l) for l in _c2[i+1:]))
        return min(_start)

    @classmethod
    def compute_score(cls, a, b) -> int:
        _c1, _c2 = [i for i in a.contents if not isinstance(i, bs4.element.NavigableString)], [i for i in b.contents if not isinstance(i, bs4.element.NavigableString)] 
        if not _c1 and not _c2:
            return 0
        if len(_c1) == len(_c2):
            return cls.equal_length_comp(_c1, _c2, a)
        _h1, _h2 = dict(zip(range(len(_c1)), _c1)), dict(zip(range(len(_c2)), _c2))
        l1, s1 = _h1 if len(_h1) > len(_h2) else _h2, _h1 if len(_h1) < len(_h2) else _h2
        _combs, _r = list(cls.combinations(list(l1), len(s1))), []
        for _j, _k in _combs:
            j, k = [l1[i] for i in _j], [l1[i] for i in _k]
            new_r = cls.equal_length_comp(list(s1.values()), j, a)
            new_start = sum(cls.compute_length(i) for i in k)
            _decend = []
            for i, h in enumerate(k):
                if cls.compute_length(a) < cls.compute_length(h):
                    _decend.append(1+sum(cls.compute_length(y) for y in k[:i])+cls.compute_score(a, h)+sum(cls.compute_length(l) for l in k[i+1:]))
            _r.append(new_r+min([new_start, 0 if not _decend else min(_decend)]))
        return min(_r)
        
    @classmethod
    def _scan_data(cls, _input, _path = []) -> typing.Any:
        if not isinstance(_input, bs4.element.NavigableString):
            _new_content = [i for i in _input.contents if not isinstance(i, bs4.element.NavigableString)]
            if len(_new_content) > 1:
                _match = cls.find_trees(_new_content)
                yield _match
            for i in _new_content:
                yield from cls._scan_data(i, _path+[_input])
        
    @classmethod
    def label_tree(cls, _tree:bs4.BeautifulSoup) -> typing.List[typing.List[int]]:
        _l = itertools.count(1)
        def _label(_tree, _path = []):
            _new_content = [i for i in _tree.contents if not isinstance(i, bs4.element.NavigableString)]
            if not _new_content:
                yield _path+[next(_l)]
            else:
                _c = next(_l)
                for i in _new_content:
                    yield from _label(i, _path+[_c])
        return list(_label(_tree))

    @classmethod
    def load_sample(cls, _filename) -> typing.Any:
        return cls._scan_data(soup(open(_filename).read(), 'html.parser'))

class _node:
    def __init__(self, _is_leaf:bool, _hash:int, _tag:str) -> None:
        self.is_leaf, self.hash, self.tag = _is_leaf, _hash, _tag
    def __repr__(self) -> str:
        return f'Node({self.hash}, is_leaf={self.is_leaf}, tag={self.tag})'    

class Tree_Row:
    def __init__(self, _paths:typing.List[list], _tags:dict, _leafs:dict) -> None:
        self.paths, self.tags, self.leafs = _paths, _tags, _leafs
    @property
    def segment(self):
        _parents, _leafs = [], []
        for [i] in self.paths:
            if self.leafs[i]:
                _leafs.append(i)
            else:
                _parents.append(i)
        #print('in segment', _parents, _leafs)
        return _parents, _leafs
    def __len__(self) -> int:
        _parents, _leafs = self.segment
        return len(_parents)+len(list(itertools.groupby(sorted(_leafs, key=lambda x:self.tags[x]), key=lambda x:self.tags[x])))
        
    def __sub__(self, _tree_row) -> int:
        [_parents1, _leafs1], [_parents2, _leafs2] = self.segment, _tree_row.segment
        p1, p2 = len(_parents1), len(_parents2)
        if p1 == p2:
            children1, children2 = {self.tags[i]:i for i in _leafs1}, {_tree_row.tags[i]:i for i in _leafs2}
            _ch1, _ch2 = [i for i in _leafs1 if self.tags[i] not in children2], [i for i in _leafs2 if _tree_row.tags[i] not in children1]
            return abs(len(list(itertools.groupby(sorted(_ch1, key=lambda x:self.tags[x]), key=lambda x:self.tags[x]))) - len(list(itertools.groupby(sorted(_ch2, key=lambda x:_tree_row.tags[x]), key=lambda x:_tree_row.tags[x]))))

        [lp, sp, _tp], [ll, ls, _ts] = [_parents1, _leafs1, self.tags] if p1 > p2 else [_parents2, _leafs2, _tree_row.tags], [_parents1, _leafs1, self.tags] if p1 < p2 else [_parents2, _leafs2, _tree_row.tags]
        l1, l2, l3 = len(lp), len(ls), len(ll)
        _combos = [itertools.combinations(ls, i) for i in range(1, (lambda x:x if x < l2 else l2)(abs(p1-p2))+1)]
        if not _combos:
            return abs(p1 - p2) + len(list(itertools.groupby(sorted(sp, key=lambda x:_tp[x]), key=lambda x:_tp[x])))
        _results, tp = [], {_tp[i]:i for i in sp}
        for combo in _combos:
            for g in combo:
                _missing = [i for i in ls if i not in g]
                ts = {_ts[i]:i for i in _missing}
                _ch1, _ch2 = [i for i in sp if _tp[i] not in ts], [i for i in _missing if _ts[i] not in tp]
                _val = abs(l1 - (l3+len(g))) + abs(len(list(itertools.groupby(sorted(_ch1, key=lambda x:_tp[x]), key=lambda x:_tp[x]))) - len(list(itertools.groupby(sorted(_ch2, key=lambda x:_ts[x]), key=lambda x:_ts[x]))))
                if not _val:
                    return 0
                _results.append(_val)
        
        return min(_results)
        
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.paths})'
    @classmethod
    def obj_tree_row(cls, _paths:typing.List[list], _obj) -> typing.Callable:
        return cls(_paths, _obj.tags, _obj.leafs)

class _V2:
    @classmethod
    @matcher_utilites.format_paths
    def label_tree(cls, _tree:bs4.BeautifulSoup) -> typing.List[typing.List[int]]:
        _l = itertools.count(1)
        def _label(_tree, _path = []):
            _new_content = [i for i in _tree.contents if not isinstance(i, bs4.element.NavigableString)]
            if not _new_content:
                yield _path+[_node(True, next(_l), _tree.name)]
            else:
                _c = next(_l)
                for i in _new_content:
                    yield from _label(i, _path+[_node(False, _c, _tree.name)])
        return list(_label(_tree))
    
    @classmethod
    @matcher_utilites.format_paths
    def label_tree_merged(cls, _tree) -> typing.List[typing.List[int]]:
        _l = itertools.count(1)
        def _label(_tree, _path = []):
            _new_content = [i for i in _tree.contents if not i.is_stylestring]
            if not _new_content:
                yield _path+[_node(True, next(_l), _tree.name)]
            else:
                _c = next(_l)
                for i in _new_content:
                    yield from _label(i, _path+[_node(False, _c, _tree.name)])
        return list(_label(_tree))
        
    @classmethod
    def _label_tree(cls, _tree:bs4.BeautifulSoup) -> typing.List[typing.List[int]]:
        _l = itertools.count(1)
        def _label(_tree, _path = []):
            _new_content = [i for i in _tree.contents if not isinstance(i, bs4.element.NavigableString)]
            if not _new_content:
                yield _path+[next(_l)]
            else:
                _c = next(_l)
                for i in _new_content:
                    yield from _label(i, _path+[_c])
        return list(_label(_tree))
    @classmethod
    def eval_row(cls, _row:typing.List[int], p_obj) -> int:
        pass
    @classmethod
    def _h_compare(cls, t_shift:int, b_shift:int, l1:typing.List[typing.List[int]], l2:typing.List[typing.List[int]]) -> int:
        top_r, bottom_r = sum(len(i) for i in l2[:t_shift]), 0 if not b_shift else sum(len(i) for i in l2[-b_shift:])
        new_l = l2[t_shift:] if not b_shift else l2[t_shift:-b_shift]
        return top_r + bottom_r + sum(abs(len(a) - len(b)) for a, b in zip(new_l, l1))
    @classmethod
    def h_compare(cls, t_shift:int, b_shift:int, l1:Tree_Row, l2:Tree_Row) -> None:
        top_r, bottom_r = sum(len(i) for i in l2[:t_shift]), 0 if not b_shift else sum(len(i) for i in l2[-b_shift:])
        new_l = l2[t_shift:] if not b_shift else l2[t_shift:-b_shift]
        _k = sum(a - b for a, b in zip(new_l, l1))
        _vals = top_r + bottom_r + _k
        return _vals
    @classmethod
    def _v2_compare(cls, _l1:typing.List[typing.List[int]], _l2:typing.List[typing.List[int]]) -> int:
        l1, l2 = list(itertools.zip_longest(*sorted(_l1, key=len, reverse=True))), list(itertools.zip_longest(*sorted(_l2, key=len, reverse=True)))
        s_1, s_2 = len(l1), len(l2)
        large, small = l1 if s_1 > s_2 else l2, l2 if s_2 < s_1 else l1
        _cast_large, _cast_small = [[set(k) for _, k in itertools.groupby(sorted(filter(None, i)))] for i in large], [[set(k) for _, k in itertools.groupby(sorted(filter(None, i)))] for i in small]
        if s_1 == s_2:
            return cls._h_compare(0, 0, _cast_small, _cast_large)
        final_result = [cls._h_compare(i, abs(s_1-s_2) - i, _cast_small, _cast_large) for i in range(abs(s_1-s_2)+1)]
        return min(final_result)
    
    @classmethod
    def v2_compare(cls, _l1, _l2) -> int:
        l1, l2 = list(itertools.zip_longest(*sorted(_l1, key=len, reverse=True))), list(itertools.zip_longest(*sorted(_l2, key=len, reverse=True)))
        s_1, s_2 = len(l1), len(l2)
        large, small = l1 if s_1 > s_2 else l2, l2 if s_2 < s_1 else l1
        obj_large, obj_small = _l1 if s_1 > s_2 else _l2, _l2 if s_2 < s_1 else _l1
        _cast_large, _cast_small = [Tree_Row.obj_tree_row([set(k) for _, k in itertools.groupby(sorted(filter(None, i)))], obj_large) for i in large], [Tree_Row.obj_tree_row([set(k) for _, k in itertools.groupby(sorted(filter(None, i)))], obj_small) for i in small]
        
        if s_1 == s_2:
            return cls.h_compare(0, 0, _cast_small, _cast_large)
        final_result = [cls.h_compare(i, abs(s_1-s_2) - i, _cast_small, _cast_large) for i in range(abs(s_1-s_2)+1)]
        return min(final_result)
        

if __name__ == '__main__':
    node1, node2 = bs4.BeautifulSoup(open('test_input_2.html').read(), 'html.parser').find_all('div', {'class':'test'})
    print(_V2._v2_compare(_V2._label_tree(node1), _V2._label_tree(node2)))
    print(_V2.v2_compare(_V2.label_tree(node1), _V2.label_tree(node2)))
    import tree_merger
    nodes = bs4.BeautifulSoup(open('test_input_5.html').read(), 'html.parser').find_all('div', {'class':'fusion-layout-column'})
    nodes = [i for i in nodes if i != '\n']
    _nd = _V2.label_tree(nodes[0])
    r = [_V2.v2_compare(_nd, _V2.label_tree(i)) for i in nodes]
    print(r)
    _d  = tree_merger.StyleTree.merge_trees(bs4.BeautifulSoup(open('test_input_5.html').read(), 'html.parser').find('div', {'class':'fusion-builder-row fusion-row '})).contents
    _nd = _V2.label_tree_merged(_d[0])
    _r = [_V2.v2_compare(_nd, _V2.label_tree_merged(i)) for i in _d]
    print(_r)
    
    @matcher_utilites.timeit
    def __outer1():
        _ = _V2.v2_compare(_V2.label_tree(node1), _V2.label_tree(node2))
    
    @matcher_utilites.timeit
    def __outer2():
        _ = _V2._v2_compare(_V2._label_tree(node1), _V2._label_tree(node2))

    __outer1()
    __outer2()
