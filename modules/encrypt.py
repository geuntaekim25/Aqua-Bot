from cryptography.fernet import Fernet


class EnDecrypt:
    def __init__(self, key=None):
        if key is None:
            key = Fernet.generate_key()
        self.key = key
        self.f = Fernet(self.key)

    def encrypt(self, data, is_out_string=True):
        if isinstance(data, bytes):
            ou = self.f.encrypt(data)
        else:
            ou = self.f.encrypt(data.encode('utf-8'))
        if is_out_string is True:
            return ou.decode('utf-8')
        else:
            return ou

    def decrypt(self, data, is_out_string=True):
        if isinstance(data, bytes):
            ou = self.f.decrypt(data)
        else:
            ou = self.f.decrypt(data.encode('utf-8'))
        if is_out_string is True:
            return ou.decode('utf-8')
        else:
            return ou
