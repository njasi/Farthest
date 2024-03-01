"""
This program decrypts the file in two parts: parsing and decoding.

First, it parses the file provided into a dictionary of number word pairs.
This allows for easy access in the next step where we decrypt the message.

To start decoding we sort all of the dictionary keys and iterate to determine what key will be at the
rightmost side of the pyramid per layer. We do this by keeping track of the last accessed index in the array,
and incrementing it by what number step we are on, as this corresponds to the width. Since this gives us the
key we can look it up in the dictionary and collect the words for the decoded message
"""

def decode(message_file: str):
    """
    Decodes a step encoded text file
    """
    return decode_dict(parse_file(message_file))


def parse_file(message_path: str):
    """
    Parse the file into a dictionary of number word pairs
    """
    result = {}
    with open(message_path, "r") as file:
        lines = file.readlines()
        for line in lines:
            num, word = line.split(" ")
            result[int(num)] = word.strip()
    return result


def decode_dict(message_dict):
    """
    Decode the dictionary of words parsed earlier
    """
    decoded = []
    keys = sorted(message_dict.keys())

    step = 0
    idx = 0
    while idx < len(keys):
        # add new word
        decoded.append(message_dict[keys[idx + step]])
        step += 1
        idx += step

    return " ".join(decoded)


print(decode("src/test.txt"))



"""

"""