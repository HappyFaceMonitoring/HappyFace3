import sys, os

class HTMLOutput(object):
    def __init__(self, indentation = 0):
        self.indentation = indentation;

    # Converts an array of strings to a single string by concatenating all
    # its entries, separated with a newline character, optionally indenting
    # each line by a constant amount of space characters. If trailing_newline
    # is false then the last line will not contain a trailing newline character.
    def PHPArrayToString(self, arr):
        str = ""
        indent = ' '*self.indentation

        for i in arr:
	    if i:
                str += indent + i + '\n'
	    else:
	        str += '\n'

	return str
