import requests, scrapio_request_utilites
import proxy_manager


def get_html(url:str, priority:int, limit:str) -> str:
    _c, proxies, agents = 0, proxy_manager._get_proxies('US'), proxy_manager._get_user_agents()
    while _c < limit:
        proxy, user_agent = next(proxies), next(agents)
        try:
            _r = requests.get(url, proxies={'https':f'https://{proxy["ip"]}:{proxy["port"]}'}, headers={'User-Agent':user_agent}, timeout=4).text
            if 'Access Denied' not in _r:
                return _r
        except:
            pass
        _c += 1
    if priority:
        try:
            print('got down here')
            return requests.get(url).text
        except:
            pass
    return scrapio_request_utilites.FailedRequest()


        
        

class get:
    def __init__(self, _url:str, _priority=1, _limit=4) -> None:
        self.url, self.priority, self.limit = _url, _priority, _limit
    @property
    def text(self) -> str:
        return get_html(self.url, self.priority, self.limit)

if __name__ == '__main__':
    '''
    with proxy_manager.refresh_proxies() as proxies:
        print(proxies)
    '''
    
    print(get('https://www.woolworths.com.au/shop/browse/drinks/cordials-juices-iced-teas/iced-teas').text)