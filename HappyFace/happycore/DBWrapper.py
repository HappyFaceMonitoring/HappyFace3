
from DataBaseLock import *
from sqlobject import *
import re, traceback, os

class DBWrapper(object):
    """
    Mother of all wrappers
    """
    
    def listOfTables(self):
        return []
    
    def __init__(self, dbConnection = None):
        object.__init__(self)
        self.lock = DataBaseLock().lock
        
        if dbConnection is None: self.dbConnection = sqlhub.processConnection
        else: self.dbConnection = dbConnection
        
        # Store a reserved SQL keywords that cannot be used as column names.
        # NOTE: This is mostly for a workaround because SQLObject does not
        # quote column names when generating queries. This leads to errors
        # if an SQL keyword is used as column name, but reserved keywords
        # differ from underlying database engines. If we encounter a problematic
        # column name, we set the dbName attribute of the column if it is not
        # set already by the module code.
        # I hope that this code won't break with future SQLObject releases,
        # since it accesses some internal, but not too deep, data.
        self.reserved_names = ['select', 'insert', 'drop', 'delete', 'truncate', 'update', 'where', 'order', 'by', 'join', 'inner', 'outer', 'left', 'right', 'as', 'alter', 'table', 'database']
        
        
    def table_init(self, tableName, table_keys):
        
        # timestamp will always be saved
        table_keys["timestamp"] = IntCol()

        # create an index for the timestap column for faster access
        table_keys["index"] = DatabaseIndex('timestamp')
        
        # lock object enables exclusive access to the database
        self.lock.acquire()
        
        # watch out for reserved SQL keywords in column names and prefix them
        # with an underscore if dbName is not set. See comment of reserved_names
        # for more info.
        real_keys = {}
        for key in table_keys.iterkeys():
            real_keys[key] = key
            if key in self.reserved_names and '_kw' in table_keys[key].__dict__:
                try:
                    if len(table_keys[key].__dict__['_kw']['dbName']) == 0:
                        table_keys[key].__dict__['_kw']['dbName'] = '_'+key
                        real_keys[key] = '_'+key
                except:
                    table_keys[key].__dict__['_kw']['dbName'] = '_'+key
                    real_keys[key] = '_'+key
            
        try: # separate try for finally block so we are compatible with Python 2.4
            try:
                class sqlmeta:
                    table = tableName
                    fromDatabase = True

                My_DB_Class = type(tableName, (SQLObject,), dict([('_connection',self.dbConnection)]+table_keys.items()))
                My_DB_Class.createTable(ifNotExists=True)

                DBProxy = type(tableName + "_DBProxy",(SQLObject,),dict(sqlmeta = sqlmeta, _connection=self.dbConnection))

                avail_keys = []
                for key in DBProxy.sqlmeta.columns.iterkeys():
                    avail_keys.append( re.sub('[A-Z]', lambda x: '_' + x.group(0).lower(), key) )
                new_columns = dict( (key, real) for key,real in real_keys.iteritems() if real not in avail_keys)
                if len(new_columns) > 0:

                    for key, real_key in new_columns.iteritems():
                        if key != "index":
                            try:
                                DBProxy.sqlmeta.addColumn(table_keys[key].__class__(real_key), changeSchema=False)

                                # It is also possible to create the new column by setting changeSchema to True
                                # above. However, this is VERY slow for large SQLite databases.
                                # This is why we run an ALTER TABLE query manually here, which is
                                # much faster (returns almost instantly).
                                sqlType = {IntCol: 'INT', StringCol: 'TEXT', UnicodeCol: 'TEXT', FloatCol: 'FLOAT'}[table_keys[key].__class__]
                                self.dbConnection.query('ALTER TABLE %s ADD COLUMN %s %s' % (tableName, real_key, sqlType))
                            except Exception, ex: print "Failing at adding new column: \"" + str(real_key) + "\" in the module " + self.__module__ + ": " + str(ex)

            except Exception, e:
                print 'Failed to create table %s: %s' % (tableName, e)
                traceback.print_exc()
        finally:
            # unlock the database access
            self.lock.release()
        
        return My_DB_Class

    def table_fill(self, My_DB_Class, table_values):
        # lock object enables exclusive access to the database
        self.lock.acquire()

        try:
            My_DB_Class(**table_values)
        finally:
            # unlock the database access
            self.lock.release()

    def __table_fill_many__(self, My_DB_Class, table_values, placeholder_fmt):
        """
        This should be used instead of table_fill if many rows are to be inserted
        since this can be much faster than calling table_fill multiple times, depending
        on the implementation and underlying database.
        """
        # lock object enables exclusive access to the database
        self.lock.acquire()
        

        try:
            # Inserting using SQLObject is quite slow, so we use executemany
            # directly within a transaction which is faster by at least
            # a factor 10. See also this for a comparison between various APIs:
            # http://pyinsci.blogspot.com/2007/07/fastest-python-database-interface.html

            # TODO: I am not sure how sqlite-specific this code is, maybe
            # needs to be changed/adapted for other DBMSes if we switch one day.
            connection = self.dbConnection
            dbObject = connection.getConnection()
            cursor = dbObject.cursor()

            name = My_DB_Class.sqlmeta.table
            columns = [col.dbName for col in My_DB_Class.sqlmeta.columns.itervalues()]
            
            # take the dbName property of columns into account
            # also, I'm sorry, but I love generators
            corrected_table_values = [dict((My_DB_Class.sqlmeta.columns[key].dbName, value) for key,value in row.iteritems()) for row in table_values]

            cursor.execute('BEGIN')
            cursor.executemany('INSERT INTO ' + name + '(' + ','.join(columns) + ') VALUES (' + ','.join(map(lambda x: placeholder_fmt%x, columns)) + ')', corrected_table_values)
            cursor.execute('COMMIT')
        finally:
            self.lock.release()
    
    def table_clear(self, My_DB_Class, archive_columns, archive_dir, time_limit):
        self.lock.acquire()

        try: # separate try for finally block so we are compatible with Python 2.4
            try:
                old_data = My_DB_Class.select( My_DB_Class.q.timestamp <= time_limit)

                for row in old_data:
                    for column in archive_columns:
                        file = getattr(row,column)

                        # If Download failed the column might be empty. We don't
                        # have anything to do in that case.
                        if file is None:
                            break

                        # Find archive directory for this file
                        # TODO: This is a bit of a hack as we are not supposed to know
                        # anything about the archive directory structure... should find
                        # a better solution for this
                        timestamp = row.timestamp
                        time_tuple = time.localtime(timestamp)

                        output_dir = archive_dir
                        while os.path.basename(output_dir) != 'archive':
                            output_dir = os.path.dirname(output_dir)

                        archive_dir = output_dir + "/" + str(time_tuple.tm_year) + "/" + ('%02d' % time_tuple.tm_mon) + "/" + ('%02d' % time_tuple.tm_mday) + "/" + str(timestamp)
                        file = archive_dir + '/' + file

                        try:
                            # Remove archived files
                            os.unlink(file)
                            # Remove empty directories (note this throws if a
                            # directory attempted to be removed is not empty).
                            dir = archive_dir
                            while dir != output_dir:
                                os.rmdir(dir)
                                dir = os.path.dirname(dir)
                        except:
                            pass

                My_DB_Class.deleteMany(My_DB_Class.q.timestamp <= time_limit)
            except Exception, ex:
                print 'Failed to clear table: ' + str(ex)
                traceback.print_exc()
        finally:
                self.lock.release()
    
    def getPHPConnectionConfig(self, connectionString):
        """
        This function returns an array of arguments passed to the PDO constructor.
        Derived classes should convert the connection string for a database backend to valid arguments.
        This method here just a dummy, passing the connectionString argument as first parameter.
        """
        return [connectionString]

