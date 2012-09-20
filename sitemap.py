import urllib2
import zlib
import lxml.etree
import logging

class SiteMaps(object):
    def __init__(self, domain, links=1000):
        self.domain = domain
        self.links = links
        self.sitemaps = []
        self.urls = []
        self.fetched_sitemaps = []
    
    def read_robots(self):
        try:
            r = urllib2.urlopen('http://%s/robots.txt' % self.domain)
            txt = r.read()
            r.close()
            
            for line in txt.split('\n'):
                line = line.strip()

                if line.lower().startswith('sitemap:'):
                    self.sitemaps.append(line[len('Sitemap:'):].strip())
        except Exception, e:
            logging.exception(e)
    
    def run(self):
        self.read_robots()
        self.sitemaps = self.sitemaps or ['http://%s/sitemap.xml' % self.domain]
        while self.sitemaps and len(self.urls) < self.links:
            sitemap = self.sitemaps.pop()
            try:
                urls_before = len(self.urls)
                self.process_sitemap(sitemap)
                self.fetched_sitemaps.append((sitemap, (urls_before, len(self.urls))))
            except Exception, e:
                logging.exception(e)
    
    def process_sitemap(self, sitemap):
        is_gzip = False
        r = urllib2.urlopen(sitemap)
        start = r.read(100)
        if 'www.sitemaps.org/schemas' not in start:
            is_gzip = True
        text = start + r.read()
        r.close()
        if is_gzip:
            try:
                text = zlib.decompress(text, 16+zlib.MAX_WBITS)
            except:
                text = ""
        
        namespaces = [
            ('sm', 'http://www.sitemaps.org/schemas/sitemap/0.9'),
        ]
        
        if not text:
            return
        
        tree = lxml.etree.fromstring(text)
        
        for sitemap in tree.xpath('//sm:sitemap | //sitemap', namespaces=namespaces):
            for loc in sitemap.xpath('sm:loc | loc', namespaces=namespaces):
                self.sitemaps.append(loc.text.strip())
        
        for sitemap in tree.xpath('//sm:url | //url', namespaces=namespaces):
            # TODO: add last update date, rank and update frequency
            for loc in sitemap.xpath('sm:loc | loc', namespaces=namespaces):
                self.urls.append(loc.text.strip())
                if len(self.urls) >= self.links:
                    return

if __name__ == '__main__':
    s = SiteMaps('washingtonpost.com')
    s.run()
    print "sitemaps fetch intervals", s.fetched_sitemaps
    print "fetched urls", len(s.urls)
    