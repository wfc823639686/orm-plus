import functools


class Field(object):

    def __int__(self, name, column_type, primary=False, notnull=True):
        self.name = name
        self.column_type = column_type
        self.primary = primary
        self.notnull = notnull

    def __str__(self):
        return '<%s:%s>' % (self.__class__.__name__, self.name)


class StringField(Field):

    def __init__(self, name, primary=False, notnull=False):
        super(StringField, self).__int__(name, 'varchar(100)', primary, notnull)


class IntegerField(Field):

    def __init__(self, name, primary=False, notnull=False):
        super(IntegerField, self).__int__(name, 'bigint', primary, notnull)


class ModelMetaclass(type):

    def __new__(cls, name, bases, attrs):
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        print('Found model: %s' % name)
        mappings = dict()
        name_mappings = dict()
        primary = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                # 别名映射处理
                print('name %s as %s' % (k, v.name))
                name_mappings[k] = v.name
                print('Found mappings %s ==> %s' % (k, v))
                if v.primary:
                    primary = k
                else:
                    mappings[k] = v
        for k in mappings.keys():
            attrs.pop(k)
        attrs.pop(primary)
        attrs['__mappings__'] = mappings
        attrs['__name_mappings__'] = name_mappings
        attrs['__table__'] = name
        attrs['__primary__'] = primary
        return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModelMetaclass):

    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def get_params(self, all = True):
        fields = []
        params = []
        args = []
        for k, v in self.__mappings__.items():
            arg = getattr(self, self.__name_mappings__[k], None)
            if not all and arg is not None:
                fields.append(k)
                params.append('?')
                args.append(arg)
            else:
                fields.append(k)
                params.append('?')
                args.append(arg)
        return fields, params, args

    def save(self):
        fields, params, args = self.get_params()
        sql = 'insert into %s (%s) values (%s)' % (self.__table__, ','.join(fields), ','.join(params))
        print('SQL: %s' % sql)
        print('ARGS: %s' % str(args))

    def update_by_id(self):
        fields, params, args = self.get_params(False)
        sql = 'update %s set %s where %s = %s' % (self.__table__, ','.join(map(lambda x: x + '=?', fields)), self.__primary__, getattr(self, self.__name_mappings__[self.__primary__], None))
        print('SQL: %s' % sql)
        print('ARGS: %s' % str(args))

    def remove_by_id(self):
        sql = 'delete from %s where %s = %s' % (self.__table__, self.__primary__, getattr(self, self.__name_mappings__[self.__primary__], None))
        print('SQL: %s' % sql)

