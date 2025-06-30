def Encrypt_ID(uid):
    return uid[::-1]

def encrypt_api(payload):
    return payload.encode().hex()