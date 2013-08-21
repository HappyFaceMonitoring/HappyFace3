# -*- coding: utf-8 -*-
#
# Copyright 2012 Institut für Experimentelle Kernphysik - Karlsruher Institut für Technologie
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import logging
import traceback
import math
import re


def prettyDataSize(size_in_bytes):
    """ Takes a data size in bytes and formats a pretty string. """
    unit = "B"
    size_in_bytes = float(size_in_bytes)
    if size_in_bytes > 1024:
        size_in_bytes /= 1024
        unit = "kiB"
    if size_in_bytes > 1024:
        size_in_bytes /= 1024
        unit = "MiB"
    if size_in_bytes > 1024:
        size_in_bytes /= 1024
        unit = "GiB"
    if size_in_bytes > 1024:
        size_in_bytes /= 1024
        unit = "TiB"
    print size_in_bytes, "%.1f " % size_in_bytes + unit
    return "%.1f " % size_in_bytes + unit

matheval_context = {
    "abs": abs,
    "sin": math.sin,
    "cos": math.cos,
    "sqrt": math.sqrt,
    "pow": math.pow,
    "floor": math.floor,
    "ceil": math.ceil,
    "max": max,
    "min": min,
    "float": float,
    "int": int,
}


def matheval(input, variables={}):
    """
    A safe way to evaluate mathematical expressions.

    The following Python functions are available

     * abs
     * sin
     * cos
     * sqrt
     * pow
     * floor
     * ceil
     * max
     * min
     * float
     * int

    :param input: String with mathematical expression
    :param variables: A dictionary with variables available for  input expression
    :returns: The result of the expression, or *None* in case of error.
    """

    # block everything, even builtins, and add "safe" mathematical functions.
    # Statements won't work, as well as potentially dangerous things like
    # __import__ or open.
    variables.update(matheval_context)
    try:
        return eval(input, {"__builtins__": None}, variables)
    except Exception, e:
        logging.error(traceback.format_exc())
        return None

__regex_url = re.compile(r"([-\+a-zA-Z]{2,7}://[-_a-zA-Z0-9\$\.\+!=\*'(),;/\?:@&\"#]+)")


def addAutoLinks(string):
    """
    Searches for URLs in string using a regular expression and
    adds <a>-Tags around them.
    """
    return __regex_url.sub("<a href=\"\\1\">\\1</a>", string)
