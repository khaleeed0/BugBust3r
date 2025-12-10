import os
import subprocess

def command_injection(user_input):
    os.system(f"ls {user_input}")  # Command injection vulnerability

def sql_injection(query):
    # Simulated SQL injection
    conn.execute(f"SELECT * FROM users WHERE name = '{query}'")

def hardcoded_password():
    password = "admin123"  # Hardcoded password
    return password

def weak_crypto():
    import hashlib
    hash = hashlib.md5("password".encode())  # Weak MD5 hash
    return hash

if __name__ == "__main__":
    command_injection("test; rm -rf /")
    hardcoded_password()
    weak_crypto()

