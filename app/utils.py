from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()
DUMMY_HASHED = password_hash.hash('dummypassword123')

def hash_password(password: str):
    return password_hash.hash(password)

def verify_password(plain_pass: str, hash_pass: str):
    return password_hash.verify(plain_pass, hash_pass)