import json
import re
from datetime import datetime, date

import mariadb

from app.config import get_config
from app.core.logger import get_logger
from app.core.query import Query

CONNECTION_POOLS = {}


class Database:
    def __init__(self):
        self.config = get_config("database", {})
        self.conn: mariadb.Connection | None = None
        self.csr: mariadb.cursors.Cursor | None = None

        self.logger = get_logger()
        self.connect()

        self.query = None

    def connect(self):
        dbhost = self.config.get("host", "localhost")
        dbport = int(self.config.get("port", 3306))
        dbname = self.config.get("database", "")
        dbuser = self.config.get("username", "")
        dbpass = self.config.get("password", "")

        pool_name = f"pool_{dbname}"
        pool_size = self.config.get("pool_size", 10)

        if pool_name not in CONNECTION_POOLS:
            CONNECTION_POOLS[pool_name] = mariadb.ConnectionPool(
                host=dbhost,
                database=dbname,
                port=dbport,
                user=dbuser,
                password=dbpass,
                autocommit=False,
                pool_name=pool_name,
                pool_size=pool_size,
                pool_validation_interval=300,
            )

        pool = CONNECTION_POOLS[pool_name]

        try:
            conn = pool.get_connection()
        except:
            # no connection in pool available
            conn = mariadb.connect(host=dbhost, database=dbname, user=dbuser, password=dbpass, autocommit=False)

        # conn.character_set = 'utf8mb4'

        self.conn = conn
        if conn:
            self.csr = self.conn.cursor()
        else:
            self.logger.error(f"failed to connect to {dbhost} - {dbname}")
            raise mariadb.DatabaseError(f"failed to connect to database")

    def execute(self, sql: str | Query, *params):
        if isinstance(sql, Query):
            sql = str(sql)

        self.csr.execute(sql, params)

    def commit(self):
        self.conn.commit()

    def get_num_rows(self):
        return self.csr.rowcount

    def get_affected_rows(self):
        return self.csr.affected_rows

    def get_last_insert_id(self):
        return int(self.csr.lastrowid) if self.csr.lastrowid else 0

    def get_table_columns(self, table):
        self.execute("SHOW FULL COLUMNS FROM %s" % table)
        fields = self.fetch_all()

        result = {}
        for field in fields:
            result[field["Field"]] = re.sub(r"[(0-9)]", "", field["Type"])

        return result

    def fetch_all(self):
        results = []
        columns = [column[0] for column in self.csr.description]
        for row in self.csr.fetchall():
            x = dict(zip(columns, row))
            results.append(x)

        return results

    def fetch_column(self, field):
        results = self.fetch_all()
        return [r[field] for r in results]

    def fetch_one(self):
        row = self.csr.fetchone()
        if row:
            columns = [column[0] for column in self.csr.description]
            result = {}

            for value, index in enumerate(row):
                result[columns[value]] = index

            return result

        return None

    def fetch_result(self):
        row = self.csr.fetchone()
        if row:
            return row[0]

        return None

    def insert_object(self, table, item, replace=False):
        fields = []
        values = []

        for k, v in item.items():
            if v is None:
                continue

            if isinstance(v, (list, dict, tuple)):
                v = json.dumps(v, default=str)

            if isinstance(v, datetime):
                v = v.strftime("%Y-%m-%d %H:%M:%S")

            if isinstance(v, date):
                v = v.strftime("%Y-%m-%d")

            # is Enum
            if hasattr(v, "value"):
                v = v.value

            if isinstance(v, bool):
                v = 1 if v else 0

            if k.startswith("_"):
                continue

            fields.append("`" + k + "`")
            values.append(self.q(v))

        cmd = "REPLACE" if replace else "INSERT"
        insert_sql = cmd + " INTO %s(%s) VALUES (%s)" % (table, ", ".join(fields), ", ".join(values))

        query = Query()
        query.Insert(table).Columns(fields).Values(", ".join(values))

        try:
            self.csr.execute(insert_sql)
        except mariadb.DatabaseError as err:
            self.logger.error("%s: %s" % (table, str(err)))
            self.conn.rollback()
            raise err
        else:
            self.conn.commit()
            return self.get_last_insert_id()

    def update_object(self, table, item: dict, key: list[str] | str, update_none=False):
        columns = self.get_table_columns(table)

        statement = "UPDATE %s SET %s WHERE %s"
        wheres = []
        fields = []

        if isinstance(key, str):
            key = [key]

        for k, v in item.items():
            if k not in columns.keys():
                continue

            if k.startswith("_"):
                continue

            if isinstance(v, (list, dict, tuple)):
                v = json.dumps(v, default=str)

            if isinstance(v, datetime):
                v = v.strftime("%Y-%m-%d %H:%M:%S")

            if isinstance(v, date):
                v = v.strftime("%Y-%m-%d")

            # is Enum
            if hasattr(v, "value"):
                v = v.value

            if isinstance(v, bool):
                v = 1 if v else 0

            if k in key:
                wheres.append(f"`{k}` = " + ("IS NULL" if v is None else self.q(v)))
                continue

            if v is None:
                if update_none:
                    val = "NULL"
                else:
                    continue

            else:
                val = self.q(v)

            fields.append(f"`{k}` = {val}")

        if not fields:
            return True

        sql = statement % (table, ", ".join(fields), " AND ".join(wheres))

        try:
            self.csr.execute(sql)
        except mariadb.DatabaseError as err:
            self.logger.error("%s: %s" % (table, str(err)))
            self.conn.rollback()
            raise err
        else:
            self.conn.commit()
            return True

    def q(self, content: any) -> str | list:
        if isinstance(content, list):
            return [self.csr._connection.escape_string(text) for text in content]

        if isinstance(content, (int, float)):
            content = str(content)

        return "'" + self.csr._connection.escape_string(content) + "'"

    def close(self):
        try:
            if self.csr:
                self.csr.close()
            if self.conn:
                self.conn.close()
        except mariadb.ProgrammingError as err:
            self.logger.debug(str(err))

    def __del__(self):
        self.close()


def get_dbo() -> Database:
    return Database()
