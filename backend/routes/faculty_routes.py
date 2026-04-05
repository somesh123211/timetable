import bcrypt
print(bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode())