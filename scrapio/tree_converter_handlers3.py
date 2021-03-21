import typing, urllib.parse
import itertools, functools, itertools
import converter_objs, functools, json
import collections


def provide_group(_f:typing.Callable) -> typing.Callable:
    @functools.wraps(_f)
    def wrapper(_self, level = True) -> typing.Any:
        if level:
            yield converter_objs.Records.load_records(list(_f(_self)))
        else:
            yield from _f(_self)
    return wrapper

class DispatchHandler:
    @property
    def is_dispatch(self):
        return True

    @property
    def is_singleton(self) -> bool:
        _val_len = sum(1 if not getattr(i, 'is_specialstring', False) else i.allowed_depth() for i in self._vals)
        return _val_len < 2 and self.main is None and not self._children

    @property
    def has_vals(self):
        return bool(self._vals)

    def __bool__(self) -> bool:
        return bool(self._vals)

    def to_dict(self, **kwargs) -> dict:
        _c = {}
        if self._vals:
            _c['values'] = [i.to_dict(**kwargs) for i in self._vals]
        if self.main is not None:
            _c['main'] = self.main.to_dict(**kwargs)
        if self._children:
            _c['children'] = [b.to_dict(**kwargs) for b in self._children.values()]

        return {'__dispatch__':_c, '__handler__':'_dispatcher'}

    def _flatten(self, _vals:typing.List[typing.Any]) -> typing.Generator:
        for i in _vals:
            if isinstance(i, list):
                yield from self._flatten(i)
            else:
                yield i

    def __iter__(self, level = True) -> typing.Iterator:
        _r = []
        if self._vals:
            for i in self._vals:
                if getattr(i, 'is_specialstring', False):
                    a, *b = i
                    _r.append(a)
                    _r.extend(b)
                else:
                    _r.append(i)
        if self.main is not None and _r:
            _r.append(list(self.main.__iter__(level = True)))
        elif self.main is not None:
            yield from self.main.__iter__(level = level)
        if self._children and _r:
            #_r.extend([list(i) for i in self._children.values()])
            _r.extend(list(self._flatten([list(i.__iter__(level=True)) for i in self._children.values()])))
            #need better way to flatten this
        else:
            for i in self._children.values():
                yield from i.__iter__(level = level if not _r else True)

        if _r:
            yield from _r

    def to_list(self) -> typing.List:
        def _to_list(_val:typing.Iterable) -> list:
            if isinstance(_val, (converter_objs.a_Href_to_table, converter_objs.img_Src_to_table, converter_objs.img_Disp_to_table)):
                return _val
            return [getattr(i, 'to_list', lambda :_to_list(i))() for i in _val]
        return _to_list(self)
            

    def to_row(self, *args, **kwargs) -> typing.List[typing.Any]:
        _l = []
        for i in self._vals:
            if getattr(i, 'is_specialstring', False):
                a, b = i.to_row(*args, **kwargs)
                _l.extend([a, *b])
            else:
                _l.append(i.to_dict())
        return _l
            


class a_HrefHandler:
    @property
    def is_specialstring(self):
        return True
    
    def allowed_depth(self) -> int:
        if len(self.struct._vals) <= 1 and self.struct.main is None and not self.struct._children:
            return 1
        return 2

    def to_dict(self, **kwargs) -> dict:
        return {'__href__':{'link':(lambda x:self.tree.tree_attrs['href'] if x is None else urllib.parse.urljoin(x, self.tree.tree_attrs['href']))(kwargs.get('url')), 'content':self.struct.to_dict(**kwargs)}, '__handler__':'_href'}

    def to_row(self, *args, **kwargs) -> typing.Tuple:
        return {'href':{'link':self.tree.tree_attrs['href']}}, self.struct.to_row(*args, **kwargs)
    
    def __iter__(self, **_) -> typing.Iterator:
        #yield {'href':{'link':self.tree.tree_attrs['href']}}
        yield converter_objs.a_Href_to_table(self)
        yield from self.struct

    
