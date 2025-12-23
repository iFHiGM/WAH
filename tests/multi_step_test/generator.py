import random
import os

print('Step 1: Generating token...')
token = random.randint(1000, 9999)
with open('token.txt', 'w') as f:
    f.write(str(token))
print(f'Token {token} written to token.txt')