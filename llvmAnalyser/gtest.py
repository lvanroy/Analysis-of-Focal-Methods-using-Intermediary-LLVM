class Gtest:
    def __init__(self):
        pass

    @staticmethod
    def identify_test_function(line):
        if "TestBodyEv" in line:
            return True
        else:
            return False
