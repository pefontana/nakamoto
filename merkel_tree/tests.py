import unittest
from hashlib import sha256
from main import merkleize, validate_proof, Side

def _sha2(s):
  return sha256(s.encode()).hexdigest()

class Testing(unittest.TestCase):
    def test_1(self):
      self.assertIsInstance(merkleize("hello world"), str, "Merkleize must return a string")

    def test_2(self):
      res = merkleize("hello")
      self.assertEqual(res, '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824', "Correctly Merkleizes 'hello'")

    def test_3(self):
      res = merkleize("hello world")
      self.assertEqual(res, '15e178b71fae8849ee562c9cc0d7ea322fba6cd495411329d47234479167cc8b', "Correctly Merkleizes 'hello world'")

    def test_4(self):
      res = merkleize("Oh joyous day!")
      self.assertEqual(res, '74bc14151a6067587e003b4771e4ffe091689ea96111785c89e2e2ae10aa0f22', "Correctly Merkleizes 3-word sentence")

    def test_5(self):
      res = merkleize("I write this sitting in the kitchen sink.")
      self.assertEqual(res, '7b688bc59bd9dcb9c07739cd48d2cdf7857430e0892fdab4c5270bd1656e5f99', "Correctly Merkleizes 8-word sentence")

    def test_6(self):
      res = merkleize("It was a bright cold day in April, and the clocks were striking thirteen.")
      self.assertEqual(res, '36a2ed4b6587fc2384a925687df8a7a772b4ec7a9ba54eeef7f9d92a042794dc', "Correctly Merkleizes 14-word sentence")

######################### Part 2 #######################

    @classmethod
    def setUpClass(self):
      sentence = '1 2 3 4'
      self.h1, self.h2, self.h3, self.h4 = [_sha2(s) for s in sentence.split()]
      self.h12 = _sha2(self.h1 + self.h2)
      self.h34 = _sha2(self.h3 + self.h4)
      self.root = _sha2(self.h12 + self.h34)
  
    def test_7(self):
      res = validate_proof(self.root, "3", [(self.h4, Side.RIGHT), (self.h12, Side.LEFT)])
      self.assertTrue(res, "validate_proof validates a correct proof")

    def test_8(self):
      res = validate_proof(self.root, "3", [(self.h4, Side.RIGHT), (self.h12, Side.RIGHT)])
      self.assertFalse(res, "Doesn't validate an incorrectly aligned proof")

    def test_9(self):
      res = validate_proof(self.root, "1", [(self.h4, Side.RIGHT), (self.h12, Side.LEFT)])
      self.assertFalse(res, "Doesn't validate a proof of the wrong element")

if __name__ == '__main__':
    unittest.main(failfast=True)