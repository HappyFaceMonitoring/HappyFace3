
from sqlalchemy import *
import hf

metadata = MetaData()
engine = None

def connect(implicit_execution=False):
    config = dict(hf.config.items("database"))
    hf.database.engine = engine_from_config(config, prefix="")
    if implicit_execution == True:
        metadata.bind = hf.database.engine

def disconnect():
    pass
