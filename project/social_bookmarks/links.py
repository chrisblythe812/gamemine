# -*- coding: utf-8 -*-

from django.conf import settings
from django.utils.translation import ugettext as _

DEFAULT_DISPLAY_TITLE = "%s %%s" % _('Share on')
SOCIAL_BOOKMARKS_LINKS = {
    # NAME: (Display Name, Display Title, URL, IMAGE, JS)

    # Nederlandse social news sites (Dutch)
    'nujij': (_('NUjij'), None, 'http://nujij.nl/jij.lynkx?t=%(title)s&u=%(url)s&b=%(description)s', 'sn-nujij.gif', None),
    'ekudos': (_('eKudos'), None, 'http://www.ekudos.nl/artikel/nieuw?url=%(url)s&title=%(title)s&desc=%(description)s','sn-ekudos.gif', None),
    'msn': (_('MSN Reporter'), None, 'http://reporter.msn.nl/?fn=contribute&Title=%(title)s&URL=%(url)s&cat_id=6&tag_id=31&Remark=','sn-msnreporter.gif', None),
    'geenredactie': (_('GeenRedactie'), None, 'http://www.geenredactie.nl/submit?url=%(url)s&title=%(title)s','sn-gr.gif', None),
    'grubb': (_('Grubb'), None, 'http://www.grubb.nl/directlink?source=%(url)s&title=%(title)s&body=%(description)s','sn-grubb.gif', None),
    'tipt': (_('Tipt'), _('Tip dit artikel!'), 'http://www.tipt.nl/new_tip.php?title=%(title)s&url=%(url)s','sn-tipt.gif', None),
    'bligg-nl': (_('Bligg'), None, 'http://www.bligg.nl/submit.php?url=%(url)s', 'sn-bligg.gif', None),             # Bligg.nl (sn-bligg-nl.gif)
    'wvwo': (_('Wat vinden wij over'), None, 'http://watvindenwijover.nl/notes/new?nextaction=home&url=%(url)s&title=%(title)s&text=%(description)s&commit=Verder', 'sn-wvwo.gif', None),   # Wat vinden wij over
    'tagmos': (_('Tagmos'), None, 'http://www.tagmos.nl/bookmarks.php/?action=add&noui=yes&jump=close&address=%(url)s&title=%(title)s&description=%(description)s', 'sn-tagmos.gif', None),              # Tagmos.nl

    # Belgische social news sites (Belgium )
    'msn-be': (_(u'MSN Reporter België'), None, 'http://reporter.be.msn.com/?fn=contribute&amp;Title=%(title)s&URL=%(url)s&cat_id=6&tag_id=31&Remark=%(description)s', 'sn-msn-be.gif', None),          # MSN Reporter België
    'bligg-be': (_('Bligg'), None, 'http://www.bligg.be/submit.php?url=%(url)s', 'sn-bligg-be.gif', None),        # Bligg.be
    'netjes': (_('Netjes'), None, 'http://www.netjes.be/toevoegen.php?url=%(url)s&titel=%(title)s&beschrijving=%(description)s', 'sn-netjes.gif', None),          # Netjes.be
        
    # social bookmarking
    #'delicious': (_('Delicious'), None, 'http://del.icio.us/post?v=5&noui&jump=close&url=%(url)s&title=%(title)s', 'sn-delicious.gif', None),
    'delicious': (_('Delicious'), None, 'http://del.icio.us/post?v=5&noui&url=%(url)s&title=%(title)s', 'sn-delicious.gif', None),
    'digg': (_('Digg'), None, 'http://digg.com/submit?phase=2&url=%(url)s&title=%(title)s&bodytext=%(description)s', 'sn-digg.gif', None),
    'technorati': (_('Technorati'), _('Add to favorites on Technorati'), 'http://technorati.com/faves?add=%(url)s', 'sn-technorati.gif', None),
    'google': (_('Google'), _('Add to Google bookmarks'), 'http://www.google.com/bookmarks/mark?op=add&title=&bkmk=%(url)s&labels=&annotation=%(title)s', 'google_002.png', None),
    'furl': (_('Furl'), None,'http://www.furl.net/storeIt.jsp?t=%(title)s&u=%(url)s','sn-furl.gif', None),
    'stumble': (_('StumbleUpon'), _('Stumble it!'), 'http://www.stumbleupon.com/submit?url=%(url)s&title=%(title)s&language=%(language_code)s', 'sn-su.gif', None),        # StumbleUpon
    
    # social tools
    'facebook': (_('Facebook'), _('Add to Facebook-profile'), 'http://www.facebook.com/sharer.php?u=%(url)s&t=%(title)s', 'sn-fb.gif', None),      # Facebook
    #'rss': (_('RSS-feed'), _('Abonneer je op de RSS-feed van deze site'), '', 'sn-rss.gif', None),            # RSS-feed van je site
    #'email': (_('e-mailen'), _('E-Mail deze pagina'), 'mailto:', 'sn-email.png', None),          # Artikel e-mailen
    'twitter': (_('Twit This'), _('Post tweet on Twitter'), 'javascript:;', 'sn-twitter.gif', ('<script type="text/javascript" src="http://s3.chuug.com/chuug.twitthis.scripts/twitthis.js"></script>', 'TwitThis.pop();')),        # Twit This
    
    # others
    'slashdot': (_('Slashdot'), None, 'http://www.slashdot.org/bookmark.pl?url=%(url)s&title=%(title)s', 'slashdot.gif', None),
    'yahoo': (_('Yahoo'), None, 'http://myweb2.search.yahoo.com/myresults/bookmarklet?u=%(url)s&t=%(title)s', 'yahoomyweb.png', None),
    'bobrdobr': (_('Bobrdobr.ru'), None, 'http://www.bobrdobr.ru/addext.html?url=%(url)s&title=%(title)s', 'bobr_sml_red_3.gif', None),
    #'newsland': (_('Newsland.ru'), None, 'http://www.newsland.ru/News/Add/', 'newsland.gif', None),
    #'smi2': (_('Smi2.ru'), None, 'http://smi2.ru/add/', 'smi2.gif', None),
    'rumarkz': (_('Rumarkz.ru'), None, 'http://rumarkz.ru/bookmarks/?action=add&popup=1&address=%(url)s&title=%(title)s', 'rumark.png', None),
    'vaau': (_('Vaau.ru'), None, 'http://www.vaau.ru/submit/?action=step2&url=%(url)s', 'vaau.gif', None),
    'memori': (_('Memori.ru'), None, 'http://memori.ru/link/?sm=1&u_data[url]=%(url)s&u_data[name]=%(title)s', 'memori.gif', None),
    'rucity': (_('Rucity.com'), None, 'http://www.rucity.com/bookmarks.php?action=add&address=%(url)s&title=%(title)s', 'rucity.gif', None),
    'moemesto': (_('Moemesto.ru'), None, 'http://moemesto.ru/post.php?url=%(url)s&title=%(title)s', 'mm.gif', None),
    'news2': (_('News2.ru'), None, 'http://news2.ru/add_story.php?url=%(url)s', 'news2ru.png', None),
    'mister-wong': (_('Mister-Wong.ru'), None, 'http://www.mister-wong.ru/index.php?action=addurl&bm_url=%(url)s&bm_description=%(title)s', 'mister-wong.gif', None),
    'yandex': (_('Yandex.ru'), None, 'http://zakladki.yandex.ru/userarea/links/addfromfav.asp?bAddLink_x=1&lurl=%(url)s&lname=%(title)s', 'yandex-zakladki.gif', None),
    'myscoop': (_('Myscoop.ru'), None, 'http://myscoop.ru/add/?URL=%(url)s&title=%(title)s', 'myscoop.gif', None),
    '100zakladok': (_('100zakladok.ru'), None, 'http://www.100zakladok.ru/save/?bmurl=%(url)s&bmtitle=%(title)s', '100zakladok.gif', None),
    'reddit': (_('Reddit'), None, 'http://reddit.com/submit?url=%(url)s&title=%(title)s', 'reddit.png', None),
}

# Set default display titles
for key, value in SOCIAL_BOOKMARKS_LINKS.iteritems():
    if not value[1]:
        SOCIAL_BOOKMARKS_LINKS[key] = (
            value[0],
            DEFAULT_DISPLAY_TITLE % value[0],
            value[2],
            value[3],
            value[4],
        )

if getattr(settings, 'SOCIAL_BOOKMARKS_CONSERVE_MEMORY', True):
    # Try to remove all entries not in SOCIAL_BOOKMARKS to conserve a little bit of memory usage
    try:
        SOCIAL_BOOKMARKS = getattr(settings, 'SOCIAL_BOOKMARKS', [])
        for key in SOCIAL_BOOKMARKS_LINKS.keys():
            if not key in SOCIAL_BOOKMARKS:
                del SOCIAL_BOOKMARKS_LINKS[key]
    except:
        pass
