# -*- coding: utf-8 -*-
import sqlalchemy
class DbDiff(object):
    def __init__(self, model, database_engine, excludedTables=None):
        #get metadata from model and database
        self.database = sqlalchemy.MetaData(database_engine, reflect = True)
        #import pdb; pdb.set_trace()
        self.conn = self.database._bind
        self.model = model
        #construct sets of all tables in database/model
        self.tablesInModel = set(self.model.tables.keys())
        self.tablesInDatabase = set(self.database.tables.keys())
        self.exclude = set(excludedTables or [])
        #construct sets with tablenames of missing and extra tables in database and model
        self.tables_missing_in_model = self.tables_extra_in_database = set(\
            sorted(self.tablesInDatabase - self.tablesInModel - self.exclude))
        self.tables_missing_in_database = self.tables_extra_in_model = set(\
            sorted(self.tablesInModel - self.tablesInDatabase - self.exclude))
        
        self.tables_different = {}
        for table_name in self.tablesInDatabase ^ self.tables_missing_in_database:
	    try:
		self.diff_table = TableDiff(self.model.tables[table_name],
					    self.database.tables[table_name],
					    table_name)
		if self.diff_table:
		    self.tables_different[table_name] = self.diff_table
	    except KeyError:
		continue
        self.differences = bool(self.tables_missing_in_database or self.tables_extra_in_database or
                                self.tables_different)
        
    def __nonzero__(self):
        return self.differences
    __bool__ = __nonzero__
    
    def tables_to_operate(self):
        self.remove_from_DB = [self.database.tables[t_name] for t_name in self.tables_extra_in_database]
        self.add_to_DB = [self.model.tables[t_name] for t_name in self.tables_extra_in_model]
        self.alter_in_DB = dict([
            (t_name, [self.database.tables[t_name], tablediff]) for t_name, tablediff in 
            self.tables_different.iteritems()])
        return (self.remove_from_DB, self.add_to_DB, self.alter_in_DB)
        
class TableDiff(object):
    def __init__(self, model_Table, database_Table, table_name):
        self.name = table_name
        self.dbTable = database_Table
        self.modTable = model_Table
        
        self.columnsInDatabase = set(self.dbTable.columns.keys())
        self.columnsInModel = set(self.modTable.columns.keys())
        
        self.columns_missing_in_model = self.columns_drop_from_database = set(\
            sorted(self.columnsInDatabase - self.columnsInModel))
        self.columns_missing_in_database = self.columns_add_to_database = set(\
            sorted(self.columnsInModel - self.columnsInDatabase))
        self.columns_alter_in_database = {}
        
        for c_name in self.columnsInDatabase - self.columns_missing_in_model:
            modCol_type = str(self.modTable.columns[c_name].type).replace('SMALLINT', 'BOOLEAN')
            dbCol_type = str(self.dbTable.columns[c_name].type).replace('SMALLINT', 'BOOLEAN')
            
            if modCol_type != dbCol_type:
                self.columns_alter_in_database[c_name] = '%s=>%s' %(dbCol_type, modCol_type)
        
        self.differences = bool(self.columns_drop_from_database or self.columns_add_to_database or
                                self.columns_alter_in_database)
    
    def columns_to_operate(self):
        self.columnsAddToDb = [self.modTable.columns[c_name] for c_name in
                                self.columns_add_to_database]
        self.columnsDropFromDb = [self.dbTable.columns[c_name] for c_name in
                                self.columns_drop_from_database]
        self.columnsAlterInDb = dict([
            (c_name, [self.dbTable.columns[c_name], mod])
            for c_name, mod in self.columns_alter_in_database.iteritems()])
	#import pdb; pdb.set_trace()
        return (self.columnsDropFromDb, self.columnsAddToDb, self.columnsAlterInDb)
        
    def __nonzero__(self):
        return self.differences
    __bool__ = __nonzero__