class ImgHandler:
    @property
    def is_specialstring(self):
        return True

    def allowed_depth(self) -> int:
        if len(self.struct._vals) <= 1 and self.struct.main is None and not self.struct._children:
            return 1
        return 2

    def to_dict(self, **kwargs) -> dict:
        return {'__img__':{'src':(lambda x:self.tree.tree_attrs['src'] if x is None else urllib.parse.urljoin(x, self.tree.tree_attrs['src']))(kwargs.get('url')), 'content':self.struct.to_dict(**kwargs)}, '__handler__':'_img'}

    def to_row(self, *args, **kwargs) -> typing.Tuple:
        return {'src':{'link':self.tree.tree_attrs['src']}}, self.struct.to_row(*args, **kwargs)

    def __iter__(self, **_) -> typing.Iterator:
        yield converter_objs.img_Disp_to_table(self)
        yield converter_objs.img_Src_to_table(self)
        yield from self.struct

 


class StructuredRecordHandler:
    @property
    def is_structuredrecord(self):
        return True
    
    @property
    def is_singleton(self) -> bool:
        return False
    
    def __bool__(self) -> bool:
        return self.is_singleton

    def to_dict(self, **kwargs) -> dict:
        return {'__structured__':{'records':[i.to_dict(**kwargs) for i in self.records], 'content':self.struct.to_dict(**kwargs), 'name':self.name}, '__handler__':'_structrecord'}

    @property
    def _is_tr(self) -> bool:
        return getattr(self.name, 'lower', lambda :'')() == 'tr'

    @provide_group
    def __iter__(self, level = True) -> typing.Iterator:
        if self.records:
            if sum(i.is_singleton for i in self.records)/float(len(self.records)) >= 0.85 or self._is_tr:
                yield converter_objs.RecordRow.load_record_row([i for b in self.records for i in b])
            else:
                for i in self.records:
                    if bool(i):
                        yield converter_objs.RecordRow.load_record_row(list(i.__iter__(level=False)))
                    else:    
                        yield from i.__iter__(level=False)
        
        yield from self.struct.__iter__(level = True)
        


class PatternMatcherHandler:
    @property
    def is_singleton(self) -> bool:
        return False

    def __bool__(self) -> bool:
        return self.is_singleton

    def to_dict(self, **kwargs) -> dict:
        return {'__pattern__':{'runs':[i.to_dict(**kwargs) for i in self.runs], 'contents':self.struct.to_dict(**kwargs)}, '__handler__':'_pattern'}

    @provide_group
    def __iter__(self, level = True) -> typing.Iterator:
        '''
        raise Exception(f"'{self.__class__.__name__}' does not have an __iter__ yet")
        '''
        for i in self.runs:
            yield from i.__iter__(level = False)
        yield from self.struct.__iter__(level = True)


class MatchedRunHandler:
    @property
    def is_singleton(self) -> bool:
        return False

    def __bool__(self) -> bool:
        return self.is_singleton

    def to_dict(self, **kwargs) -> dict:
        return {'__run__':{'content':[i.to_dict(**kwargs) for i in self.run_objs]}, '__handler__':'_run'}

    
    def __iter__(self, level = True) -> typing.Iterator:
        for i in self.run_objs:
            yield converter_objs.RunRow.load_run_row(list(i.__iter__(level = False)))



def _clean_to_List(d:typing.List) -> typing.List:
    return list(filter(None, [_clean_to_List(i) if isinstance(i, list) else getattr(i, 'strip_val', i) for i in d]))
    
    
def outer_clean_to_List(d):
    return list(filter(None, [outer_clean_to_List(i) if isinstance(i, list) else i for i in d]))

