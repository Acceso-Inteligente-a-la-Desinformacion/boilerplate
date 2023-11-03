import sqlite3
import random
import datetime

from typing import List

class DbField:
    def __init__(self, name: str, type: str, min: int = 0, max: int = 1000):
        self.name = name.replace(' ', '_').upper()
        self.type = type
        self.min = min
        self.max = max
    
    def get(self):
        return f'{self.name.upper()} {self.type.upper()}'
    
    def exampleValue(self):
        if self.type.lower() == 'text':
            value = self.name.capitalize() + ' ' + str(random.randint(self.min, self.max))
        elif self.type.lower() == 'int':
            value = random.randint(self.min, self.max)
        elif self.type.lower() == 'date':
            value = datetime.datetime.now()

        return value
    
class DbTable:
    def __init__(self, name: str, fields: List[DbField]):
        self.name = name.lower().replace(' ', '_')
        self.fields = fields

class DB:
    def __init__(self, dbName: str, tables: List[DbTable] = [], enviorenment: str = 'prod'):

        self.dbName = dbName
        self.tables = tables
        
        self.connection = None

        self.enviorenment = enviorenment

        self.connect()
        self.createSchema()

    def getTable(self, tableName: str):
        for table in self.tables:
            if table.name == tableName:
                return table

    def rebuildSchema(self, env:str = 'dev'):
        for table in self.tables:
            if self.enviorenment == 'dev' and env == 'dev':
                self.dropTable(table.name, 'dev')
                self.createTable(table.name, 'dev')
                self.dummyData(table)

            self.dropTable(table.name)
            self.createTable(table.name)

    def createSchema(self):
        for table in self.tables:
            if self.enviorenment == 'dev':
                self.createTable(table.name, 'dev')
                self.dummyData(table)

            self.createTable(table.name)
        

    def dummyData(self, table: DbTable, quantity: int = 25):
        while(quantity > 0):
            data = []
            for field in table.fields:
                data.append(field.exampleValue())

            t = tuple(e for e in data)

            self.insert(table.name, t, 'dev')

            quantity -= 1

    def connect(self):
        connection = sqlite3.connect(self.dbName+'.db')
        connection.text_factory = str

        self.connection = connection

    def dropTable(self, tableName: str, env: str = 'prod'):
        table = self.getTable(tableName)

        if(env == 'dev'):
            appendName = f'_{env}'
        else:
            appendName = ''

        self.connection.execute("DROP TABLE IF EXISTS "+table.name+appendName)
        self.connection.commit()

    def closeConnection(self, env: str = 'prod'):
        self.connection.close()

    def exec(self, query: str, data: tuple = ()):

        #print(query)
        #print(data)

        if len(data):
            result = self.connection.execute(query, data)
        else:
            result = self.connection.execute(query)

        self.connection.commit()
        return result
    
    def createTable(self, tableName: str, env: str = 'prod'):
        table = self.getTable(tableName)
        
        if(env == 'dev'):
            appendName = f'_{env}'
        else:
            appendName = ''

        fieldsQuery = ""
        i = 1
        for field in table.fields:
            fieldsQuery += field.get() + (', ' if i<len(table.fields) else '')
            i += 1

        return self.exec("CREATE TABLE IF NOT EXISTS "+table.name+appendName+" ("+fieldsQuery+");")
    
    def insert(self, tableName: str, data: tuple, env: str = 'prod'):

        table = self.getTable(tableName)

        if(env == 'dev'):
            appendName = f'_{env}'
        else:
            appendName = ''
    
        variables = ''
        i = 1
        for field in table.fields:
            variables += '?' + (',' if i<len(table.fields) else '')
            i += 1

        return self.exec(f"INSERT INTO {table.name}{appendName} VALUES ({variables})", data)

    def countTable(self, tableName: str):
        return self.exec('SELECT COUNT(*) FROM '+tableName).fetchone()[0]