import orm
import re

orm.connect('117.50.68.68', 33306, 'developer', 'LYDsj!2019', 'smarttourismcloud_test')


class User(orm.Model):
    table_name = 'sys_user'
    user_id = orm.IntegerField('id', primary=True)
    name = orm.StringField('name', notnull=False)


u = User(id=1, name='wfc')
# print(u.get_all_fields())
# u.get_by_id(2)

ew = orm.EntityWrapper()
# ew.eq('name', 'wfc').ne('sex', '1').inside('status', 1, 2)\
#     .other().eq('name', 'aaa').ne('sex', '0').like_left('email', '8236')
ew.like_left('email', '82')
# print(ew.get_where_sql())
r = u.select(ew, pi=1)
# print(str(r))

sql = """select * from sys_user
    where 1=1
    {and name = #name#}
    and email like #email#
    {and user_id = #id#}"""
sql1 = """select * from sys_user"""
# (?<=#)(\S+)(?=#)
# matchObj = re.match(r'[(](.*?)[)]', "select aa from (sys_user)")

r = orm.select_list(sql, {'name': '王凤晨', 'id': 0, 'email': 'sfd%'}, ["ps['name'] != None", "ps['id'] != 0"])
print(r)