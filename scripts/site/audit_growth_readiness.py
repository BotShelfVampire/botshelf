#!/usr/bin/env python3
"""Read-only, anonymous public-surface audit; never a rendered-UX approval.

Run: python3 scripts/site/audit_growth_readiness.py --contract /path/to/acceptance.json --output /tmp/bsv-audit.json
     python3 scripts/site/audit_growth_readiness.py --self-test
Exit 0 = static checks passed, 1 = static failure, 2 = transport/unverified.
Release approval still requires the browser evidence listed in the contract.
No cookies, authentication, account actions, downloads, or external-link crawling.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

CONTRACT = None
ORIGIN = 'https://botshelfvampire.com'
MAX_BYTES = 2_000_000


class Document(HTMLParser):
    """Collect actual anchors and title only, without interpreting CSS or JS."""
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.links, self.title = [], ''
        self.in_title = False
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])
        if tag == 'title':
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


class PublicOnlyRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlsplit(newurl).netloc != urlsplit(ORIGIN).netloc or urlsplit(newurl).scheme != 'https':
            raise HTTPError(req.full_url, code, 'External redirect requires review', headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(path):
    if not path.startswith('/') or path.startswith('//') or urlsplit(path).query:
        raise ValueError('Only known public site paths without query parameters are allowed')
    url = ORIGIN + path
    opener = build_opener(PublicOnlyRedirect())
    try:
        request = Request(url, headers={'User-Agent': 'BSV-Public-Readiness-Audit/1.0', 'Cache-Control': 'no-cache'})
        with opener.open(request, timeout=20) as response:
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                return {'status': 'unverified', 'reason': 'response_size_limit', 'url': url}
            return {'status': 'received', 'url': url, 'final_url': response.url,
                    'http_status': response.status, 'content_type': response.headers.get('Content-Type', ''),
                    'sha256': hashlib.sha256(body).hexdigest(), 'source': body.decode('utf-8')}
    except HTTPError as exc:
        return {'status': 'fail' if exc.code in (404, 410) else 'unverified', 'url': url,
                'http_status': exc.code, 'reason': 'http_error'}
    except (URLError, TimeoutError, UnicodeDecodeError, OSError) as exc:
        return {'status': 'unverified', 'url': url, 'reason': type(exc).__name__}


def inspect(page, response):
    result = {k: v for k, v in response.items() if k != 'source'}
    result['id'] = page['id']
    result['scope'] = 'anonymous HTTP and static HTML only'
    if response['status'] != 'received':
        return result
    if urlsplit(response['final_url']).path.rstrip('/') != page['path'].rstrip('/'):
        result.update(status='fail', reason='unexpected_redirect')
        return result
    if 'text/html' not in response['content_type'].lower():
        result.update(status='fail', reason='expected_html')
        return result
    doc = Document(response['source'])
    checks = [{'id': 'expected_title', 'status': 'pass' if re.search(page['title_pattern'], doc.title, re.I) else 'fail'}]
    links = {urljoin(response['url'], link) for link in doc.links}
    for required in page.get('required_links', []):
        checks.append({'id': 'anchor_present', 'target': required,
                       'status': 'pass' if urljoin(response['url'], required) in links else 'fail'})
    result.update(status='fail' if any(c['status'] == 'fail' for c in checks) else 'pass',
                  title=doc.title.strip(), checks=checks)
    return result


def audit(contract, fetcher=fetch):
    results = [inspect(page, fetcher(page['path'])) for page in contract['public_pages']]
    counts = dict(Counter(r['status'] for r in results))
    static_status = 'fail' if counts.get('fail') else 'unverified' if counts.get('unverified') else 'pass'
    return {'schema_version': 1, 'checked_at_utc': datetime.now(timezone.utc).isoformat(),
            'static_status': static_status, 'counts': counts, 'pages': results,
            'release_readiness': 'unverified',
            'reason': 'Static availability is not rendered EN/JA, content usefulness, mobile usability, or runtime verification.',
            'browser_matrix': contract['browser_matrix'],
            'manual_checks': contract['manual_checks'],
            'unmapped_domains': [d['id'] for d in contract['domains'] if d['list_path'] is None]}


def self_test():
    import unittest
    class Tests(unittest.TestCase):
        def response(self, source='<title>Known page</title><a href="/ok/">Open</a>'):
            return {'status': 'received', 'url': ORIGIN+'/', 'final_url': ORIGIN+'/',
                    'http_status': 200, 'content_type': 'text/html', 'source': source}
        def page(self):
            return {'id': 'home', 'path': '/', 'title_pattern': 'Known page', 'required_links': ['/ok/']}
        def test_existing_link(self):
            self.assertEqual(inspect(self.page(), self.response())['status'], 'pass')
        def test_missing_link(self):
            self.assertEqual(inspect(self.page(), self.response('<title>Known page</title>'))['status'], 'fail')
        def test_script_string_is_not_anchor(self):
            r=self.response('<title>Known page</title><script>var a="<a href=\'/ok/\'>x</a>"</script>')
            self.assertEqual(inspect(self.page(), r)['status'], 'fail')
        def test_soft_404(self):
            self.assertEqual(inspect(self.page(), self.response('<title>Page not found</title>'))['status'], 'fail')
        def test_branded_soft_404(self):
            page={'id':'ai-list','path':'/','title_pattern':r'^Build Library — AI Team Registry building blocks \| BotShelf Vampire$'}
            self.assertEqual(inspect(page,self.response('<title>Not found | BotShelf Vampire</title>'))['status'],'fail')
        def test_http_failure_retained(self):
            self.assertEqual(inspect(self.page(),{'status':'fail','http_status':404})['status'],'fail')
        def test_registration_redirect(self):
            r=self.response(); r['final_url']=ORIGIN+'/register.html'
            self.assertEqual(inspect(self.page(),r)['reason'],'unexpected_redirect')
        def test_transport_not_failure_or_pass(self):
            self.assertEqual(inspect(self.page(),{'status':'unverified','reason':'TimeoutError'})['status'],'unverified')
        def test_wrong_mime(self):
            r=self.response();r['content_type']='application/json'
            self.assertEqual(inspect(self.page(),r)['status'],'fail')
        def test_bilingual_hidden_copy_not_language_failure(self):
            r=self.response('<title>Known page</title><span hidden>Coming soon</span><span lang="ja">準備中</span><a href="/ok/">Open 開く</a>')
            self.assertEqual(inspect(self.page(),r)['status'],'pass')
        def test_static_pass_never_approves_release(self):
            c={'public_pages':[self.page()],'domains':[],'browser_matrix':[],'manual_checks':[]}
            self.assertEqual(audit(c,lambda _: self.response())['release_readiness'],'unverified')
        def test_external_redirect_blocked(self):
            with self.assertRaises(HTTPError):
                PublicOnlyRedirect().redirect_request(Request(ORIGIN),None,302,'',{},'https://example.com/')
    return unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract',type=Path,default=CONTRACT)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test:
        return 0 if self_test() else 1
    if args.contract is None:
        parser.error('--contract is required for an audit')
    if args.contract is None:
        parser.error('--contract is required for an audit')
    report=audit(json.loads(args.contract.read_text()))
    encoded=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        args.output.write_text(encoded)
        print(json.dumps({'static_status':report['static_status'],'counts':report['counts'],
                          'release_readiness':report['release_readiness'],'output':str(args.output)}))
    else:
        print(encoded,end='')
    return {'pass':0,'fail':1,'unverified':2}[report['static_status']]


if __name__=='__main__':
    sys.exit(main())
