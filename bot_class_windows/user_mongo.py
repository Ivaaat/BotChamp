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


def view_users():
    user = ''
    for user_view in users_col.find():
        for key, value in user_view.items():
            user += f'{key}: {value}\n'
        user += '\n'
    return user


def get_push(id) :
    push_dict = users_col.find_one({"_id": str(id)})
    return push_dict['Push']

def get_user(id) :
    user_dict = users_col.find_one({"_id": str(id)})
    if user_dict is None:
        return False
    else: 
        return True

