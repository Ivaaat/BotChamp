filename = 'MyBase.txt'

class MyBaseDB:

    def create(self, msg, id_name):
        name_vpn = {
                    "Number": str(wda()) + ')',
                    "Name": msg,
                    "Id": id_name

        }
        userlist = ""
        for value in name_vpn.values():
            userlist += f'  {value}'
        with open(filename, "a", encoding='utf-8') as file:
            file.write(f'{userlist.lstrip()}\n')

    def update(self, num):
        with open(filename, "r", encoding='utf-8') as file:
            lines = file.readlines()
        del lines[num]
        with open(filename, "w", encoding='utf-8') as file:
            file.writelines(lines)
        with open(filename, "r", encoding='utf-8') as file:
            contents = file.readlines()
        i = 0
        while i < (wda() - num):
            contents[num + i] = contents[num + i].replace(
                f'{str(num + 1 + i)}', f'{str(num + i)}')
            i += 1
        with open(filename, "w", encoding='utf-8') as file:
            file.writelines(contents)

    def open(self):
        with open(filename, "r", encoding='utf-8') as file:
            content = file.read()
        #print(content)
        return content

def wda():
    with open(filename, "r", encoding='utf-8') as file:
        j = sum(1 for _ in file)
    return j
