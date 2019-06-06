import orm


class User(orm.Model):
    us_id = orm.IntegerField('id', primary=True)
    us_name = orm.StringField('name', notnull=False)


u = User(id=1, name='wfc')
u.remove_by_id()