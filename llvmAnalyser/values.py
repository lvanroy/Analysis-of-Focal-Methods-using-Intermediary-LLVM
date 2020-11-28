# this function accepts a chain of tokens and will return the defined value within it
# the value needs to start on the first token
# the return will be a tuple containing the value that was found, as well as the remaining tokens


def get_value(tokens):
    # read the parameter value
    angle_brackets = 0
    square_brackets = 0
    curly_brackets = 0
    round_brackets = 0
    value = ""
    while True:
        angle_brackets = angle_brackets + tokens[0].count("<") - tokens[0].count(">")
        square_brackets = square_brackets + tokens[0].count("[") - tokens[0].count("]")
        curly_brackets = curly_brackets + tokens[0].count("{") - tokens[0].count("}")
        round_brackets = round_brackets + tokens[0].count("(") - tokens[0].count(")")
        value += tokens.pop(0)

        if angle_brackets == 0 and square_brackets == 0 and curly_brackets == 0 and \
                ((value[-1] == ")" and round_brackets == -1) or
                 (value[-1] == "," and round_brackets == 0)):
            if value[-1] == ")":
                tokens.insert(0, ')')
                value = value.rsplit(")", 1)[0]
            else:
                value = value.rsplit(",", 1)[0]

            if value[-1] == ",":
                value = value[:-1]
            return value, tokens
