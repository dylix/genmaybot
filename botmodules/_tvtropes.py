def get_trope(self, e, urlposted=False):

    if urlposted:
        if "tvtropes.org/pmwiki/pmwiki.php" in e.input:
            url = e.input
        else:
            return
    elif not e.input:
        url = "https://tvtropes.org/pmwiki/browse.php"
        page = self.tools["load_html_from_url"](url)
        pageurl = page.find("a", {"class": "button-random-trope"}, href=True)
        url = f"https://tvtropes.org{pageurl['href']}"
        page = self.tools["load_html_from_url"](url)
    else:
        #searchterm = "site:tvtropes.org " + e.input
        #url = self.tools['google_url'](searchterm, "tvtropes.org/pmwiki/pmwiki.php")
        url = f"https://tvtropes.org/pmwiki/search_result.php?q={e.input}"
        page, url = self.tools["load_html_from_url"](url, returnurl=True)

    #page, url = self.tools["load_html_from_url"](url, returnurl=True)

    pagetitle = page.find("h1", {"class": "entry-title"}).text
    page = page.select('#main-article')[0].extract()
    for div in page.findAll('div'):
        div.extract()

    trope = self.tools['remove_html_tags'](str(page))

    trope = trope.replace("\n", " ").replace("\r", " ").strip()

    trope = "{}: {}".format(pagetitle, trope[0:392])
    if trope.rfind(".") != -1:
        trope = trope[0:trope.rfind(".") + 1]

    if not urlposted:
        trope = trope + " [ %s ]" % self.tools['shorten_url'](url)

    e.output = trope
    return e

get_trope.command = "!trope"
