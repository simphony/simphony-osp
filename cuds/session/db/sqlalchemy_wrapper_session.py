# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import sqlalchemy
from cuds.session.db.conditions import (EqualsCondition,
                                        AndCondition)
from cuds.session.db.sql_wrapper_session import SqlWrapperSession
from cuds.generator.ontology_datatypes import convert_from


class SqlAlchemyWrapperSession(SqlWrapperSession):

    def __init__(self, url, **kwargs):
        super().__init__(engine=sqlalchemy.create_engine(url),
                         **kwargs)
        self._connection = self._engine.connect()
        self._transaction = None
        self._metadata = sqlalchemy.MetaData(self._connection)
        self._metadata.reflect(self._engine)

    def __str__(self):
        return "SqlAlchemy Wrapper with engine %s" % self._engine

    # OVERRIDE
    def close(self):
        self._connection.close()
        self._engine.dispose()

    # OVERRIDE
    def _init_transaction(self):
        self._transaction = self._connection.begin()

    # OVERRIDE
    def _rollback_transaction(self):
        self._transaction.rollback()
        self._transaction = None

    # OVERRIDE
    def _commit(self):
        self._transaction.commit()

    # OVERRIDE
    def _db_select(self, table_name, columns, condition, datatypes):
        condition = self._get_sqlalchemy_condition(condition)
        table = self._get_sqlalchemy_table(table_name)
        sqlalchemy_columns = [getattr(table.c, column) for column in columns]
        s = sqlalchemy.sql.select(sqlalchemy_columns).where(condition)
        c = self._connection.execute(s)
        return self._convert_values(c, columns, datatypes)

    # OVERRIDE
    def _db_create(self, table_name, columns, datatypes,
                   primary_key, foreign_key, index):
        if table_name in self._metadata.tables:
            return
        columns = [
            sqlalchemy.Column(
                c,
                self._to_sqlalchemy_datatype(datatypes[c]),
                *([sqlalchemy.ForeignKey(".".join(foreign_key[c]))]
                  if c in foreign_key else []),
                primary_key=c in primary_key,
                index=c in index)
            for c in columns]
        sqlalchemy.Table(table_name, self._metadata, *columns)
        self._metadata.create_all()

    # OVERRIDE
    def _db_insert(self, table_name, columns, values, datatypes):
        table = self._get_sqlalchemy_table(table_name)
        stmt = table.insert().values(**{
            column: convert_from(value, datatypes[column])
            for column, value in zip(columns, values)
        })
        self._connection.execute(stmt)

    # OVERRIDE
    def _db_update(self, table_name, columns, values, condition, datatypes):
        table = self._get_sqlalchemy_table(table_name)
        condition = self._get_sqlalchemy_condition(condition)
        stmt = table.update() \
            .where(condition) \
            .values(**{
                column: convert_from(value, datatypes[column])
                for column, value in zip(columns, values)
            })
        self._connection.execute(stmt)

    # OVERRIDE
    def _db_delete(self, table_name, condition):
        table = self._get_sqlalchemy_table(table_name)
        condition = self._get_sqlalchemy_condition(condition)
        stmt = table.delete() \
            .where(condition)
        self._connection.execute(stmt)

    # OVERRIDE
    def _get_table_names(self, prefix):
        return set(filter(lambda x: x.startswith(prefix),
                          self._metadata.tables.keys()))

    def _get_sqlalchemy_condition(self, condition):
        """Transform the given condition to a SqlAlchemy condition

        :param condition: The condition to transform
        :type condition: Union[AndCondition, EqualsCondition]
        :raises NotImplementedError: Unknown condition type.
        :return: SqlAlchemy condition.
        :rtype: expression
        """
        if condition is None:
            return True
        if isinstance(condition, EqualsCondition):
            value = convert_from(condition.value, condition.datatype)
            table = self._get_sqlalchemy_table(condition.table_name)
            column = getattr(table.c, condition.column_name)
            return column == value
        if isinstance(condition, AndCondition):
            return sqlalchemy.sql.and_(*[self._get_sqlalchemy_condition(c)
                                         for c in condition.conditions])
        raise NotImplementedError("Unsupported condition")

    def _to_sqlalchemy_datatype(self, cuds_datatype):
        """Convert the given Cuds datatype to a datatype of sqlalchemy.

        :param cuds_datatype: The given cuds_object datatype.
        :type cuds_datatype: str
        :raises NotImplementedError: Unsupported datatype given.
        :return: A sqlalchemy datatype.
        :rtype: str
        """
        if cuds_datatype == "UUID":
            return sqlalchemy.String(36)
        if cuds_datatype == "INT":
            return sqlalchemy.Integer
        if cuds_datatype == "BOOL":
            return sqlalchemy.Boolean
        if cuds_datatype == "FLOAT":
            return sqlalchemy.Float
        elif cuds_datatype.startswith("STRING") and ":" in cuds_datatype:
            return sqlalchemy.String(int(cuds_datatype.split(":")[1]))
        elif cuds_datatype.startswith("STRING"):
            return sqlalchemy.String()
        elif cuds_datatype.startswith("UNDEFINED"):
            return sqlalchemy.String()
        else:
            raise NotImplementedError("Unsupported data type!")

    def _get_sqlalchemy_table(self, table_name):
        """Get the sqlalchemy table, either from metadata or load it.

        :param table_name: The name of the table to get.
        :type table_name: str
        :return: The sqlalchemy table
        :rtype: Table
        """
        if table_name in self._metadata.tables:
            return self._metadata.tables[table_name]
        return sqlalchemy.Table(table_name,
                                self._metadata,
                                autoload=True,
                                autoload_with=self._connection)
