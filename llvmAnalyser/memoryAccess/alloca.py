class AllocaAnalyzer:
    def __init__(self):
        self.type = None
        self.num_elements = None
        self.alignment = None
        self.address_space = None

    def analyze_alloca_instruction(self, tokens):
        # skip assigned register, equality sign and alloca instruction
        i = 3

        if tokens[i] == "inalloca":
            i += 2

        if tokens[i+1] in {"()", "()*"}:
            self.type = "{} {}".format(tokens[i], tokens[i+1].replace(",", ""))
            i += 2
        else:
            self.type = tokens[i].replace(",", "")
            i += 1

        if i < len(tokens) and "align" not in tokens[i] and not tokens[i].startswith("addrspace"):
            self.num_elements = tokens[i+1]
            i += 2

        if i < len(tokens) and tokens[i] == "align":
            self.alignment = tokens[i+1]
            i += 2

        if i < len(tokens) and tokens[i].starswith("addrspace"):
            self.address_space = tokens[i]
            i += 1
