import typing, multiprocessing as mp
import proxy_manager

class FailedRequest:
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}>'


def timeout(sec:int) -> typing.Callable:
    def outer(_f:typing.Callable) -> typing.Callable:
        def _f_wrapper(_func:typing.Callable, _url, _p, usr_agent, _q):
            _q.put(_func(_url, _p, usr_agent))

        def wrapper(url:str, priority:int, limit:int = 4) -> typing.Any:
            _c, proxies = 0, proxy_manager._get_proxies('US')
            user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1 (compatible; AdsBot-Google-Mobile; +http://www.google.com/mobile/adsbot.html)'
            while _c < limit:
                print('within limit')
                _q, _result = mp.Queue(), None
                _p = next(proxies)
                if isinstance(_p, proxy_manager.ProxyDearth):
                    return None
                proc = mp.Process(target=_f_wrapper, name='Run_Request', args=(_f, url, _p, user_agent, _q))
                proc.start()
                proc.join(sec)
                try:
                    _result = _q.get(False)
                    print('result in try',_results)
                except:
                    pass
                if proc.is_alive():
                    proc.terminate()
                else:
                    return _result if not isinstance(_result, proxy_manager.ProxyDearth) else None
                proc.join()
                _c += 1
            return None
        return wrapper
    return outer