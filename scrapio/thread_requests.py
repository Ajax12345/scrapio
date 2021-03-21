import requests, re, functools
from bs4 import BeautifulSoup as soup
import concurrent.futures, multiprocessing as mp
import style_parser, collections, typing, time
from urllib.parse import urlparse

def strip_path(_url:str) -> str:
    return (lambda _r:f'{_r.scheme}://{_r.netloc}')(urlparse(_url))

class ThreadRequests:
    def __init__(self, _base:str, _urls:typing.List[dict], _xml_depth = 1, _count = 0, _depth = 2) -> None:
        self.base, self.urls, self.xml_depth, self.count, self.depth = _base, _urls, _xml_depth, _count, _depth
    def __enter__(self) -> typing.Callable:
        return self

    def request_html(self, _url:str) -> typing.Any:
        return soup(requests.get(_url).text, 'html.parser')

    def request_xml(self, _url:str) -> typing.Any:
        _d = soup(requests.get(style_parser.style_parser_utilites._merge_url(self.base, _url)).text, 'html.parser')
        if _d.urlset:
            return [i.text for i in _d.urlset.find_all('loc')]
 
        if _d.sitemapindex and self.xml_depth and self.count < self.depth:
            _maps = [i.text for i in _d.sitemapindex.find_all('loc')]
            with ThreadRequests(self.base, [{'ext':'xml', 'url':i} for i in _maps], _xml_depth = self.xml_depth, _count = self.count + 1, _depth = self.depth) as _resp:
                pass
            return _resp.response
        return None

    def request_txt(self, _url:str) -> typing.Any:
        _d = soup(requests.get(style_parser.style_parser_utilites._merge_url(self.base, _url)).text, 'html.parser')
        if _d.body is None:
            _content = list(filter(None, _d.text.split('\n')))
            _maps = [i.split(": ")[-1] for i in _content if i.lower().startswith('sitemap')]
            if _maps:
                with ThreadRequests(self.base, [{'ext':'xml', 'url':i} for i in _maps], _xml_depth = self.xml_depth) as _resp:
                    pass
                return _resp.response
                
        return self.request_xml('/sitemap.xml')
    
    def request_css(self, _url:str) -> typing.Any:
        try:
            return style_parser.StyleSheet.load_url(style_parser.style_parser_utilites._merge_url(self.base, _url))
        except:
            return None
        
    def __exit__(self, *args, **kwargs) -> bool:
        def start_processes(_payload:dict) -> typing.Any:
            return _payload['ext'], getattr(self, f'request_{_payload["ext"]}')(_payload['url'])
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as pool:
            self.response = collections.defaultdict(list)
            for a, b in pool.map(start_processes, self.urls):
                if b:
                    self.response[a].append(b)
        self.response = {**self.response, 'css':functools.reduce(lambda x, y:x+y, list(filter(None, self.response['css'])))}
        return False


def timeit(_f:typing.Callable) -> typing.Callable:
    def wrapper(*args, **kwargs):
        t = time.time()
        _r = _f(*args, **kwargs)
        print(f"'{_f.__name__}' ran in: {abs(time.time() - t)}")
        return _r
    return wrapper

