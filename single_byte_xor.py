#!/usr/bin/python

def xor(str1, str2):
    if len(str1) != len(str2):
        raise "errno: strings are not of equal length"
    s1 = bytearray(str1)
    s2 = bytearray(str2)
  
    result = bytearray()
    for i in range(len(s1)):
        result.append( s1[i] ^ s2[i] )
    
    return str(result)

def single_byte_xor(plaintext, key):
    if len(key) != 1:
      raise "errno: key length must be a single byte"
    return xor(plaintext, key*len(plaintext))

def break_single_byte_xor(ciphertext):
    keys = []
    plaintext = []
  
    for key in range(256):
        text = single_byte_xor(ciphertext, chr(key))
        if "flag" in text: # change flag to match whatever value should be in key
            keys.append(chr(key))
            plaintext.append(text)
    return keys, plaintext


ciphertext = "define_ciphertext_here"
k, pt = break_single_byte_xor(ciphertext)  
print ("Keys: ", k)
print ("Plaintexts: ", pt)