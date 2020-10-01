class StoreAnalyzer:
    def __init__(self):
        pass

    def analyzer_store(self, tokens, function_memory):
        i = 1
        if tokens[i] == "volatile":
            i += 1

        # skip type
        i += 1
        if tokens[i] in {"()", "()*"}:
            i += 1

        value = tokens[i].replace(",", "")
        i += 1

        # skip type
        i += 1
        if tokens[i] in {"()", "()*"}:
            i += 1

        register = tokens[i].replace(",", "")
        register_obj = function_memory.get_register_object(register)
        register_obj.set_value(value)
