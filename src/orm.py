import pymysql
import re

db = None


def connect(host, port, user, psw, db_name):
    global db
    db = pymysql.connect(host=host, port=port, user=user, password=psw,database=db_name)


def query_one(sql):
    cursor = db.cursor()
    cursor.execute(sql)
    return cursor.fetchone()


def query_list(sql):
    cursor = db.cursor()
    cursor.execute(sql)
    return cursor.fetchall()


def query_count(sql):
    cursor = db.cursor()
    cursor.execute(sql)
    return cursor.fetchone()[0]


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
        table_name = name
        mappings = dict()
        name_mappings = dict()
        primary = None
        for k, v in attrs.items():
            if k == 'table_name':
                table_name = v
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
        attrs['__table__'] = table_name
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

    def get_params(self, is_all=True):
        fields = []
        params = []
        args = []
        for k, v in self.__mappings__.items():
            arg = getattr(self, self.__name_mappings__[k], None)
            if not is_all and arg is not None:
                fields.append(k)
                params.append('?')
                args.append(arg)
            else:
                fields.append(k)
                params.append('?')
                args.append(arg)
        return fields, params, args

    def name_mappings(self, n):
        return self.__name_mappings__[n]

    def insert(self):
        fields, params, args = self.get_params()
        sql = 'insert into {} ({}) values ({})'.format(self.__table__, ','.join(fields), ','.join(params))
        print('SQL: {}'.format(sql))
        print('ARGS: {}'.format(str(args)))

    def update_by_id(self):
        fields, params, args = self.get_params(False)
        sql = 'update {} set {} where {} = {}'\
            .format(self.__table__, ','.join(map(lambda x: x + '=?', fields)), self.__primary__,
                    getattr(self, self.name_mappings(self.__primary__), None))
        print('SQL: {}'.format(sql))
        print('ARGS: {}'.format(str(args)))

    def delete_by_id(self):
        sql = 'delete from {} where {} = {}'\
            .format(self.__table__, self.__primary__, getattr(self, self.name_mappings(self.__primary__), None))
        print('SQL: {}'.format(sql))

    def _get_all_fields(self):
        r = ['{} AS `{}`'.format(self.__primary__, self.name_mappings(self.__primary__))]
        for n in self.__mappings__:
            r.append('{} AS `{}`'.format(n, self.__name_mappings__[n]))
        return ','.join(r)

    def select_by_id(self, id):
        sql = 'select {} from {} where {} = {}'.format(self._get_all_fields(), self.__table__, self.__primary__, id)
        print('SQL: {}'.format(sql))

    def select(self, ew, pi=0, size=10):
        if pi != 0:
            count_sql = 'select count(0) from {} where {}'.format(self.__table__, ew.get_where_sql())
            cr = query_one(count_sql)
            if cr != 0:
                if pi == 1:
                    limit = '{}'.format(size)
                else:
                    limit = '{}, {}'.format((pi - 1) * size, size)
                sql = 'select {} from {} where {} limit {}'\
                    .format(self._get_all_fields(), self.__table__, ew.get_where_sql(), limit)
                print('SQL: {}'.format(sql))
                return query_list(sql)
        else:
            sql = 'select {} from {} where {}' \
                .format(self._get_all_fields(), self.__table__, ew.get_where_sql())
            print('SQL: {}'.format(sql))
            return query_list(sql)


def to_str(x):
    if not isinstance(x, str):
        return str(x)
    else:
        return x


class EntityWrapper(object):

    def __init__(self):
        self.ors = [[]]
        self.index = 0

    def eq(self, n, v):
        self.ors[self.index].append("{} = '{}'".format(n, v))
        return self

    def ne(self, n, v):
        self.ors[self.index].append("{} != '{}'".format(n, v))
        return self

    def like_left(self, n, v):
        self.ors[self.index].append("{} like '{}%'".format(n, v))
        return self

    def like_right(self, n, v):
        self.ors[self.index].append("{} like '%{}'".format(n, v))
        return self

    def inside(self, n, *args):
        self.ors[self.index].append("{} in ({})".format(n, ','.join(map(to_str, args))))
        return self

    def not_inside(self, n, *args):
        self.ors[self.index].append("{} not in ({})".format(n, ','.join(map(to_str, args))))
        return self

    def other(self):
        self.ors.append([])
        self.index = self.index + 1
        return self

    def get_where_sql(self):
        r = []
        for a in self.ors:
            r.append('(' + ' and '.join(a) + ')')
        if r.__len__() == 1:
            return r.__getitem__(0)
        return ' or '.join(r)


def get_dynamic_sql(s):
    p1 = re.compile(r'[{](.*?)[}]', re.S)
    return re.findall(p1, s)


def get_params(s):
    p1 = re.compile(r'[#](.*?)[#]', re.S)
    return re.findall(p1, s)


def rep_param(s, n, v):
    f = '#{}#'.format(n)
    return s.replace(f, "'{}'".format(str(v)))


def select_list(sql, ps, cdt):
    ds = get_dynamic_sql(sql)
    if ds.__len__() != cdt.__len__():
        assert AttributeError('condition is error')
    for i, v in enumerate(ds):
        if eval(cdt[i]):
            s = ds[i]
            params = get_params(s)
            for p in params:
                s = rep_param(s, p, ps[p])
            print(s)
            sql = sql.replace(ds[i], s)
        else:
            sql = sql.replace(ds[i], '')
    print('src:' + sql)
    sql = sql.replace('{', '').replace('}', '')
    print('final: ' + sql)
