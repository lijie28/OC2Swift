import sqlite3
import sys
import os


class SqlManager(object):

    def close(self):
        self.conn.close()

    def open(self):
        # keyword, timestamp, result(json string)
        self.conn.execute('''create table IF NOT EXISTS search_history (
        keyword varchar UNIQUE PRIMARY KEY,
        timestamp varchar,
        result json);
        ''')
        self.conn.commit()

    def insert_data(self, keyword, timestamp, result):
        if "'" in result:
            result = result.replace("'", "’")
        statement = "REPLACE INTO search_history VALUES ('%s', '%s', '%s')" % (
            keyword, timestamp, result)
        # print("statement:", statement)
        # self.conn.execute(statement, data)
        self.conn.execute(statement)
        self.conn.commit()
        # self.conn.close()

    def search_data(self, keyword):
        statement = "select keyword, timestamp, result from search_history WHERE keyword='%s'" % keyword
        return self.conn.execute(statement).fetchall()

    def search_all(self):
        statement = "select * from search_history"
        return self.conn.execute(statement).fetchall()

    def __init__(self, source_path="sqlite.db"):
        # print ('初始self')
        self.conn = sqlite3.connect(source_path)
        self.conn.text_factory = str
        self.open()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        keyword = sys.argv[1]
        sql = SqlManager()
        list = sql.search_data(keyword)
        print(list)
        sql.close()
    else:
        sql = SqlManager()
        result = sql.search_all()
        for hitory in result:
            print(hitory)
            print("="*100)
        sql.close()
        # print(result)
