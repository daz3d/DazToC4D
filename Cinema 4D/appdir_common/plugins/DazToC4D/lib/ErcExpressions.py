"""
For More information on ERC Types Check out our Documentaion on it.
http://docs.daz3d.com/doku.php/public/software/dazstudio/4/referenceguide/scripting/api_reference/object_index/erclink_dz
Note: ErcKeyed is not calculated the same way as in Daz Studio and uses a linear interporlation method.
      This method does not calculated all keyed values and only works for the first two values. 
"""


def erc_start():
    erc_start = """
import math
import c4d
def main():
    global Output1
    global current
    Output1 = 0
    temp = 0
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
            temp += abs((var{4} - {2})/{0})
        elif {1} >= var{4}:
            temp = 1
        else:
            temp = 0
    if {0} > 0:
        if {2} <= var{4} <= {1}:
            temp = abs((var{4} - {2} * {3}) / {0})
        elif {1} <= var{4}: 
            temp = 1
        else:
            temp = 0
                """.format(
        dist, maximum, minimum, norm_dist, x, var
    )
    return erc_keyed


def erc_delta_add(scalar, addend, x, var):
    erc_delta_add = """
    global var{2}
    var{2} = {3}{2}))
    delta_add = {0} + {1}
    temp += var{2} * delta_add
                """.format(
        scalar, addend, x, var
    )
    return erc_delta_add


def erc_divide_into(addend, x, var):
    erc_divide_into = """
    global var{1}
    var{1} = {2}{1}))
    temp *= var{1} / current + {0} 
                """.format(
        addend, x, var
    )
    return erc_divide_into


def erc_divide_by(addend, x, var):
    erc_divide_by = """
    global var{1}
    var{1} = {2}{1}))
    temp *= current / var{1} + {0} 
                """.format(
        addend, x, var
    )
    return erc_divide_by


def erc_multiply(addend, x, var):
    erc_multiply = """
    global var{1}
    var{1} = {2}{1}))
    if current > 0:
        temp += var{1} * current + {0} 
    else:
        temp *= var{1} + {0} 
                """.format(
        addend, x, var
    )
    return erc_multiply


def erc_subtract(addend, x, var):
    erc_multiply = """
    global var{1}
    var{1} = {2}{1}))
    temp += current - var{1} + {0} 
                """.format(
        addend, x, var
    )
    return erc_multiply


def erc_add(addend, x, var):
    erc_add = """
    global var{1}
    var{1} = {2}{1}))
    temp = var{1} + current + {0} 
                """.format(
        addend, x, var
    )
    return erc_add


def erc_limits(min, max):
    erc_limits = """
    if temp < {0}:
        Output1 = 0
    elif temp > {1}:
        Output1 = 1 
    else:
        Output1 = temp
    """.format(
        min, max
    )
    return erc_limits
