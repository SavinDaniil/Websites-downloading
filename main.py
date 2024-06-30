import os
import re
import threading
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def save_file(soup, pagefolder, session, url, tag, inner):
    if not os.path.exists(pagefolder):
        os.mkdir(pagefolder)
    for res in soup.findAll(tag):
        if tag == 'link' and res.has_attr('crossorigin'):
            del res.attrs['crossorigin']
        if tag == 'base':
            res.extract()
        elif tag == 'style':
            if res.string:
                text = res.string.strip()
                try:
                    if 'url' in text:
                        index = 0
                        s = re.search("(url\(+)(?!\")([^)]*)", text)
                        while s:
                            urls = text[s.start() + 4 + index: s.end() + index]
                            filename = urls.split('/')[-1]
                            filepath = os.path.join(pagefolder, filename)
                            fileurl = urljoin(url, urls)
                            localpath = '../' + os.path.join(pagefolder, filename).replace('\\', '/')
                            text = (text[:s.start() + 4 + index] + localpath + text[s.end() - 1 + index + 1:])

                            if not os.path.isfile(filepath):
                                with open(filepath, 'wb') as f:
                                    filebin = session.get(fileurl)
                                    f.write(filebin.content)

                            index += s.end() - (len(urls) - len(localpath))
                            s = re.search("(url\(+)(?!\")([^)]*)", text[index:])
                        res.string = text
                except Exception:
                    res.string = text

        elif res.has_attr(inner):
            try:
                filename, ext = os.path.splitext(os.path.basename(res[inner]))
                if '?' in ext:
                    ext = ext[:ext.find('?')]
                filename = re.sub('\W+', '', filename) + ext
                fileurl = urljoin(url, res.get(inner))
                filepath = os.path.join(pagefolder, filename)
                res[inner] = '../' + os.path.join(pagefolder, filename).replace('\\', '/')
                if tag == 'img':
                    if res.has_attr('srcset'):
                        res.attrs['srcset'] = ''

                if not os.path.isfile(filepath):  # has not been downloaded yet
                    with open(filepath, 'wb') as file:
                        filebin = session.get(fileurl)
                        file.write(filebin.content)
            except Exception:
                pass


def save_page(url, pagepath):
    path, _ = os.path.splitext(pagepath)
    # pagefolder = os.path.join('sites', f'{path}_files')
    pagefolder = f'sites/{path}_files'
    session = requests.Session()
    try:
        response = session.get(url)
    except requests.exceptions.ConnectionError as exception:
        raise exception

    soup = BeautifulSoup(response.content.decode('utf-8'), "html.parser")
    tags_inner = {'img': 'src', 'link': 'href', 'script': 'src', 'style': '', 'base': ''}
    threads = []
    for tag, inner in tags_inner.items():  # save and rename resource files
        thread = threading.Thread(target=save_file, args=[soup, pagefolder, session, url, tag, inner])
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

    with open(f'templates/{path}.html', 'wb') as file:
        file.write(soup.prettify('utf-8'))


# examples
# save_page('https://github.com/', 'github')


