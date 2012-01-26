import os
from os.path import dirname
import logging
import sys

import psycopg2

from muze import Muze
from melissadata.melissa import Melissa

REV = 265

PROJECT_ROOT = dirname(__file__)
BUILDOUT_DIR = dirname(PROJECT_ROOT)
# When deploying with capistrano
SHARED_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "../../../shared"))

MAINTENANCE = False

DEBUG = False

ADMINS = (
    ("Wayne Tucker", "wayne.tucker@gamemine.com"),
    ("alexandre", "mvi@os3ti.com")
)
MANAGERS = ADMINS

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "gamemine",
        "USER": "avl",
    }
}

TIME_ZONE = "America/Chicago"
DATE_FORMAT = "m-d-Y"
TIME_FORMAT = "P"

LANGUAGE_CODE = "en-us"

SITE_ID = 1

SSL_ENABLED = True

USE_I18N = False
USE_L10N = False

STATIC_ROOT = os.path.join(PROJECT_ROOT, "site_media/static")
MEDIA_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, "../../../../media"))
STATIC_URL = "/m/"
MEDIA_URL = "/m/media/"  # Some Javascript code may depend on this, so not changing
EMAIL_STATIC_URL = "http://www.gamemine.com/m/"
ADMIN_MEDIA_PREFIX = "/m/grappelli/"

STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, "static"),
)

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
#    "django.contrib.staticfiles.finders.DefaultStorageFinder",
)

INTERNAL_IPS = ("127.0.0.1",)

SECRET_KEY = "m$sk8%y98)d!#4xby&*ldp5)tr6@n&(!9$f_#c%_v2fki7(2l2"

TEMPLATE_LOADERS = (
    "djaml.filesystem",
    "djaml.app_directories",
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
#     "django.template.loaders.eggs.Loader",
)

MIDDLEWARE_CLASSES = [
    "django_snippets.middleware.CurrentSessionIDMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "project.middleware.CampaignTrackerMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "project.members.middleware.ProfileMiddleware",
    "project.middleware.MaintenanceMiddleware",
    "project.cart.middleware.CartMiddleware",
    "project.trade.middleware.CartMiddleware",
    "project.buy_orders.middleware.BuyListMiddleware",
    "deferred_messages.middleware.DeferredMessageMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

FIXTURE_DIRS = (
    os.path.join(PROJECT_ROOT, "fixtures"),
)

ROOT_URLCONF = "project.urls"

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, "templates"),
)

INSTALLED_APPS = (
#    "admin_tools.theming",
#    "admin_tools.menu",
#    "admin_tools.dashboard",

    "django.contrib.comments",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "grappelli",
    'filebrowser',
    "django.contrib.admin",
    "django.contrib.staticfiles",

    "django_extensions",
    "test_utils",
    "south",
    "mailer",
    "django_nose",
    "debug_toolbar",
    "django_snippets.templates",
    "fixture_magic",
    "sentry",
    "sentry.client",

    "project",
    "project.utils",
    "project.catalog",
    "project.inventory",
    "project.claims",
    "project.members",
    "project.new_members",
    "project.reviews",
    "project.buy_orders",
    "project.cart",
    "project.discount",
    "project.rent",
    "project.new_rent",
    "project.banners",
    "project.trade",
    "project.search",
    "project.staff",
    "project.taxes",
    "project.crm",
    "project.subscription",
    "project.os3marketing",
    "project.offer_term",
    "project.social_bookmarks",

    "sorl.thumbnail",
    "tinymce",
)

SOUTH_TESTS_MIGRATE = False

DEBUG_TOOLBAR_CONFIG = {
    "INTERCEPT_REDIRECTS": False,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(name)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        },
        "simple": {
            "format": "%(levelname)s : %(name)s : %(message)s"
        },
    },
    "handlers": {
        "null": {
            "level": "DEBUG",
            "class": "django.utils.log.NullHandler",
        },
        "sentry": {
            "level": "WARNING",
            "class": "sentry.client.handlers.SentryHandler",
            "formatter": "verbose"
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple"
        }
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "nose.plugins.manager": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "sentry.errors": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
        # Workarround for http://south.aeracode.org/ticket/767
        "south": {
            "handlers": ["null"],
            "level": "ERROR",
            "propagate": False,
        },
        "": {
            "level": "INFO",
            "handlers": ["sentry", "console"],
        },
    },
}


TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.request",
    "project.context_processors.core",
    "project.catalog.context_processors.common",
    "project.members.context_processors.core",
    "project.cart.context_processors.common",
    "project.rent.context_processors.common",
    "project.trade.context_processors.common",
    "project.staff.context_processors.common",
    "project.tds.context_processors.free_trial",
)

#CACHE_BACKEND = "memcached://127.0.0.1:11211/"
#CACHE_MIDDLEWARE_SECONDS = 900
#CACHE_MIDDLEWARE_KEY_PREFIX = "s1"
#CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

#SESSION_ENGINE = "django.contrib.sessions.backends.cache"

AUTH_PROFILE_MODULE = "new_members.Profile"


TEST_RUNNER = "project.utils.test.SmartDjangoTestSuiteRunner"

CATALOG_ITEMS_AMOUNT = 20
SEARCH_RESULTS_PER_PAGE = 25

LOGIN_REDIRECT_URL = "/"

AUTHENTICATION_BACKENDS = (
    "django_snippets.auth.backends.AuthenticateByEmailModelBackend",
    "django.contrib.auth.backends.ModelBackend",
)

EMAIL_BACKEND = "mailer.backend.DbBackend"

DEFAULT_FROM_EMAIL = "Gamemine <notifications@gamemine.com>"
LOGIN_URL = "/Member-Home/Login/"

COMMENTS_APP = "project.reviews"

ADMIN_TOOLS_INDEX_DASHBOARD = "project.dashboard.CustomIndexDashboard"

#==============================================================================
# Muze
#==============================================================================
MUZE_FTP = {
    "host": "ftp.muzegames2.muze.com",
    "username": "gamemine",
    "password": "g4M1n3o9",
}

MUZE_DATABASE = {
    "database": "gamemine_muze",
    "user": "avl",
}
#------------------------------------------------------------------------------

DEFAULT_REVIEWS_COUNT = 3

#==============================================================================
# Melissa
#==============================================================================
MELISSA_CONFIG = {
    "use_melissa": False,
    "lib_path": os.path.join(BUILDOUT_DIR, "lib/melissa/linux"),
    "address": {
        "api_key": "W3P6TWA9",
        "data_path": os.path.join(SHARED_DIR, "data/melissa/address/data"),
    },
    "name": {
        "api_key": "P2EH2MTS",
        "data_path": os.path.join(SHARED_DIR, "data/melissa/name/data"),
    },
    "phone": {
        "api_key": "9W-09L-8H4",
        "data_path": os.path.join(SHARED_DIR, "data/melissa/phone/data"),
    },
    "email": {
        "api_key": "87R3PGNX",
        "data_path": os.path.join(SHARED_DIR, "data/melissa/email/data"),
    },
}
#------------------------------------------------------------------------------

#==============================================================================
# Authorize.net
#==============================================================================
AUTH_NET_CONF = {
    "test_mode": True,
    "gateway": "https://secure.authorize.net/gateway/transact.dll",
    "api_login_id": "276kEd7kBH",
    "trans_key": "3BTt6Q43r2nGtd6v",
    "test_card": {
        "number": "1111111111111111",
        "exp": "0111",
        "ccv": "123",
    },
}

BILLING_CARDS_CRYPTO_KEY = "%2EvV{dfy/)p?qo};noJ[W|_IBn*W*h#"
#------------------------------------------------------------------------------

#==============================================================================
# Endicia
#==============================================================================
ENDICIA_CONF = {
    "test_mode": False,
    "url": "https://LabelServer.endicia.com/LabelService/EwsLabelService.asmx",
    "requester_id": "ABCD",
    "account_id": "750711",
    "pass_phrase": "GameMine9",
}
#------------------------------------------------------------------------------

CART_SESSION_LIFETIME = 45

CATALOG_ITEM_VIDEOS_AMOUNT = None
CATALOG_ITEM_SCREENSHOT_AMOUNT = None

GAMEMINE_POST_ADDRESS = {
    "company": "GAMEMINE",
    "address1": "247 HIGH ST",
    "address2": "",
    "city": "PALO ALTO",
    "state": "CA",
    "zip_code": "94301-1041",
}

GAMEMINE_SHIPPING_ADDRESS = GAMEMINE_POST_ADDRESS

FEEDBACKIFY_IFN_KEY = "ooP2Io7uco2She5D"

