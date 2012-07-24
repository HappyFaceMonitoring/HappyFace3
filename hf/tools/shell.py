"""
 An interactive execution shell for HappyFace
"""

import code, traceback, sys
import hf

def execute():
    code.interact("Interactive HappyFace Shell", local={'hf':hf})