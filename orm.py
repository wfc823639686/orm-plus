import pymysql
import re

db = None


def connect(host, port, user, psw, db_name):
    global db
    db = pymysql.connect(host=host, port=port, user=user, password=psw,
                         database=db_name, cursorclass=pymysql.cursors.DictCursor)


def query_one(sql):
    with db.cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchone()


def query_list(sql):
    with db.cursor() as cursor:
        cursor.execute(sql)
        return list(cursor.fetchall())


def upd(sql, args=None):
    if args is None:
        args = []
    with db.cursor() as cursor:
        cursor.execute(sql, args)
        db.commit()


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

    def __new__(mcs, name, bases, attrs):
        if name == 'Model':
            return type.__new__(mcs, name, bases, attrs)
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
        return type.__new__(mcs, name, bases, attrs)


class Model(dict, metaclass=ModelMetaclass):

    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def set_dict(self, d):
        for i in d.keys():
            self.setdefault(i, d[i])

    def mapping_dict(self, d):
        for i in d.keys():
            try:
                sr = self.name_mappings(i)
                self.setdefault(sr, d[i])
            except KeyError:
                pass

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
                params.append('%s')
                args.append(arg)
            else:
                fields.append(k)
                params.append('%s')
                args.append(arg)
        return fields, params, args

    @classmethod
    def name_mappings(cls, n):
        return cls.__name_mappings__[n]

    def insert(self):
        fields, params, args = self.get_params()
        sql = 'insert into {} ({}) values ({})'.format(self.__table__, ','.join(fields), ','.join(params))
        print('SQL: {}'.format(sql))
        print('ARGS: {}'.format(str(args)))
        upd(sql, args)

    def update_by_id(self):
        fields, params, args = self.get_params(False)
        sql = 'update {} set {} where {} = {}' \
            .format(self.__table__, ','.join(map(lambda x: x + '=%s', fields)), self.__primary__,
                    getattr(self, self.name_mappings(self.__primary__), None))
        print('SQL: {}'.format(sql))
        print('ARGS: {}'.format(str(args)))
        upd(sql, args)

    def delete_by_id(self):
        sql = 'delete from {} where {} = {}' \
            .format(self.__table__, self.__primary__, getattr(self, self.name_mappings(self.__primary__), None))
        print('SQL: {}'.format(sql))
        upd(sql)

    @classmethod
    def _get_all_fields(cls):
        r = ['{} AS `{}`'.format(cls.__primary__, cls.name_mappings(cls.__primary__))]
        for n in cls.__mappings__:
            r.append('{} AS `{}`'.format(n, cls.__name_mappings__[n]))
        return ','.join(r)

    @classmethod
    def select_by_id(cls, id):
        sql = 'select {} from {} where {} = {}'.format(cls._get_all_fields(), cls.__table__, cls.__primary__, id)
        print('SQL: {}'.format(sql))
        r = cls()
        r.set_dict(query_one(sql))
        return r

    @classmethod
    def wrapper(cls, rs):
        results = []
        for item in rs:
            r = cls()
            r.set_dict(item)
            results.append(r)
        return results

    @classmethod
    def select(cls, ew, pi=0, size=10):
        if pi != 0:
            count_sql = 'select count(0) from {} where {}'.format(cls.__table__, ew.get_where_sql())
            cr = query_one(count_sql)['count(0)']
            if cr != 0:
                if pi == 1:
                    limit = '{}'.format(size)
                else:
                    limit = '{}, {}'.format((pi - 1) * size, size)
                sql = 'select {} from {} where {} limit {}' \
                    .format(cls._get_all_fields(), cls.__table__, ew.get_where_sql(), limit)
                print('SQL: {}'.format(sql))
                r = cls.wrapper(query_list(sql))
                return Page(cr, r)
        else:
            sql = 'select {} from {} where {}' \
                .format(cls._get_all_fields(), cls.__table__, ew.get_where_sql())
            print('SQL: {}'.format(sql))
            return cls.wrapper(query_list(sql))


class Page(dict):

    def __init__(self, total, list, **kwargs):
        super().__init__(**kwargs)
        self.setdefault('total', total)
        self.setdefault('list', list)


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


def rep_params(s, ps):
    dps = get_params(s)
    for dp in dps:
        f = '#{}#'.format(dp)
        s = s.replace(f, "'{}'".format(str(ps[dp])))
    return s


def paging(sql, pi, size, cl=None):
    if re.search('group by', sql, re.IGNORECASE):
        count_sql = 'select count(0) from ({}) as count_num'.format(sql)
    else:
        count_sql = sql.replace('select .* from', sql, 1)
    if pi == 1:
        limit_str = ' limit {}'.format(size)
    else:
        limit_str = ' limit {}, {}'.format((pi - 1) * size, size)
    cr = query_one(count_sql)
    if cr and cr['count(0)'] != 0:
        r = query_list(sql + limit_str)
        if r and cl:
            return enc(r, cl)
        else:
            return r
    else:
        return None


def enc(r, cl):
    results = []
    for i in r:
        a = cl()
        a.mapping_dict(i)
        results.append(a)
    return results


def select_list(sql, ps, cdt, cl=None, pi=0, size=10):
    ds = get_dynamic_sql(sql)
    if ds.__len__() != cdt.__len__():
        raise AttributeError('condition is error')
    for i, v in enumerate(ds):
        try:
            if eval(cdt[i]):
                s = ds[i]
                sql = sql.replace(ds[i], s)
            else:
                sql = sql.replace(ds[i], '')
        except KeyError:
            sql = sql.replace(ds[i], '')
    print('src:' + sql)
    sql = sql.replace('{', '').replace('}', '')
    sql = rep_params(sql, ps)
    print('final: ' + sql)
    if pi == 0:
        r = query_list(sql)
        if r and cl:
            return enc(r, cl)
        else:
            return r
    else:
        return paging(sql, pi, size, cl)
