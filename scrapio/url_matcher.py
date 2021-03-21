import re, itertools
import urllib.parse, math
from bs4 import BeautifulSoup as soup

def score(a, b) -> float:
    if not all([a, b]):
        return 1
    if (re.findall('^\d+$', a) and re.findall('^\d+$', b)) or (a == b):
        return 0
    p1, p2 = re.split('\-|_', a), re.split('\-|_', b)
    return 1/float(1+pow(math.e, 4*(len(set(p1)&set(p2))/float(len(set(p1+p2))))))

def get_score(a:str, b:str) -> float:
    url1, url2 = list(filter(None, urllib.parse.urlparse(a).path.split('/'))),  list(filter(None, urllib.parse.urlparse(urllib.parse.urljoin(a, b)).path.split('/')))
    l1, l2 = urllib.parse.parse_qs(urllib.parse.urlparse(a).query), urllib.parse.parse_qs(urllib.parse.urlparse(urllib.parse.urljoin(a, b)).query)
    return sum(score(j, k) for j, k in itertools.zip_longest(url1, url2)) + sum(0.1*(l1.get(i) != l2.get(i)) for i in set(list(l1)+list(l2)))

def new_get_score(a, b) -> float:
    url1, url2 = list(filter(None, urllib.parse.urlparse(a).path.split('/'))),  list(filter(None, urllib.parse.urlparse(urllib.parse.urljoin(a, b)).path.split('/')))
    l1, l2 = urllib.parse.parse_qs(urllib.parse.urlparse(a).query), urllib.parse.parse_qs(urllib.parse.urlparse(urllib.parse.urljoin(a, b)).query)
    return [url1 ==url2, sum(score(j, k) for j, k in itertools.zip_longest(url1, url2)) + sum(0.1*(l1.get(i) != l2.get(i)) for i in set(list(l1)+list(l2)))]

def compare_rest(url:str) -> list:
    return (lambda x:[re.sub('/$', '', x.path), x.query, x.fragment])(urllib.parse.urlparse(url))

def target_urls(original:str, page) -> list:
    urls = {re.sub('^[\s\n]+|[\s\n]+', '', i['href'].replace('https', 'http')) for i in page.find_all('a') if i.attrs.get('href') and not i['href'].startswith('mailto') and (lambda x:re.sub('^www\.', '', urllib.parse.urlparse(x).netloc) == re.sub('^www\.', '', urllib.parse.urlparse(original).netloc) and compare_rest(original) != compare_rest(x))(urllib.parse.urljoin(original, str(i['href'])))}
    l = sorted([[get_score(original, i), i] for i in urls], key=lambda x:x[0])[:10]
    return [[a, b] for a, b in l if not b.startswith('#')]


if __name__ == '__main__':
    result = target_urls('https://www.booking.com/country.html', soup(open('test_input_5.html').read(), 'html.parser'))
    print(result)