import json
from datetime import datetime
from datetime import date
from decimal import Decimal


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.__str__()
        if isinstance(obj, datetime):
            return obj.__str__()
        if isinstance(obj, Decimal):
            return obj.__str__()
        return json.JSONEncoder.default(self, obj)
