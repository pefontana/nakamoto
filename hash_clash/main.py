##################################
#            PART 1              #
##################################
from hashlib import sha256

def hash(s: str) -> str:
  return sha256(s.encode()).hexdigest()

def binary_leading_0s(hex_str: str) -> int:
    binary_representation = bin(int(hex_str, 16))[2:].zfill(256)
    return len(binary_representation) - len(binary_representation.lstrip('0'))

# VERSION:DATE:EMAIL:NONCE
# eg: 1:081031:satoshin@gmx.com:b4c26b1694691666


def is_valid(token: str, date: str, email: str, difficulty: int) -> bool:
  [_version, _date, _email, _nonce] = token.split(":")
  if (_version != "1") or (_date != date) or (_email != email):
     return False
  
  proof_of_work = hash(token)

  return binary_leading_0s(proof_of_work) >= difficulty


##################################
#            PART 2              #
##################################
import random

# Generate a random number with no more than 16 hex digits
def generate_random_hex() -> str:
  random_number = random.randint(0, 2**64 - 1)  # 2**64 is 16 hex digits
  return str(hex(random_number)[2:])  # Remove the '0x' prefix

def mint(date: str, email: str, difficulty: int) -> str:
  token = "1" + ":" + date + ":" + email + ":"
  nonce = "0"
  while binary_leading_0s(hash(token + nonce)) < difficulty:
     nonce = generate_random_hex()
  
  return token + nonce


if __name__ == "__main__":
  import uuid
  difficulty = 20
  date = "240124"
  for _ in range(10):
     random_email = f"nakamoto_{str(uuid.uuid4())[:8]}@gmail.com"
     token = mint(date, random_email, difficulty)
     assert(is_valid(token, date, random_email, difficulty ))
     print(mint(date, random_email, difficulty) + " => hash: " + hash(token))



     
