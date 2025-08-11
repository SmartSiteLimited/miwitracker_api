import copy


class QueryElement:
    def __init__(self, name: str, elements: str | list, glue: str = ','):
        self.elements: list[str] = []
        self.name = name
        self.glue = glue

        self.append(elements)

    def append(self, elements: str | list[str]):
        if isinstance(elements, list):
            self.elements.extend(elements)
        else:
            self.elements.append(elements)

    def __str__(self) -> str:
        if self.name[-2:] == '()':
            return f"{self.name[:-2]}({self.glue.join(map(str, self.elements))})\n"
        else:
            return f"{self.name} {self.glue.join(map(str, self.elements))}\n"

    def __deepcopy__(self, memo):
        clone = type(self)(self.name, self.elements, self.glue)

        for k, v in self.__dict__.items():
            if hasattr(v, '__class__') and issubclass(v.__class__, object):
                clone.__dict__[k] = copy.deepcopy(v)
            elif isinstance(v, list):
                clone.__dict__[k] = [copy.deepcopy(element) for element in v]
            else:
                setattr(clone, k, copy.deepcopy(v))

        return clone


class Query:
    def __init__(self):
        self.type = None

        self._select = None
        self._alias = None
        self._from = None
        self._where = None
        self._group = None
        self._having = None
        self._join = []
        self._order = None
        self._limit = 0
        self._offset = 0

        self._insert = None
        self._values = None
        self._set = None
        self._columns = None
        self._delete = None

        self._update = None

        self.auto_increment_field = False

    def Select(self, columns: str | list[str]) -> 'Query':
        self.type = 'select'

        if self._select:
            self._select.append(columns)
        else:
            self._select = QueryElement('SELECT', columns)

        return self

    def From(self, table: str, alias: str | None = None) -> 'Query':
        if alias:
            table += f' AS {alias}'

        if self._from:
            self._from.append(table)
        else:
            self._from = QueryElement('FROM', table)

        return self

    def Where(self, conditions, glue='AND') -> 'Query':
        if self._where:
            self._where.append(conditions)
        else:
            glue = glue.upper()
            self._where = QueryElement('WHERE', conditions, f" {glue} ")

        return self

    def WhereIn(self, key: str, key_values: list[int] | list[str]) -> 'Query':
        if type(key_values[0]) == int:
            key_values = [str(x) for x in key_values]
            self.Where(f'{key} IN ({",".join(key_values)})')
        else:
            self.Where(f'{key} IN ({",".join([str(x) for x in key_values])})')

        return self

    def Group(self, columns: str | list[str]) -> 'Query':
        if self._group:
            self._group.append(columns)
        else:
            self._group = QueryElement('GROUP BY', columns)

        return self

    def Having(self, conditions: list[str] | str, glue='AND') -> 'Query':
        if self._having:
            self._having.append(conditions)
        else:
            glue = glue.upper()
            self._having = QueryElement('HAVING', conditions, f" {glue} ")

        return self

    def Join(self, join_type: str, table: str, condition: str | None = None) -> 'Query':
        join_type = join_type.upper() + ' JOIN'

        if condition:
            self._join.append(QueryElement(join_type, [table, condition], ' ON '))
        else:
            self._join.append(QueryElement(join_type, table))

        return self

    def Order(self, columns: str | list[str]) -> 'Query':
        if self._order:
            self._order.append(columns)
        else:
            self._order = QueryElement('ORDER BY', columns)

        return self

    def Insert(self, table: str, increment_field=False) -> 'Query':
        self.type = 'insert'
        self._insert = QueryElement('INSERT INTO', table)
        self.auto_increment_field = increment_field

        return self

    def Values(self, values: list | str) -> 'Query':
        if self._values:
            self._values.append(values)
        else:
            self._values = QueryElement('()', values, '),(')

        return self

    def Columns(self, columns: str | list[str]) -> 'Query':
        if self._columns:
            self._columns.append(columns)
        else:
            self._columns = QueryElement('()', columns)

        return self

    def Update(self, table: str) -> 'Query':
        self.type = 'update'
        self._update = QueryElement('UPDATE', table)

        return self

    def Set(self, conditions: list[str] | str, glue=',') -> 'Query':
        if self._set:
            self._set.append(conditions)
        else:
            glue = glue.upper()
            self._set = QueryElement('SET', conditions, f" {glue} ")

        return self

    def Alias(self, alias: str) -> 'Query':
        self._alias = alias
        return self

    def Limit(self, limit=0, offset=0) -> 'Query':
        self._limit = limit
        self._offset = offset
        return self

    def Delete(self, table: str) -> 'Query':
        self.type = 'delete'
        self._delete = QueryElement('DELETE', "")
        self.From(table)

        return self

    def process_limit(self, query_str: str) -> str:
        if self._limit and self._offset:
            query_str += ' LIMIT ' + str(self._offset) + ', ' + str(self._limit)
        elif self._limit:
            query_str += ' LIMIT ' + str(self._limit)

        return query_str

    def clear(self, clause: str | None = None) -> 'Query':
        match clause:
            case 'alias':
                self._alias = None
            case 'select':
                self._select = None
                self.type = None
            case 'delete':
                self._delete = None
                self.type = None
            case 'update':
                self._update = None
                self.type = None
            case 'insert':
                self._insert = None
                self.type = None
            case 'from':
                self._from = None
            case 'join':
                self._join = []
            case 'set':
                self._set = None
            case 'where':
                self._where = None
            case 'group':
                self._group = None
            case 'having':
                self._having = None
            case 'order':
                self._order = None
            case 'columns':
                self._columns = None
            case 'values':
                self._values = None
            case 'limit':
                self._limit = 0
            case 'offset':
                self._offset = 0
            case _:
                self.type = None

                self._select = None
                self._alias = None
                self._from = None
                self._where = None
                self._group = None
                self._having = None
                self._join = []
                self._order = None
                self._limit = 0
                self._offset = 0

                self._insert = None
                self._values = None
                self._set = None
                self._columns = None
                self._delete = None

                self._update = None

                self.auto_increment_field = False

        return self

    def __str__(self):
        query_str = ""

        match self.type:
            case 'select':
                query_str += str(self._select)
                query_str += str(self._from)

                if self._join:
                    for join in self._join:
                        query_str += str(join)

                if self._where:
                    query_str += str(self._where)

                if self._group:
                    query_str += str(self._group)

                if self._having:
                    query_str += str(self._having)

                if self._order:
                    query_str += str(self._order)

            case 'insert':
                query_str += str(self._insert)

                if self._set:
                    query_str += str(self._set)
                elif self._values:
                    if self._columns:
                        query_str += str(self._columns)

                    query_str += ' VALUES '
                    query_str += str(self._values)

            case 'update':
                query_str += str(self._update)

                if self._join:
                    for join in self._join:
                        query_str += str(join)

                if self._set:
                    query_str += str(self._set)

                if self._where:
                    query_str += str(self._where)

            case 'delete':
                query_str += str(self._delete)
                query_str += str(self._from)

                if self._join:
                    for join in self._join:
                        query_str += str(join)

                if self._where:
                    query_str += str(self._where)

        query_str = self.process_limit(query_str)

        if self.type == 'select' and self._alias:
            query_str = f"({query_str}) AS {self._alias}"

        return query_str

    def __deepcopy__(self, memo):
        clone = type(self)()

        for k, v in self.__dict__.items():
            if hasattr(v, '__class__') and issubclass(v.__class__, object):
                clone.__dict__[k] = copy.deepcopy(v)
            elif isinstance(v, list):
                clone.__dict__[k] = [copy.deepcopy(element) for element in v]
            else:
                setattr(clone, k, copy.deepcopy(v))

        return clone