'''
def clean_to_List(d:list) -> list:
    _table_count = itertools.count(1)
    def inner_clean(_d:list, _flag:bool = False, level:int = 0, root=False) -> list:
        if _flag:
            new_row = [i for a, b in itertools.groupby(list(filter(None, _d)), key=lambda x:isinstance(x, list)) for i in ([list(b)] if not a else b)]
            if root:
                return list(filter(lambda x:bool(x['content']), [{'table':next(_table_count), 'content':[[getattr(k, 'strip_val', k) for k in i]] if all(not isinstance(b, list) for b in i) else inner_clean(i, level=1)} for i in new_row]))
            return {'table':next(_table_count), 'content':[[getattr(k, 'strip_val', k) for k in i] if all(not isinstance(b, list) for b in i) else inner_clean(i, level=2) for i in new_row]}
        if level == 1:
            new_row = [i for a, b in itertools.groupby(list(filter(None, _d)), key=lambda x:isinstance(x, list)) for i in ([list(b)] if not a else b)]
            return list(filter(None, [[getattr(k, 'strip_val', k) for k in i] if all(not isinstance(k, list) for k in i) else inner_clean(i, level=2) for i in new_row]))
        return list(filter(None, [inner_clean(i, _flag=True, root=False) if isinstance(i, list) else getattr(i, 'strip_val', i) for i in _d]))
        
    return inner_clean(d, _flag=True, root=True)

'''
def filter_row(row:typing.List[typing.Any]) -> list:
    new_row = [i for i in row if i]
    return [getattr(a, 'to_payload', a) for i, a in enumerate(new_row) if all(b != a for b in new_row[:i])]

'''
def clean_to_List(d:list, url:str) -> list:
    _table_count = itertools.count(1)
    with open('invalid_attrs.json') as f:
        _forbidden = json.load(f)
    def inner_clean(_d:list, _flag:bool = False, level:int = 0, root=False, parent=0, table=0) -> list:
        if _flag:
            new_row = [i for a, b in itertools.groupby(list(filter(None, _d)), key=lambda x:isinstance(x, list)) for i in ([list(b)] if not a else b)]
            if root:
                print(new_row)
                print('-'*20)
                return list(filter(lambda x:bool(x['_content']), [(lambda x:{'table':x, 'name':f'Table{x}', '_content':[filter_row([k.format_payload(table=x, parent=parent, forbidden=_forbidden, url=url) for k in i])] if all(not isinstance(b, list) for b in i) else inner_clean(i, level=1, parent=x), 'content':x, 'storetype':'table', 'newtable':parent})(next(_table_count)) for i in new_row]))
            new_table = next(_table_count)
            return {'table':new_table, 'name':f'Table{new_table}', '_content':[filter_row([k.format_payload(table=new_table, parent=parent, forbidden=_forbidden, url=url) for k in i]) if all(not isinstance(b, list) for b in i) else inner_clean(i, level=2, parent=parent, table=new_table) for i in new_row], 'content':new_table, 'storetype':'table', 'newtable':parent}
        if level == 1:
            new_row = [i for a, b in itertools.groupby(list(filter(None, _d)), key=lambda x:isinstance(x, list)) for i in ([list(b)] if not a else b)]
            return list(filter(None, [filter_row([k.format_payload(table=table, parent=parent, forbidden=_forbidden, url=url) for k in i]) if all(not isinstance(k, list) for k in i) else inner_clean(i, level=2, parent=parent, table=table) for i in new_row]))
        return list(filter(None, filter_row([inner_clean(i, _flag=True, root=False, parent=parent, table=table) if isinstance(i, list) else i.format_payload(table=table, parent=parent, forbidden=_forbidden, url=url) for i in _d])))
    return inner_clean(d, _flag=True, root=True)
'''
'''

def clean_to_List(d:list, url:str) -> list:
    _table_count = itertools.count(1)
    with open('invalid_attrs.json') as f:
        _forbidden = json.load(f)   
    def inner_clean(_d, to_table = True, parent=0, table=0):
        if to_table:
            new_table = next(_table_count)
            def table_formation(row):
                freq = collections.defaultdict(int)
                for i in row:
                    freq[not isinstance(i, list)] += 1
                if freq[True] >= freq[False]:
                    return list(filter(None, [filter_row([k.format_payload(table=table, parent=parent, forbidden=_forbidden, url=url) if not isinstance(k, list) else inner_clean(k, to_table=True, parent = new_table) for k in row])]))
                return list(filter(None, [inner_clean(k, to_table=False, parent=new_table) if isinstance(k, list) else filter_row([k.format_payload(table=table, parent=parent, forbidden=_forbidden, url=url)]) for k in row]))

            return {'table':new_table, 'name':f'Table{new_table}', 'content':new_table, 'storetype':'table', 'newtable':parent, '_content':table_formation(_d)}
        
        return filter_row([k.format_payload(table=table, parent=parent, forbidden=_forbidden, url=url) if not isinstance(k, list) else inner_clean(k, to_table=True, table=parent, parent = parent) for k in _d])
    new_d = [i for a, b in itertools.groupby(d, key=lambda x:isinstance(x, list)) for i in ([list(b)] if not a else b)]
    return [inner_clean(i) for i in new_d]
'''


