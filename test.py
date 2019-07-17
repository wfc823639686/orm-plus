import orm
import json
import json_encoder as je

orm.connect('127.0.0.1', 3306, 'root', '123456', 'test')


class User(orm.Model):
    table_name = 't_user'
    us_id = orm.IntegerField('id', primary=True)
    us_name = orm.StringField('name', notnull=False)


# u = User(id=1, name='wfc')
# print(u.get_all_fields())
# u.get_by_id(2)

# ew = orm.EntityWrapper()
# ew.eq('name', 'wfc').ne('sex', '1').inside('status', 1, 2)\
#     .other().eq('name', 'aaa').ne('sex', '0').like_left('email', '8236')
# ew.like_left('email', '82')
# print(ew.get_where_sql())
# r = u.select(ew, pi=1)
# print(str(r))

# sql = """select * from sys_user
#     where 1=1
#     {and name = #name#
#         and email like #email#
#     }
#     {and user_id = #id#}"""
# (?<=#)(\S+)(?=#)
# matchObj = re.match(r'[(](.*?)[)]', "select aa from (sys_user)")

# r = orm.select_list(sql, {'name': None, 'id': 0, 'email': 'sfd%'}, ["ps['name'] != None", "ps['id'] != 0"])
# print(r)
#
# sql1 = """select RD_Date `date`, SUM(RD_Flow) flow
#                 from T_TJ_FlowRealTime_Day
#                 where RD_DataSource=#dataSource# AND RD_ObjType=#objType#
#                 { and RD_FJNM like concat(#fjnm#,'____')}
#                 { and RD_Date >= #startDate#}
#                 { and RD_Date <= #endDate#}
#                 group by RD_Date
#                 order by RD_Date"""
#
# params = {
#     'dataSource': '04',
#     'objType': '02',
#     'fjnm': '0000',
#     'startDate': None,
#     'endDate': None
# }
# cdt = ["ps['fjnm'].__len__() > 10", "ps['startDate'] != None", "ps['endDate'] != None"]
# r1 = orm.select_list(sql1, params, cdt, cl=User, pi=2)
# print(r1)
# print(json.dumps(r1, cls=je.JsonEncoder))
#
# sql = """
#         select * from t_user
#         where 1=1
#         {and us_name = #name#}
#     """
# r = orm.select_list(sql, {'name': None}, ["ps['name'] != None"], cl=User)
# print(r)

# r = User.select_by_id(2)
# print(r)
ew = orm.EntityWrapper()
ew.eq('us_name', 'wfc')
r = User.select(ew, pi=1, size=10)
print(r)