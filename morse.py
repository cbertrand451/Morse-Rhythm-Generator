# Mapping from characters to Morse code patterns
MORSE_DICT = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "0": "-----",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    ".": ".-.-.-",
    ",": "--..--",
    "?": "..--..",
    "!": "-.-.--",
    "'": ".----.",
    '"': ".-..-.",
    "/": "-..-.",
    "(": "-.--.",
    ")": "-.--.-",
    "&": ".-...",
    ":": "---...",
    ";": "-.-.-.",
    "=": "-...-",
    "+": ".-.-.",
    "-": "-....-",
    "_": "..--.-",
}


# Turn input text into a list of Morse tokens
def text_to_morse(text):
    # empty morse
    morse = []
    # if nothing then return nothing
    if not text:
        return morse
    # character loop, makes upper
    for ch in text.upper():
        # if the character is whitespace, add a gap
        if ch.isspace():
            if morse and morse[-1]["type"] != "word_gap":
                morse.append({"type": "word_gap"})
            continue
        # checks to make sure its a valid character
        if ch not in MORSE_DICT:
            continue
        # written for chance I ever want to put a gap in between each letter, rn its 0
        if morse and morse[-1]["type"] == "letter":
            morse.append({"type": "letter_gap"})
        # otherwise append the morse rhythms as normal
        morse.append({"type": "letter", "value": MORSE_DICT[ch], "char": ch})

    return morse