INGRAM = {
    "ftp": {
        "host": "ftp.accessingram.com",
        "username": "1067676",
        "password": "squeaky58tylo",
    },
}


#==============================================================================
# Social bookmarks
#==============================================================================
# Function to call on an object to retreive it's permalink
SOCIAL_BOOKMARKS_PERMALINK_FUNC = "get_absolute_url"

# Open in new window
SOCIAL_BOOKMARKS_OPEN_IN_NEW_WINDOW = True

# List of enabled social sites
SOCIAL_BOOKMARKS = [
    'delicious',
    'digg',
    'facebook',
    'twitter',
#    'ekudos',
#    'technorati',
    'google',
    'furl',
    'stumble',
#    'slashdot',
    'yahoo',
    'reddit',
]
#------------------------------------------------------------------------------


#==============================================================================
# tiny_mce
#==============================================================================
TINYMCE_JS_URL = os.path.join(STATIC_URL, 'tiny_mce/tiny_mce.js')
TINYMCE_JS_ROOT = os.path.join(STATIC_ROOT, 'tiny_mce')
TINYMCE_DEFAULT_CONFIG = {
    'mode' : "textareas",
    'theme' : "advanced",
    'skin' : "o2k7",
    'content_css' : os.path.join(STATIC_URL, "css/editor.css"),
    'plugins': "safari,spellchecker,pagebreak,style,layer,table,save,advhr,advimage,advlink,emotions,iespell,inlinepopups,insertdatetime,searchreplace,print,\
contextmenu,paste,directionality,noneditable,visualchars,nonbreaking,xhtmlxtras,template",
    'theme_advanced_buttons1' : "save,newdocument,|,bold,italic,underline,strikethrough,|,justifyleft,justifycenter,justifyright,justifyfull,|,styleselect,fo\
rmatselect,fontselect,fontsizeselect",
    'theme_advanced_buttons2' : "cut,copy,paste,pastetext,pasteword,|,search,replace,|,bullist,numlist,|,outdent,indent,blockquote,|,undo,redo,|,link,unlink,\
anchor,image,cleanup,help,code,|,insertdate,inserttime,preview,|,forecolor,backcolor",
    'theme_advanced_buttons3' : "tablecontrols,|,hr,removeformat,visualaid,|,sub,sup,|,charmap,emotions,iespell,media,advhr,|,print,|,ltr,rtl,|,fullscreen",
    'theme_advanced_buttons4' : "insertlayer,moveforward,movebackward,absolute,|,styleprops,spellchecker,|,cite,abbr,acronym,del,ins,attribs,|,visualchars,no\
nbreaking,template,blockquote,pagebreak,|,insertfile,insertimage",
    'theme_advanced_toolbar_location' : "top",
    'theme_advanced_toolbar_align' : "left",
    'theme_advanced_statusbar_location' : "bottom",
    'height': "600",
    'width': "100%",
    'relative_urls' : False,
    'remove_script_host' : False,
}
#------------------------------------------------------------------------------


#==============================================================================
# FILEBROWSER
#==============================================================================
FILEBROWSER_DIRECTORY = "newsletter/"
#------------------------------------------------------------------------------


# To import local_settings when deploying with capistrano
sys.path.append(SHARED_DIR)

try:
    from local_settings import *
except ImportError:
    pass

# Django-filebrowser fix
if not os.path.exists(os.path.join(MEDIA_ROOT, FILEBROWSER_DIRECTORY)):
    os.makedirs(os.path.join(MEDIA_ROOT, FILEBROWSER_DIRECTORY))

TEMPLATE_DEBUG = DEBUG

if DEBUG:
    LOGGING["loggers"][""]["level"] = "DEBUG"


if SSL_ENABLED:
    MIDDLEWARE_CLASSES += ["django_snippets.thirdparty.views.SSLMiddleware"]

AUTH_NET_TEST_MODE = AUTH_NET_CONF.get("test_mode", True)
AUTH_NET_GATEWAY = AUTH_NET_CONF["gateway"]
AUTH_NET_API_LOGIN_ID = AUTH_NET_CONF["api_login_id"]
AUTH_NET_TRANS_KEY = AUTH_NET_CONF["trans_key"]

MELISSA = Melissa(MELISSA_CONFIG) if MELISSA_CONFIG["use_melissa"] else None

MUZE_DB = psycopg2.connect(**MUZE_DATABASE)
MUZE = Muze(MUZE_DB)
