import typing, json, urllib.parse

class IterationError(Exception):
    pass

class StyleString_payload:
    def __init__(self, _string:str, **kwargs) -> None:
        self.string, self.kwargs = _string, kwargs
    def __bool__(self) -> bool:
        return bool(self.string)
    def __eq__(self, _obj) -> bool:
        return isinstance(_obj, self.__class__) and self.string == _obj.string
    @property
    def to_payload(self) -> dict:
        return {'storetype':'text', 'content':self.string, 'table':self.kwargs['parent'], 'newtable':self.kwargs['table']}
    @property
    def strip_val(self):
        return self.string


class a_Href_payload:
    def __init__(self, _url:str, **kwargs) -> None:
        self.url, self.kwargs = _url, kwargs
    def __bool__(self) -> bool:
        return self.url not in self.kwargs['forbidden']['href']
    def __eq__(self, _obj) -> bool:
        return isinstance(_obj, self.__class__) and self.url == _obj.url
    @property
    def to_payload(self) -> dict:
        return {'storetype':'link', 'content':urllib.parse.urljoin(self.kwargs.get('url', ''), self.url), 'table':self.kwargs['parent'], 'newtable':self.kwargs['table']}

    @property
    def strip_val(self):
        return {'link':{'href':self.url}}


class img_Src_payload:
    def __init__(self, _url:str, **kwargs) -> None:
        self.url, self.kwargs, self.img_flag = _url, kwargs, True
    def __bool__(self) -> bool:
        return self.url not in self.kwargs['forbidden']['src']
    def __eq__(self, _obj) -> bool:
        return isinstance(_obj, self.__class__) and self.url == _obj.url and getattr(_obj, 'img_flag', False)
    @property
    def to_payload(self) -> dict:
        return {'storetype':'img', 'content':urllib.parse.urljoin(self.kwargs.get('url', ''), self.url), 'table':self.kwargs['parent'], 'newtable':self.kwargs['table']}

    @property
    def strip_val(self):
        return {'img':{'src':self.url}}

class img_Disp_payload:
    def __init__(self, _url:str, **kwargs) -> None:
        self.url, self.kwargs, self.img_flag = _url, kwargs, False
    def __bool__(self) -> bool:
        return self.url not in self.kwargs['forbidden']['src']
    def __eq__(self, _obj) -> bool:
        return isinstance(_obj, self.__class__) and self.url == _obj.url and hasattr(_obj, 'img_flag') and not _obj.img_flag
    @property
    def to_payload(self) -> dict:
        return {'storetype':'img_display', 'content':urllib.parse.urljoin(self.kwargs.get('url', ''), self.url), 'table':self.kwargs['parent'], 'newtable':self.kwargs['table']}

    @property
    def strip_val(self):
        return {'img':{'src':self.url}}

class a_Href_to_table:
    def __init__(self, _ref:typing.Callable) -> None:
        self.ref = _ref
    @property
    def strip_val(self) -> dict:
        return {'href':{'link':self.ref.tree.tree_attrs['href']}}
    def format_payload(self, **kwargs) -> a_Href_payload:
        return a_Href_payload(self.ref.tree.tree_attrs['href'], **kwargs)

class img_Src_to_table:
    def __init__(self, _ref:typing.Callable) -> None:
        self.ref = _ref
    @property
    def strip_val(self) -> dict:
        return {'src':{'link':self.ref.tree.tree_attrs['src']}}
    def format_payload(self, **kwargs) -> img_Src_payload:
        return img_Src_payload(self.ref.tree.tree_attrs['src'], **kwargs)

class img_Disp_to_table:
    def __init__(self, _ref:typing.Callable) -> None:
        self.ref = _ref
    @property
    def strip_val(self) -> dict:
        return {'src':{'link':self.ref.tree.tree_attrs['src']}}
    def format_payload(self, **kwargs) -> img_Src_payload:
        return img_Disp_payload(self.ref.tree.tree_attrs['src'], **kwargs)

class RecordRow:
    def __init__(self, _row:typing.List[typing.Any]) -> None:
        self.row = _row
    @classmethod
    def load_record_row(cls, _row:typing.List[typing.Any]) -> typing.Callable:
        return cls(_row)
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.row})'
    def __iter__(self) -> typing.Iterator:
        raise IterationError(f"'{self.__class__.__name__}' does not have an __iter__ yet")
    
    def to_list(self) -> typing.List:
        def _to_list(_val:typing.Iterable) -> list:
            if isinstance(_val, (a_Href_to_table, img_Src_to_table, img_Disp_to_table)):
                return _val
            return [getattr(i, 'to_list', lambda :_to_list(i))() for i in _val]
        return _to_list(self.row)

class RunRow:
    def __init__(self, _row:typing.List[typing.Any]) -> None:
        self.row = _row
    @classmethod
    def load_run_row(cls, _row:typing.List[typing.Any]) -> typing.Callable:
        return cls(_row)

    def to_list(self) -> typing.List:
        def _to_list(_val:typing.Iterable) -> list:
            if isinstance(_val, (a_Href_to_table, img_Src_to_table, img_Disp_to_table)):
                return _val
            return [getattr(i, 'to_list', lambda :_to_list(i))() for i in _val]
        return _to_list(self.row)

    def __iter__(self) -> typing.Iterable:
        raise IterationError(f"'{self.__class__.__name__}' does not have an __iter__ yet")

class Records:
    def __init__(self, _rows:typing.List[RecordRow]) -> None:
        self.rows = _rows
    def __iter__(self) -> typing.Iterator:
        yield from self.rows
    def __bool__(self) -> bool:
        return bool(self.rows)
    @classmethod
    def load_records(cls, _rows:typing.List[RecordRow] = []) -> typing.Callable:
        return cls(_rows)
    def __repr__(self) -> str:
        return '{}(\n{}\n)'.format(self.__class__.__name__, '\n'.join('\t'+repr(i)+',' for i in self.rows))
    
    def add_record(self, _record:RecordRow):
        self.rows.append(_record)

    def to_list(self) -> typing.List:
        def _to_list(_val:typing.Iterable) -> list:
            if isinstance(_val, (a_Href_to_table, img_Src_to_table, img_Disp_to_table)):
                return _val
            return [getattr(i, 'to_list', lambda :_to_list(i))() for i in _val]
        return _to_list(self.rows)