'''
def clean_to_List(d:list, url:str) -> list:
    _table_count = itertools.count(1)
    with open('invalid_attrs.json') as f:
        _forbidden = json.load(f)   
    def inner_clean(_d, to_table = True, parent=0, table=0):
        if to_table:
            new_table = next(_table_count)
            def table_formation(row):
                if any(not isinstance(i, list) for i in row):
                    return list(filter(None, [filter_row([k.format_payload(table=table, parent=parent, forbidden=_forbidden, url=url) if not isinstance(k, list) else inner_clean(k, to_table=True, parent = new_table) for k in row])]))
                return list(filter(None, [inner_clean(k, to_table=False, parent=new_table) if any(not isinstance(j, list) for j in k) else [inner_clean(k, to_table=True, parent=new_table)] for k in row]))
            return {'table':new_table, 'name':f'Table{new_table}', 'content':new_table, 'storetype':'table', 'newtable':parent, '_content':table_formation(_d)}
        return filter_row([k.format_payload(table=table, parent=parent, forbidden=_forbidden, url=url) if not isinstance(k, list) else inner_clean(k, to_table=True, table=parent, parent = parent) for k in _d])
    new_d = [i for a, b in itertools.groupby(d, key=lambda x:isinstance(x, list)) for i in ([list(b)] if not a else b)]
    return [inner_clean(i) for i in new_d]
'''

def clean_to_List(d:list, url:str) -> list:
    _table_count = itertools.count(1)
    with open('invalid_attrs.json') as f:
        _forbidden = json.load(f)   
    def inner_clean(_d, to_table = True, parent=0, table=0):
        if to_table:
            new_table = next(_table_count)
            def table_formation(row):
                freq = collections.defaultdict(int)
                for i in row:
                    freq[not isinstance(i, list)] += 1
                if freq[True] >= freq[False]:
                    return list(filter(None, [filter_row([k.format_payload(table=table, parent=parent, forbidden=_forbidden, url=url) if not isinstance(k, list) else inner_clean(k, to_table=True, parent = new_table) for k in row])]))
                new_result = []
                for k in row:
                    if not isinstance(k, list):
                        new_result.append(filter_row([k.format_payload(table=table, parent=parent, forbidden=_forbidden, url=url)]))
                    elif any(isinstance(j, list) for j in k):
                        if sum(isinstance(i, list) for i in k) > sum(not isinstance(i, list) for i in k):
                            new_result.append([inner_clean(k, to_table=True, parent=new_table)])
                        else:
                            new_result.append(list(filter(None, filter_row([i.format_payload(table=table, parent=parent, forbidden=_forbidden, url=url) if not isinstance(i, list) else inner_clean(i, to_table=True, parent=new_table) for i in k]))))
                        #new_result.append([inner_clean(k, to_table=True, parent=new_table)])
                    else:
                        new_result.append(inner_clean(k, to_table=False, parent=new_table))
                return list(filter(None, new_result))
                #return list(filter(None, [inner_clean(k, to_table=False, parent=new_table) if isinstance(k, list) else filter_row([k.format_payload(table=table, parent=parent, forbidden=_forbidden, url=url)]) for k in row]))

            return {'table':new_table, 'name':f'Table{new_table}', 'content':new_table, 'storetype':'table', 'newtable':parent, '_content':table_formation(_d)}
        
        return filter_row([k.format_payload(table=table, parent=parent, forbidden=_forbidden, url=url) if not isinstance(k, list) else inner_clean(k, to_table=True, table=parent, parent = parent) for k in _d])
    new_d = [i for a, b in itertools.groupby(d, key=lambda x:isinstance(x, list)) for i in ([list(b)] if not a else b)]
    return [inner_clean(i) for i in new_d]