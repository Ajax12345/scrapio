import typing, urllib.parse
import itertools, functools
import converter_objs

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

    def __iter__(self) -> typing.Iterator:
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
            _r.append(list(self.main))
        elif self.main is not None:
            yield from self.main
        if self._children and _r:
            #_r.extend([list(i) for i in self._children.values()])
            _r.extend(list(self._flatten([list(i) for i in self._children.values()])))
            #need better way to flatten this
        else:
            for i in self._children.values():
                yield from i

        if _r:
            yield from _r

    def to_list(self) -> typing.List:
        def _to_list(_val:typing.Iterable) -> list:
            if isinstance(_val, dict):
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
    
    def __iter__(self) -> typing.Iterator:
        yield {'href':{'link':self.tree.tree_attrs['href']}}
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

    def __iter__(self) -> typing.Iterator:
        yield {'src':{'link':self.tree.tree_attrs['src']}}
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

    def __iter__(self) -> typing.Iterator:
        if self.records:
            if sum(i.is_singleton for i in self.records)/float(len(self.records)) >= 0.85:
                yield converter_objs.RecordRow.load_record_row([i for b in self.records for i in b])
            else:
                _flag = False
                for i in self.records:
                    if bool(i):
                        yield converter_objs.RecordRow.load_record_row(list(i))
                        _flag = True
                    elif _flag:
                        yield converter_objs.RecordRow.load_record_row(list(i))
                    else:    
                        yield from i
        
        yield from self.struct
        


class PatternMatcherHandler:
    @property
    def is_singleton(self) -> bool:
        return False

    def __bool__(self) -> bool:
        return self.is_singleton

    def to_dict(self, **kwargs) -> dict:
        return {'__pattern__':{'runs':[i.to_dict(**kwargs) for i in self.runs], 'contents':self.struct.to_dict(**kwargs)}, '__handler__':'_pattern'}

    def __iter__(self) -> typing.Iterator:
        '''
        raise Exception(f"'{self.__class__.__name__}' does not have an __iter__ yet")
        '''
        for i in self.runs:
            yield from i
        yield from self.struct


class MatchedRunHandler:
    @property
    def is_singleton(self) -> bool:
        return False

    def __bool__(self) -> bool:
        return self.is_singleton

    def to_dict(self, **kwargs) -> dict:
        return {'__run__':{'content':[i.to_dict(**kwargs) for i in self.run_objs]}, '__handler__':'_run'}

    def __iter__(self) -> typing.Iterator:
        for i in self.run_objs:
            yield  converter_objs.RunRow.load_run_row(list(i))