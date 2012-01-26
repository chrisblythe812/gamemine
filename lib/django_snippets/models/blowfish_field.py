from logging import debug #@UnusedImport
from Crypto.Cipher import Blowfish
import hashlib
import base64

from django.db import models
from django.utils import simplejson as json


def encrypt(key, obj):
    text = json.dumps(obj)
    sha1 = hashlib.sha1()
    sha1.update(text)
    checksum = sha1.digest()
    l = len(text) % 8
    if l:
        text += '\0' * (8 - l)
    encrypted = Blowfish.new(key).encrypt(text)
    return base64.encodestring(''.join([checksum, encrypted]))


def decrypt(key, data):
    data = base64.decodestring(data)
    checksum, data = data[:20], data[20:]
    text = Blowfish.new(key).decrypt(data)
    text = text.strip('\0')
    sha1 = hashlib.sha1()
    sha1.update(text)
    if checksum != sha1.digest():
        raise ValueError()
    return json.loads(text)


class CryptedObject(str):
    pass


class BlowfishField(models.TextField):
    __metaclass__ = models.SubfieldBase

    def __init__(self, key=None, *args, **kwargs):
        self.key = key
        super(BlowfishField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, CryptedObject):
            return decrypt(self.key, value)
        else:
            try:
                return decrypt(self.key, value)
            except:
                return value

    def get_db_prep_value(self, value, connection=None, prepared=False):
        if value is not None and not isinstance(value, CryptedObject):
            value = CryptedObject(encrypt(self.key, value))
        return value

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)


import psycopg2
psycopg2.extensions.register_adapter(CryptedObject, psycopg2.extensions.QuotedString) 

from south.modelsinspector import add_introspection_rules #@UnresolvedImport
add_introspection_rules([
    (
        [BlowfishField], # Class(es) these apply to
        [],              # Positional arguments (not used)
        {},              # Keyword argument
    ),
], ["^django_snippets\.models\.blowfish_field\.BlowfishField"])
