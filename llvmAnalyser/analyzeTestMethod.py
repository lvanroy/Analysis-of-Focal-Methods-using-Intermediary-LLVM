# if the variable traces back to a constant, return None, else, return the
# mutator that assigned last to it

def get_focal_method(current_node, variable_under_test, depth=0):
    print(current_node)
    print(variable_under_test)
