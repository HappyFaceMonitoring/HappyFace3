"""
 An interactive execution shell for HappyFace
"""

import code, traceback, sys
import hf

def execute(args):
    code.interact("Interactive HappyFace Shell", local={'hf':hf})