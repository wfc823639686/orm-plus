import orm


class User(orm.Model):
    us_id = orm.IntegerField('id', primary=True)
    us_name = orm.StringField('name', notnull=False)


u = User(id=1, name='wfc')
# print(u.get_all_fields())
# u.get_by_id(2)

ew = orm.EntityWrapper()
ew.eq('name', 'wfc').ne('sex', '1').inside('aa', 1, 2)\
    .other().eq('name', 'aaa').ne('sex', '0').like_left('hh', 11)
# print(ew.get_where_sql())
u.select(ew)