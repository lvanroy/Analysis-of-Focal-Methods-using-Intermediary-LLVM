import re
from llvmAnalyser.types import get_type

# this function accepts a chain of tokens and will return the defined value within it
# the value needs to start on the first token
# the return will be a tuple containing the value that was found, as well as the remaining tokens

boolean = re.compile(r'^((false)|(true))(,|\))?$')
fp = re.compile(r'^[-+]?[0-9]+[.]?[0-9]*([eE][-+]?[0-9]+)?(,|\))?$')
fp_hex = re.compile(r'^0x[0-9a-fA-F]+(,|\))?$')
null_none_undef = re.compile(r'^((null)|(none)|(undef))(,|\))?$')
zeroinitializer = re.compile(r'^zeroinitializer(,|\))?$')
global_var = re.compile(r'^@([_\.][0-9a-zA-Z]+)+(,|\))?$')


def remove_trailing_char(value):
    if value[-1] == ",":
        value = value[:-1]
    if value[-1] == ")":
        value = value[:-1]
    return value


def get_value(tokens):
    value = tokens.pop(0)

    # match registers
    if value[0] == "%":
        value = remove_trailing_char(value)
        return value, tokens

    # match booleans
    if boolean.match(value):
        value = remove_trailing_char(value)
        return value, tokens

    # match numeric constants
    if fp.match(value):
        value = remove_trailing_char(value)
        return value, tokens

    # match hexadecimal numeric constants
    if fp_hex.match(value):
        value = remove_trailing_char(value)
        return value, tokens

    # match null and none
    if null_none_undef.match(value):
        value = remove_trailing_char(value)
        return value, tokens

    # match zero initialization
    if zeroinitializer.match(value):
        value = remove_trailing_char(value)
        return value, tokens

    # match global var
    if global_var.match(value):
        value = remove_trailing_char(value)
        return value, tokens

    if value in ["trunc", "zext", "sext", "fptrunc", "fpext",
                 "fptoui", "fptosi", "uitofp", "sitofp", "ptrtoint",
                 "inttoptr", "bitcast", "addrspacecast"]:
        return get_value_from_conversion(value, tokens), tokens

    if value == "getelementptr":
        return get_value_from_getelementptr(value, tokens), tokens

    # read construct value
    while True:
        angle_brackets = value.count("<") - value.count(">")
        square_brackets = value.count("[") - value.count("]")
        curly_brackets = value.count("{") - value.count("}")
        round_brackets = value.count("(") - value.count(")")

        if angle_brackets == 0 and square_brackets == 0 and curly_brackets == 0 and \
                ((value[-1] == ")" and round_brackets == -1) or
                 (round_brackets == 0)):
            if value[-1] == ")" and round_brackets == -1:
                tokens.insert(0, ')')
                value = value[:-1]
            elif value[-1] == ",":
                value = value[:-1]

            return value, tokens

        value += " {}".format(tokens.pop(0))


def get_value_from_conversion(op, tokens):
    # get the original value
    type1, tokens = get_type(tokens)
    op += " {}".format(type1)
    value, tokens = get_value(tokens)
    op += " {}".format(value)

    # pop the to token
    op += " {}".format(tokens.pop(0))

    # get the final type
    type2, tokens = get_type(tokens)
    op += " {}".format(type2)

    # pop potential remaining tokens
    while tokens and "dereferenceable" in tokens[0]:
        tokens.pop(0)

    return op


def get_value_from_getelementptr(value, tokens):
    # pop a potential inbounds keyword
    if tokens[0] == "inbounds":
        value += " {}".format(tokens.pop(0))

    # get the type
    type1, tokens = get_type(tokens)
    value += " {},".format(type1)

    # get the second type
    type2, tokens = get_type(tokens)
    value += " {}".format(type2)

    # get the value
    const_val, tokens = get_value(tokens)
    value += " {},".format(const_val)

    # access potential further indices
    while value[-1] == ",":
        if tokens[0] == "inrange":
            value += " {}".format(tokens.pop(0))

        # get the index type
        idx_type, tokens = get_type(tokens)
        value += " {}".format(idx_type)

        # get the index value
        value += " {}".format(tokens.pop(0))

    return value
