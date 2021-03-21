import requests, json, contextlib
from bs4 import BeautifulSoup as soup
import random, typing, functools

@contextlib.contextmanager
def refresh_proxies(_code = None, _with_proxy=False):
    with open('proxies.json') as f:
        _d = json.load(f)
    #d = soup(requests.get('https://www.sslproxies.org/').text if not _d or _with_proxy else requests.get('https://www.sslproxies.org/', proxies={'https':(lambda x:f'https://{x["ip"]}:{x["port"]}')(random.choice(_d))}).text, 'html.parser')
    d = soup(requests.get('https://www.sslproxies.org/').text, 'html.parser')
    _, *r, _ = [dict(zip(['ip', 'port', 'code'], [i.text for i in b.find_all('td')][:3])) for b in d.find('table', {'id':'proxylisttable'}).find_all('tr')]
    yield r
    with open('proxies.json', 'w') as f:
        json.dump(r if _code is None else (lambda x:r if len(x) < 5 else x)([i for i in r if i['code'] == _code]), f)
    

@contextlib.contextmanager
def refresh_user_agents() -> dict:
    _d = {'chrome':[b.a.text for i in range(1, 11) for b in soup(requests.get(f'https://developers.whatismybrowser.com/useragents/explore/software_name/chrome/{i}').text, 'html.parser').find_all('td', {'class':'useragent'})], 'firefox':[b.a.text for i in range(1, 11) for b in soup(requests.get(f'https://developers.whatismybrowser.com/useragents/explore/software_name/firefox/{i}').text, 'html.parser').find_all('td', {'class':'useragent'})]}
    with open('user_agents.json', 'w') as f:
        json.dump(_d, f)
    yield _d


class ProxyDearth:
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}>'

class AgentDearth:
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}>'

def load_proxies(_f:typing.Callable) -> typing.Callable:
    @functools.wraps(_f)
    def wrapper(_self, _code=None) -> typing.Any:
        _f(_self, _code)
        with open('proxies.json') as f:
            _self.proxies = (lambda x:x if _code is None else [i for i in x if i['code'] == _code])(json.load(f))
    return wrapper

def load_user_agents(_f:typing.Callable) -> typing.Callable:
    @functools.wraps(_f)
    def wrapper(_self, _browser:str = 'chrome') -> typing.Any:
        _f(_self, _browser)
        with open('user_agents.json') as f:
            _self.agents = json.load(f)
    return wrapper

class _get_user_agents:
    @load_user_agents
    def __init__(self, _browser:str='chrome') -> None:
        self.browser, self.seen = _browser, []
    
    def __next__(self) -> str:
        _t = random.choice(self.agents[self.browser])
        while _t in self.seen:
            if len(self.seen) == len(self.agents[self.browser]):
                return AgentDearth()
            _t = random.choice(self.agents[self.browser])
        return _t

class _get_proxies:
    @load_proxies
    def __init__(self, _code = None) -> None:
        self.code, self.seen = _code, []
    @classmethod
    def get_proxies(cls, _code = None) -> typing.Callable:
        return cls(_code)
    def __next__(self) -> dict:
        _t, flag = random.choice(self.proxies), False
        while _t in self.seen:
            if len(self.seen) == len(self.proxies):
                return ProxyDearth()
            _t = random.choice(self.proxies)
            flag = True
        self.seen.append(_t)
        return _t
        


if __name__ == '__main__':
    with refresh_proxies() as f:
        print(f)