import typing, requests, cssutils
import style_parser_utilites
import logging, re

cssutils.log.setLevel(logging.CRITICAL)

class entity_type:
    _symbols = {"class":".", "tag":"", 'id':'#'}
    @property
    def entity_name(self):
        return self.__class__.__name__[1:]
    def __repr__(self) -> str:
        return f'{self.__class__._symbols[self.entity_name]}{self.name}'

class _class(entity_type):
    def __init__(self, _name:str) -> None:
        self.name = _name
    
class _id(entity_type):
    def __init__(self, _name:str) -> None:
        self.name = _name

class _tag(entity_type):
    def __init__(self, _name:str) -> None:
        self.name = _name

class DescriptorBlock:
    def __init__(self, *args:typing.List) -> None:
        self.descriptors = args
    def __iter__(self) -> typing.Generator:
        yield from self.descriptors
    def __len__(self) -> int:
        return len(self.descriptors)
    def __repr__(self) -> str:
        return ''.join(map(str, self.descriptors))
    def __str__(self) -> str:
        return repr(self)

class Descriptor:
    _ident = {'.':_class, '#':_id}
    @style_parser_utilites.contextualize_idents
    def __init__(self, _descriptor:typing.List[DescriptorBlock]) -> None:
        self.entities = _descriptor
    def __repr__(self) -> str:
        return '{}({})'.format(self.__class__.__name__, ' '.join(map(str, self.entities)))
    def __str__(self) -> str:
        return repr(self)
    def __eq__(self, _elems) -> bool:
        return
    
    @property
    def is_empty(self) -> bool:
        return bool(self.entities)
    def __len__(self) -> int:
        return len(self.entities)
    def __bool__(self) -> bool:
        return len(self.descriptor) == 1
    def __iter__(self) -> typing.Generator:
        yield from self.entities

class StyleRule:
    def __init__(self, _key:str, _value:str) -> None:
        self.key, self.value = _key, _value
    def __repr__(self) -> str:
        return f'{self.key}: {self.value};'
    def __str__(self) -> str:
        return repr(self)


class CSSRuleBlock:
    def __init__(self, _descriptor:str, _rules:typing.List[StyleRule]) -> None:
        self.rule_desc, self.rules = self.format_descriptor(_descriptor), _rules
    def descriptor_block(self, _block:str) -> DescriptorBlock:
        return DescriptorBlock(*[(lambda x:_tag(i) if not x else Descriptor._ident[x[0]](i[1:]))(re.findall('^[\.#]', i)) for i in re.findall('[\.#][\w\-]+|[\w\-]+', _block)])
    def format_descriptor(self, _descriptor:str) -> Descriptor:
        #print(_descriptor, re.split('[\s\+\>]+', _descriptor))
        #return Descriptor([(lambda x:_tag(i) if not x else Descriptor._ident[x[0]](i[1:]))(re.findall('^[\.#]', i)) for i in re.findall('[\.#][\w\-]+|[\w\-]+', _descriptor)])
        #print('split here', re.split('[\s\+\>]+', _descriptor))
        return Descriptor([self.descriptor_block(i) for i in re.split('[\s\+\>]+', _descriptor)])
        
    @classmethod
    def load_rule(cls, _rule:cssutils.css.CSSStyleRule) -> typing.Callable:
        return cls(_rule.selectorText, [StyleRule(i.name, i.value) for i in _rule.style])
    @classmethod
    def _load_rule(cls, _header:str, _rule:cssutils.css.CSSStyleRule) -> typing.Callable:
        return cls(_header, [StyleRule(i.name, i.value) for i in _rule]) 
    def __repr__(self) -> str:
        return str(self.rule_desc)+' {\n'+'\n'.join(f'\t{i}' for i in self.rules)+'\n}'
    def __str__(self) -> str:
        return repr(self)

class StyleSheet:
    """
    border-top-width
    border-top-style
    border-width
    background
    background-color
    width, height
    border-radius
    border-color
    text-align
    border-top
    border-bottom, border-bottom-width, border-bottom-style
    border-right, border-right-width, border-right-style
    border-left, border-left-width, border-left-style
    background-size,background-image 
    """ 
    @style_parser_utilites.filter_non_essential
    def __init__(self, _rules:typing.List[CSSRuleBlock]) -> None:
        self.rules = _rules
    def __repr__(self) -> str:
        return '{}(\n{}\n)'.format(self.__class__.__name__, "\n".join(map(str, self.rules)))
    def __iter__(self) -> typing.Generator:
        yield from self.rules
    def find_match(self, _desc, _elem_path) -> typing.List:
        pass
    def __getitem__(self, _elem_path) -> typing.List[CSSRuleBlock]:
        _r = []
        for rule in self.rules:
            _desc, _rules = rule.rule_desc, rule.rules
            if len(_desc) <= len(_elem_path) and self.find_match(_desc, _elem_path):
                _r.append(rule)
        return _r

    @classmethod
    @style_parser_utilites.load_urls
    @style_parser_utilites.filter_urls(remove={'googleapis'})
    def lookup_styles(cls, *urls:typing.List[str]) -> typing.Callable:
        #return cls([CSSRuleBlock.load_rule(i) for b in urls for i in cssutils.parseUrl(b).cssRules if isinstance(i, cssutils.css.CSSStyleRule)])
        _rules = [(re.split(',\s+|,', re.sub('\[\w+\=[^\]]+\]|:+[\w\-]+|\*', '', i.selectorText)), i.style) for b in urls for i in cssutils.parseUrl(b).cssRules if isinstance(i, cssutils.css.CSSStyleRule)]
        return cls([CSSRuleBlock._load_rule(i, a) for b, a in _rules for i in b if i])
    @classmethod
    def test_reader(cls) -> None:
        #return cls([CSSRuleBlock.load_rule(i) for i in cssutils.parseString(open('test_css.css').read()).cssRules if isinstance(i, cssutils.css.CSSStyleRule)])
        _rules = [(re.split(',\s+|,', re.sub('\[\w+\=[^\]]+\]|:+[\w\-]+|\s+\*|\*', '', i.selectorText)), i.style) for i in cssutils.parseString(open('test_css.css').read()).cssRules if isinstance(i, cssutils.css.CSSStyleRule)]
        #print('rules first part', _rules[:10])
        return cls([CSSRuleBlock._load_rule(i, a) for b, a in _rules for i in b if i])
    @classmethod
    def test_load_url(cls, _url) -> None:
        #return cls([CSSRuleBlock.load_rule(i) for i in cssutils.parseUrl(_url).cssRules if isinstance(i, cssutils.css.CSSStyleRule)])
        _rules = [(re.split(',\s+|,', re.sub('\[\w+\=[^\]]+\]|:\w+|\*', '', i.selectorText)), i.style) for i in cssutils.parseUrl(_url).cssRules if isinstance(i, cssutils.css.CSSStyleRule)]
        return cls([CSSRuleBlock._load_rule(i, a) for b, a in _rules for i in b if i])

if __name__ == '__main__':
    r = StyleSheet.test_load_url('https://www.crisismagazine.com/wp-content/thesis/skins/crisismag/css.css')
    #print(StyleSheet.test_reader())    