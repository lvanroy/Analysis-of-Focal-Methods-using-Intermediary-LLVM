class Gtest:
    def __init__(self):
        pass

    @staticmethod
    def identify_test_function(line):
        if "type { %\"class.testing::Test\" }" in line:
            return line.split(" = ")[0].split("class.")[1]
        else:
            return None