class SQLiteWrapper(DBWrapper):
    def table_fill_many(self, My_DB_Class, table_values):
        self.__table_fill_many__(My_DB_Class, table_values, placeholder_fmt=':%s')
    
    def getPHPConnectionConfig(self, connectionString):
        result = re.match("sqlite://(.+)", connectionString)
        return ["sqlite:"+result.group(1)]
    
    def listOfTables(self):
        conn = self.dbConnection.getConnection()
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
        rows = cursor.fetchall() # Fetch all to avoid a lock on the table
        cursor.close()
        return [row[0] for row in rows]

class PostgresWrapper(DBWrapper):
    def __init__(self, dbConnection=None):
        DBWrapper.__init__(self, dbConnection)
        self.reserved_names.extend(['user'])
    def table_fill_many(self, My_DB_Class, table_values):
        self.__table_fill_many__(My_DB_Class, table_values, placeholder_fmt='%%(%s)s')
    
    def getPHPConnectionConfig(self, connectionString):
        parameters = {}
        # default parameters, if applicable
        parameters['port'] = 5432
        
        result = re.match("postgres://([^@]*)@?([^/]+)/(.+)", connectionString)
        if result is None:
            print PostgresWrapper.__module__+": Cannot parse connection string to extract PHP parameters"
        user_part = result.group(1)
        host_part = result.group(2)
        dbName = result.group(3)
        
        
        try: parameters["user"] = user_part.split(":")[0]
        except: pass
        try: parameters["password"] = user_part.split(":")[1]
        except: pass
        try: parameters["host"] = host_part.split(":")[0]
        except: pass
        try: parameters["port"] = host_part.split(":")[1]
        except: pass
        
        parameters['dbname'] = dbName
        
        return ["pgsql:" + ";".join([key+"="+str(value) for key,value in parameters.iteritems()]) ]

# This variable contains the DBWrapper that is used by all modules
SelectedDBWrapper = None
