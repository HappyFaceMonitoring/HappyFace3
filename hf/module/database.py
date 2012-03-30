
import hf.database
from sqlalchemy import *

module_instances = Table("module_instances", hf.database.metadata,
    Column("instance", Text, primary_key=True),
    Column("module", Text)
)

hf_runs = Table("hf_runs", hf.database.metadata,
    Column("id", Integer, Sequence('module_instances_id_seq'), primary_key=True),
    Column("time", DateTime, unique=True)
)