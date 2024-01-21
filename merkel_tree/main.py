#######################################
#              PART 1                 #
#######################################

from hashlib import sha256
from enum import Enum
import math

def next_power_of_2(n):
    return 2 ** math.ceil(math.log2(n))

def hash(s: str) -> str:
  return sha256(s.encode()).hexdigest()

def merkleize(sentence: str) -> str:
    sentence_list = sentence.split(" ")
    print(sentence_list)
    hash_words = list(map(lambda word: hash(word), sentence_list))

    # Padding
    zeros_needed = next_power_of_2(len(hash_words)) - len(hash_words)
    hash_words.extend(['\x00'] * zeros_needed)

    # Hash till we get the root
    layer = hash_words
    while len(layer) != 1:
        new_layer = []
        for i in range(0, len(layer)-1, 2):
           new_layer.append(hash(layer[i] + layer[i+1]))
        layer = new_layer
    return layer[0]
           

#######################################
#              PART 2                 #
#######################################

class Side(Enum):
  LEFT = 0
  RIGHT = 1

def validate_proof(root: str, data: str, proof: [(str, Side)]) -> bool:
  
  node = hash(data)
  
  for (sibling, side) in proof:
     if side == Side.LEFT:
        node = hash(sibling + node)
     else:
        node = hash(node + sibling)

  return node == root

    

     
  pass # your code here

