def erc_start():
    erc_start = """
import math
import c4d
def main():
    global Output1
    global current
    Output1 = 0
    """
    return erc_start


def erc_var(bone, direction):
    if bone != "None":
        return "math.degrees((" + direction + " * var"
    else:
        return "float((" + direction + " * var"


def erc_keyed(dist, maximum, minimum, norm_dist, x, var):
    erc_keyed = """
    global var{4}
    var{4} = {5}{4}))
    if {0} < 0:
        if {1} <= var{4} <= {2}:
            Output1 += abs((var{4} - {2})/{0})
        elif {1} >= var{4}:
            Output1 = 1
        else:
            Output1 = 0
    if {0} > 0:
        if {2} <= var{4} <= {1}:
            Output1 = abs((var{4} - {2} * {3}) / {0})
        elif {1} <= var{4}: 
            Output1 = 1
        else:
            Output1 = 0
                """.format(
        dist, maximum, minimum, norm_dist, x, var
    )
    return erc_keyed


def erc_delta_add(scalar, addend, x, var):
    erc_delta_add = """
    global var{2}
    var{2} = {3}{2}))
    delta_add = {0} + {1}
    Output1 += var{2} * delta_add
                """.format(
        scalar, addend, x, var
    )
    return erc_delta_add


def erc_divide_into(addend, x, var):
    erc_divide_into = """
    global var{1}
    var{1} = {2}{1}))
    Output1 *= var{1} / current + {0} 
                """.format(
        addend, x, var
    )
    return erc_divide_into


def erc_divide_by(addend, x, var):
    erc_divide_by = """
    global var{1}
    var{1} = {2}{1}))
    Output1 *= current / var{1} + {0} 
                """.format(
        addend, x, var
    )
    return erc_divide_by


def erc_multiply(addend, x, var):
    erc_multiply = """
    global var{1}
    var{1} = {2}{1}))
    if current > 0:
        Output1 += var{1} * current + {0} 
    else:
        Output1 *= var{1} + {0} 
                """.format(
        addend, x, var
    )
    return erc_multiply


def erc_subtract(addend, x, var):
    erc_multiply = """
    global var{1}
    var{1} = {2}{1}))
    Output1 += current - var{1} + {0} 
                """.format(
        addend, x, var
    )
    return erc_multiply


def erc_add(addend, x, var):
    erc_add = """
    global var{1}
    var{1} = {2}{1}))
    Output1 = var{1} + current + {0} 
                """.format(
        addend, x, var
    )
    return erc_add


def erc_limits(min, max):
    erc_limits = """
    if Output1 < {0}:
        Output1 = 0
    elif Output1 > {1}:
        Output1 = 1 
    """.format(
        min, max
    )
    return erc_limits
