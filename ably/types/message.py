from __future__ import absolute_import

import base64
import json
import logging
import time

import six

from ably.types.typedbuffer import TypedBuffer
from ably.util.crypto import CipherData

log = logging.getLogger(__name__)

class Message(object):
    def __init__(self, name=None, data=None, client_id=None, timestamp=None):
        if name is None:
            self.__name = None
        elif isinstance(name, six.string_types):
            self.__name = name
        elif isinstance(name, six.binary_type):
            self.__name = name.decode('ascii')
        else:
            log.debug(name)
            log.debug(name.__class__)
            raise ValueError("name must be a string or bytes")
        self.__client_id = client_id
        self.__data = data
        self.__timestamp = timestamp

    @property
    def name(self):
        return self.__name

    @property
    def client_id(self):
        return self.__client_id

    @property
    def data(self):
        return self.__data

    @property
    def timestamp(self):
        return self.__timestamp

    def encrypt(self, channel_cipher):
        if isinstance(self.data, CipherData):
            return

        typed_data = TypedBuffer.from_obj(self.data)
        encrypted_data = channel_cipher.encrypt(typed_data.buffer)

        self.data = CipherData(encrypted_data, typed_data.type)

    def decrypt(self, channel_cipher):
        if not isinstance(self.data, CipherData):
            return

        decrypted_data = channel_cipher.decrypt(self.data.buffer)
        decrypted_typed_buffer = TypedBuffer(decrypted_data, self.data.type)

        self.__data = decrypted_typed_buffer.decode()

    def as_json(self):
        data = self.data
        encoding = None

        log.debug(data.__class__)

        if isinstance(data, six.binary_type):
            data = base64.b64encode(data).decode('ascii')
            encoding = 'base64'

        log.debug(data)
        log.debug(data.__class__)

        request_body = {
            'name': self.name,
            'data': data,
            'timestamp': time.time() * 1000.0,
        }

        if encoding:
            request_body['encoding'] = encoding

        request_body = json.dumps(request_body)
        return request_body

    @staticmethod
    def from_json(obj):
        name = obj.get('name')
        data = obj.get('data')
        timestamp = obj.get('timestamp')
        encoding = obj.get('encoding')

        log.debug("MESSAGE: %s", str(obj))

        if encoding and encoding == six.u('base64'):
            data = base64.b64decode(data)
        elif encoding and encoding == six.u('base64+cipher'):
            ciphertext = base64.b64decode(data)
            #TODO
            data = ciphertext

        return Message(name=name, data=data,timestamp=timestamp)