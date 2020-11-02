# analyzer for the br commands that can either be of the form
# br i1 <cond>, label <iftrue>, label <iffalse>
# br label <dest>          ; Unconditional branch

class BrAnalyzer:
    def __init__(self):
        pass

    @staticmethod
    def analyze_br(tokens: list):
        br = Br()

        # pop the br command
        tokens.pop(0)

        if tokens[0] == "label":
            br.set_label_1(tokens[1])
            return br

        # pop the i1 type specifier
        tokens.pop(0)

        # copy the condition to the br object
        br.set_condition(tokens[0])
        tokens.pop(0)

        # read the iftrue label
        tokens.pop(0)
        br.set_label_1(tokens[0].replace(",", ""))
        tokens.pop(0)

        # read the iffalse label
        tokens.pop(0)
        br.set_label_2(tokens[0])

        return br


class Br:
    def __init__(self):
        self.condition = None
        self.label1 = None
        self.label2 = None

    def set_condition(self, condition):
        self.condition = condition

    def set_label_1(self, label):
        self.label1 = label

    def get_label1(self):
        return self.label1

    def set_label_2(self, label):
        self.label2 = label

    def get_label2(self):
        return self.label2
