def erc_start():
    erc_start = """
    import math
    def main():
        global Output1
    """


def erc_keyed(dist, maximum, minimum, norm_dist):
    erc_keyed = """
    global var
    var = math.degrees(var)
    if {0} < 0:
        if {1} <= var <= {2}:
            Output1 = abs((var - {2})/{0})
        elif {1} >= var:
            Output1 = 1
        else:
            Output1 = 0
    if {0} > 0:
        if {2} <= var <= {1}:
            Output1 = abs((var - {2} * {3}) / {0})
        elif {1} <= var: 
            Output1 = 1
        else:
            Output1 = 0
                """.format(
        dist, maximum, minimum, norm_dist
    )
    return erc_keyed


def erc_delta_add(scalar, addend):
    erc_delta_add = """
    global var
    var = math.degrees(var)
    delta_add = scalar + addend
    Output1 = var * 
                """.format(
        scalar, addend
    )
    return erc_delta_add


def erc_divide_into(scalar):
    erc_divide_into = """
    global var
    var = math.degrees(var)
    Output1 = var / current + addend 
                """.format(
        scalar
    )
    return erc_divide_into


def erc_divide_by(addend):
    erc_divide_by = """
    global var
    var = math.degrees(var)
    Output1 = current / var + addend 
                """.format(
        addend
    )
    return erc_divide_by


def erc_multiply(addend):
    erc_multiply = """
    global var
    var = math.degrees(var)
    if current > 0:
        Output1 = var * current + addend 
    else:
        Output1 = var + addend 
                """.format(
        addend
    )
    return erc_multiply


def erc_subtract(addend):
    erc_multiply = """
    global var
    var = math.degrees(var)
    Output1 = current - var + addend 
                """.format(
        addend
    )
    return erc_multiply


def erc_add(addend):
    erc_multiply = """
    global var
    var = math.degrees(var)
    Output1 = var + current + addend 
                """.format(
        addend
    )
    return erc_multiply
