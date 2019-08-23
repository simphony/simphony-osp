# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.


class EqualsCondition():
    def __init__(self, column_name, value, datatype):
        self.column_name = column_name
        self.value = value
        self.datatype = datatype
