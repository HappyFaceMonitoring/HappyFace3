"""
 An interactive execution shell for HappyFace
"""

import code, traceback, sys
import hf

load_hf_environment = True

def execute():
    code.interact("Interactive HappyFace Shell", local={'hf':hf})