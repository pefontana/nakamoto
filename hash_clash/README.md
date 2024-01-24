# Part 1

For this assignment, first you'll be writing a Hashcash validator. Given a Hashcash token, you should be able to verify whether the Hashcash is valid. (This function will be stateless, so we won't be trying to detect double spends.) 

The Hashcash format we'll be using is Hashcash version 1, which is formatted as follows: `VERSION:DATE:EMAIL:NONCE`. 

**The value for the version should always be 1**. The date should span **no more than 6 digits**, and the nonce should be **no more than 16 hex characters.**

Your function will be provided the Hashcash token as a string, the date (formatted as a string), the email, and the difficulty in bits (as an int). Recall that the difficulty level is the number of leading 0s measured in bits. We've provided a helper function that will count the number of binary leading 0s in a hex string (given a 256-bit value).

**The hash function we'll be using is SHA-2**.

You can import it from hashlib:

```
from hashlib import sha256
```

Here's an example of a valid Hashcash token at difficulty 20: `1:081031:satoshin@gmx.com:b4c26b1694691666`

Here's an example of an invalid Hashcash token at difficulty 20: `1:081031:satoshin@gmx.com:835b8121ee4da3f8`

# Part 2

For part 2 of the assignment, you'll be writing your own Hashcash minter. This will be the complement of the Hashcash validator.

Again, your nonce should be **no more than 16 hex digits**. The hash function we'll be using is **SHA-2**.

You will be provided the date as a String, email as a string, and the difficulty in bits as an Integer. You need to compute the proof of work and output a valid Hashcash token. Your function should return the token as a string.

You can check out the canonical solution [here](https://repl.it/@nakamoto/Hashcash-Solution#main.py).