if __name__ == '__main__':

    @timeit
    def single_process():
        return style_parser.StyleSheet.load_url('https://www.learningconnection.philips.com/sites/default/files/css/css_lQaZfjVpwP_oGNqdtWCSpJT1EMqXdMiU84ekLLxQnc4.css')

    @timeit
    def conseq_process():
        return [style_parser.StyleSheet.load_url(i) for i in ['https://www.learningconnection.philips.com/sites/default/files/css/css_lQaZfjVpwP_oGNqdtWCSpJT1EMqXdMiU84ekLLxQnc4.css', 'https://www.learningconnection.philips.com/sites/default/files/css/css_69iQNH9_V5jG-ypN2uK1-Lehh5o2pv6am8NNHLtqn_M.css', 'https://www.learningconnection.philips.com/sites/default/files/css/css_6zemUaNACzZ5sPLowbJJP0jVAcgeofg1dmXJdb1dfGY.css', 'https://www.learningconnection.philips.com/sites/default/files/css/css_89FjzX-x8du62ZZE5LFfkiexdk2eoooHfQ5QT-C8R9g.css', 'https://www.learningconnection.philips.com/sites/default/files/css/css_aPVPiQn8pEUdfGRHDqhKeYbPBlz_x-isxY2s-ekcsvE.css', 'https://www.learningconnection.philips.com/sites/default/files/css/css_jBWvBukjhwT25MA1nFD6XEa1hwK1FVoqeLg3Smpxyv4.css', 'https://www.learningconnection.philips.com/sites/all/themes/philips2018/css/style.css?pw6kwa', 'https://www.learningconnection.philips.com/sites/default/files/css_injector/css_injector_2.css?pw6kwa', 'https://www.learningconnection.philips.com/sites/default/files/css_injector/css_injector_4.css?pw6kwa', 'https://www.learningconnection.philips.com/sites/default/files/css_injector/css_injector_6.css?pw6kwa', 'https://www.learningconnection.philips.com/sites/default/files/css/css_mlAzxDXQhxfC6ODMwLfYZ3O7X-uBuzZ9u_6Icqj0MxE.css']]

    @timeit
    def multiprocess():
        _urls = ['https://www.learningconnection.philips.com/sites/default/files/css/css_lQaZfjVpwP_oGNqdtWCSpJT1EMqXdMiU84ekLLxQnc4.css', 'https://www.learningconnection.philips.com/sites/default/files/css/css_69iQNH9_V5jG-ypN2uK1-Lehh5o2pv6am8NNHLtqn_M.css', 'https://www.learningconnection.philips.com/sites/default/files/css/css_6zemUaNACzZ5sPLowbJJP0jVAcgeofg1dmXJdb1dfGY.css', 'https://www.learningconnection.philips.com/sites/default/files/css/css_89FjzX-x8du62ZZE5LFfkiexdk2eoooHfQ5QT-C8R9g.css', 'https://www.learningconnection.philips.com/sites/default/files/css/css_aPVPiQn8pEUdfGRHDqhKeYbPBlz_x-isxY2s-ekcsvE.css', 'https://www.learningconnection.philips.com/sites/default/files/css/css_jBWvBukjhwT25MA1nFD6XEa1hwK1FVoqeLg3Smpxyv4.css', 'https://www.learningconnection.philips.com/sites/all/themes/philips2018/css/style.css?pw6kwa', 'https://www.learningconnection.philips.com/sites/default/files/css_injector/css_injector_2.css?pw6kwa', 'https://www.learningconnection.philips.com/sites/default/files/css_injector/css_injector_4.css?pw6kwa', 'https://www.learningconnection.philips.com/sites/default/files/css_injector/css_injector_6.css?pw6kwa', 'https://www.learningconnection.philips.com/sites/default/files/css/css_mlAzxDXQhxfC6ODMwLfYZ3O7X-uBuzZ9u_6Icqj0MxE.css']
        with ThreadRequests(strip_path('https://www.learningconnection.philips.com/en/course/pinnacle%C2%B3-advanced-planning-education'), [{'ext':'css', 'url':i} for i in _urls]) as _payload:
            pass

        print(_payload.response)
        

    #_ = single_process()
    #_ = conseq_process()
    #print(ThreadRequests('https://www.nykaa.com', []).request_txt('/robots.txt'))  
    '''
    _urls = ['https://www.learningconnection.philips.com/sites/default/files/css/css_lQaZfjVpwP_oGNqdtWCSpJT1EMqXdMiU84ekLLxQnc4.css', 'https://www.learningconnection.philips.com/sites/default/files/css/css_69iQNH9_V5jG-ypN2uK1-Lehh5o2pv6am8NNHLtqn_M.css', 'https://www.learningconnection.philips.com/sites/default/files/css/css_6zemUaNACzZ5sPLowbJJP0jVAcgeofg1dmXJdb1dfGY.css', 'https://www.learningconnection.philips.com/sites/default/files/css/css_89FjzX-x8du62ZZE5LFfkiexdk2eoooHfQ5QT-C8R9g.css', 'https://www.learningconnection.philips.com/sites/default/files/css/css_aPVPiQn8pEUdfGRHDqhKeYbPBlz_x-isxY2s-ekcsvE.css', 'https://www.learningconnection.philips.com/sites/default/files/css/css_jBWvBukjhwT25MA1nFD6XEa1hwK1FVoqeLg3Smpxyv4.css', 'https://www.learningconnection.philips.com/sites/all/themes/philips2018/css/style.css?pw6kwa', 'https://www.learningconnection.philips.com/sites/default/files/css_injector/css_injector_2.css?pw6kwa', 'https://www.learningconnection.philips.com/sites/default/files/css_injector/css_injector_4.css?pw6kwa', 'https://www.learningconnection.philips.com/sites/default/files/css_injector/css_injector_6.css?pw6kwa', 'https://www.learningconnection.philips.com/sites/default/files/css/css_mlAzxDXQhxfC6ODMwLfYZ3O7X-uBuzZ9u_6Icqj0MxE.css']
    with ThreadRequests(strip_path('https://www.nykaa.com/media/sitemap/sitemap-makeup-new.xml'), [{'ext':'css', 'url':i} for i in _urls]) as _payload:
        pass
    
    _r = _payload.response
    print(_r)
    '''
    import grab
    @timeit
    def grab_proc():
        return grab.Grab().go("https://www.nykaa.com/skin/moisturizers/serums-essence/c/8397?root=nav_3&page_no=1").body

    @timeit
    def requests_proc():
        return requests.get('https://www.nykaa.com/skin/moisturizers/serums-essence/c/8397?root=nav_3&page_no=1').text

    _ = grab_proc()
    _ = requests_proc()