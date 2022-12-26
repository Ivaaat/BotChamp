

class MyBaseDB:
    def __init__(self,filename = 'MyBase', one_column = "Number", two_column = 'Name', three_column = 'Id'):
    #def __init__(self,filename = 'MyBase', one_column = "Имя", two_column = 'Name', three_column = 'id'):
        self.filename = f"{filename}.txt"
        self.one_column = one_column
        self.two_column = two_column
        self.three_column = three_column
        try:
            with open(self.filename, "r", encoding='utf-8') as file:
                self.num_line = str(sum(1 for _ in file)) + ")"
        except OSError:
            with open(self.filename, "a", encoding='utf-8') as file:
                userlist = '{}     {}       {}'.format(one_column, two_column, three_column)
                file.write(f'{userlist}\n')


    def create(self, name, id_name, unique_strings = False):
        with open(self.filename, "r", encoding='utf-8') as file:
                self.num_line = sum(1 for _ in file)
        name_vpn = {
                    self.one_column: str(self.num_line) + ')',
                    self.two_column: name,
                    self.three_column: id_name

        }
        with open(self.filename, "r", encoding='utf-8') as file:
                lines = file.readlines()  
                separator1 =  (lines[0].find(self.two_column) - 2) * " "
                separator2 =  (lines[0].find(self.three_column) - (lines[0].find(self.two_column)) - len(name_vpn[self.two_column])) * " "
        userlist = '{}{}{}{}{}\n'.format(name_vpn[self.one_column], separator1,
                                        name_vpn[self.two_column], separator2,
                                        name_vpn[self.three_column])
                                
        if unique_strings:
                for i in range(1,len(lines)):
                    if str(name_vpn[self.three_column]) in lines[i]:
                        msg = '\n[INFO] Такой пользователь уже существует\n'
                        print(msg)
                        return msg
        with open(self.filename, "a", encoding='utf-8') as file:
            file.write(f'{userlist}')

    def update(self, num):
        with open(self.filename, "r", encoding='utf-8') as file:
            self.num_line = sum(1 for _ in file)
            lines = file.readlines()
        del lines[num]
        with open(self.filename, "w", encoding='utf-8') as file:
            file.writelines(lines)
        with open(self.filename, "r", encoding='utf-8') as file:
            contents = file.readlines()
        i = 0
        while i < (self.num_line - num):
            contents[num + i] = contents[num + i].replace(
                f'{str(num + 1 + i)}', f'{str(num + i)}')
            i += 1
        with open(self.filename, "w", encoding='utf-8') as file:
            file.writelines(contents)

    def open(self):
        with open(self.filename, "r", encoding='utf-8') as file:
            content = file.read()
        return content


# base = MyBaseDB()
# base.create('Александр', 123123, unique_strings = True)
# base.create('Иван', 323312, unique_strings = True)
# base.create('Александр', 123123, unique_strings = True)
# base.create('Иван', 323312, unique_strings = True)
