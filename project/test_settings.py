from project.settings import *


DEBUG = False

MELISSA_CONFIG['use_melissa'] = False

AUTH_NET_CONF['test_mode'] = True

SSL_ENABLED = False


# --
TEMPLATE_DEBUG = DEBUG
MAILER_DEBUG = DEBUG

if DEBUG:
    LOGGING['loggers']['']['level'] = 'DEBUG'


if SSL_ENABLED:
    MIDDLEWARE_CLASSES += ['django_snippets.thirdparty.views.SSLMiddleware']

AUTH_NET_TEST_MODE = AUTH_NET_CONF.get('test_mode', False)
AUTH_NET_GATEWAY = AUTH_NET_CONF['gateway']
AUTH_NET_API_LOGIN_ID = AUTH_NET_CONF['api_login_id']
AUTH_NET_TRANS_KEY = AUTH_NET_CONF['trans_key']

MELISSA = Melissa(MELISSA_CONFIG) if MELISSA_CONFIG['use_melissa'] else None

MUZE_DB = psycopg2.connect(**MUZE_DATABASE)
MUZE = Muze(MUZE_DB)
