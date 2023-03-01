from pymongo import MongoClient

client = MongoClient()
db = client['users-table']
users_col = db['users']


def add_user(employee_name, id, push = False):
    users = {"_id": str(id),
            "Name" : employee_name,
            "Push": push
                }
    try:
        users_col.insert_one(users)
        return True
    except Exception():
        return False

def get_list_user():
    list_user = []
    for user_view in users_col.find():
        for key, value in user_view.items():
            if key == "_id":
                list_user.append(int(value))
    return list_user

def get_live():
    dict_live = {}
    list_live = []
    for live_view in users_col.find():
        try:
            
            for key, value in live_view['live'].items():
                if value:
                    list_live.append(key)
            dict_live[live_view['_id']] = list_live
        except KeyError:
            continue
    return dict_live
#get_live()



def view_users():
    user = ''
    for user_view in users_col.find():
        for key, value in user_view.items():
            user += f'{key}: {value}\n'
        user += '\n'
    return user

def set_push(id, bool_push):
    users_col.update_one({"_id": str(id)},{"$set":{"Push" : bool_push}})

def add_field(id, num_field, bool_push):
    users_col.update_one({"_id": str(id)},{"$set":{'live':{num_field:bool_push}}})


def delete_field(id, name_field):
    users_col.update_one({"_id": str(id)},  {"$unset": {f"{name_field}":1}})

def get_push(id, name_field = "") :
    push_dict = users_col.find_one({"_id": str(id)})
    try:
        if name_field != "":
            return push_dict[name_field]
        else:
            return push_dict['Push']
    except KeyError:
        return ""
        

def get_user(id) :
    user_dict = users_col.find_one({"_id": str(id)})
    if user_dict is None:
        return False
    else: 
        return True

