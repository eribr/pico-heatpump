def reverse_bits(value, bit_length):
    reversed_value = 0
    for i in range(bit_length):
        bit = (value >> i) & 1
        reversed_value |= bit << (bit_length - 1 - i)
    return reversed_value

def reverse_bits_8(value):
    return reverse_bits(value, 8)

def reverse_bits_16(value):
    return reverse_bits(value, 16)