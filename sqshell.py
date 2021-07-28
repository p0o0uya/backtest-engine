import mysql.connector as msql

######################### CLASS #########################
class sqshell():

    HOST                = '54.37.199.113' #'127.0.0.1', 'localhost', '54.37.199.113'
    PORT                = '3306'
    USER                = 'telebot'
    PASS                = '4501210575Hk_21'
    DB                  = 'xenonvpn'
    TABLES              = []
    TABLES_INFO         = {}
    DEFAULT_TABLE_NAME  = 'userbase'
    
    def __init__(self):
        try:
            self.dbconn()
            print('connection successfull to the database')
        except Exception as Err:
            print(Err)
        self.getinfo()

    def dbconn(self):
        self.conn  = msql.connect(user=self.USER, password=self.PASS, host=self.HOST,
                        port=self.PORT, database=self.DB)    #auth_plugin='caching_sha2_password'
        self.cur   = self.conn.cursor()
        return

    def dbdiss(self):
        self.conn.disconnect()

    def getinfo(self):
        query = ("SHOW TABLES")
        self.cur.execute(query)
        ret = self.cur.fetchall()
        self.TABLES = [x[0] for x in ret]
        for table in self.TABLES:
            query = ("SHOW COLUMNS FROM `{}`;".format(table))
            self.cur.execute(query)
            ret = self.cur.fetchall()
            self.TABLES_INFO[table] = [x[0] for x in ret]
        return 

    def getrow(self, key, value, table:str=None):
        # the only parameter that is read from user is value, that is why we only use that in our injection prevention
        if not table:
            table = self.DEFAULT_TABLE_NAME
        query = ("SELECT * FROM `{}` WHERE BINARY `{}` = %(value)s;".format(table, key))
        self.cur.execute(query, {'value':value})
        ret = self.cur.fetchall()
        return list(ret[0]) if ret else None

    def getrows(self, key, value, table:str=None):
        # the only parameter that is read from user is value, that is why we only use that in our injection prevention
        if not table:
            table = self.DEFAULT_TABLE_NAME
        query = ("SELECT * FROM `{}` WHERE BINARY `{}` = %(value)s;".format(table, key))
        self.cur.execute(query, {'value':value})
        ret = self.cur.fetchall()
        return list(ret) if ret else None
    
    def getcol(self, col, table:str=None):
        if not table:
            table = self.DEFAULT_TABLE_NAME
        query = ("SELECT `{}` FROM `{}`;".format(col, table))
        try:
            self.cur.execute(query)
            ret = self.cur.fetchall()
            return [x[0] for x in ret]
        except Exception as Err:
            print("There is No Column called {}".format(col))
            return None

    def getcollike(self, col, liker, table:str=None):
        if not table:
            table = self.DEFAULT_TABLE_NAME
        query = ("SELECT `{}` FROM `{}` WHERE `{}` LIKE %(liker)s;".format(col, table, col))
        self.cur.execute(query, {'liker': liker})
        ret = self.cur.fetchall()
        return [x[0] for x in ret]

    def setrow(self, params, table:str=None):
        if not table:
            table = self.DEFAULT_TABLE_NAME
        keys = list(params.keys())
        values = []
        for key in keys:
            values.append(params[key])
        keys1 = ', '.join(keys)
        fromuser = "%(" + ")s, %(".join(keys) + ")s"
        query = ("INSERT INTO `{}` ({}) VALUES ({});".format(table, keys1, fromuser))
        try:
            self.cur.execute(query, params)
#            ret = self.cur.fetchall()
            return True
        except Exception as Err:
            print("Couldn't set row!")
            print(Err)
            return False

    def delrow(self, key, value, table:str=None):
        if not table:
            table = self.DEFAULT_TABLE_NAME
        query = ("DELETE FROM `{}` WHERE `{}` = %(value)s;".format(table, key))
        try:
            self.cur.execute(query, {'value': value})
#            ret = self.cur.fetchall()
            return True
        except Exception as Err:
            print("Couldn't delete row!")
            print(Err)
            return False

    def colupdate(self, colname, value, keycol, keycolval, table:str=None):
        if not table:
            table = self.DEFAULT_TABLE_NAME
        query = ("UPDATE `{}` SET `{}` = %(value)s WHERE `{}` = %(keycolval)s;".format(table, colname, keycol))
        try:
            self.cur.execute(query, {'value': value, 'keycolval': keycolval})
            # ret = self.cur.fetchall()
            return True
        except Exception as Err:
            print("Couldn't update entry!")
            print(Err)
            return False

    def colplus(self, colname, val, keycol, keycolval, table:str=None):
        if not table:
            table = self.DEFAULT_TABLE_NAME
        value = abs(val)
        sgn   = value/val
        sgn   = '+' if sgn > 0 else '-'
        query = ("UPDATE `{}` SET `{}` = `{}` {} %(value)s WHERE `{}` = %(keycolval)s;".format(table, colname, colname, sgn, keycol))
        try:
            self.cur.execute(query, {'value': value, 'keycolval': keycolval})
#            ret = self.cur.fetchall()
            return True
        except Exception as Err:
            print("Couldn't update entry!")
            print(Err)
            return False

    def colpluss(self, colname, val, keycol, keycolvals, table:str=None):
        if not table:
            table = self.DEFAULT_TABLE_NAME
        value = abs(val)
        sgn   = value/val
        sgn   = '+' if sgn > 0 else '-'
        if len(keycolvals)==1:
            keycolvals = f'{keycolvals[0]}'
            query = (f"UPDATE `{table}` SET `{colname}` = `{colname}` {sgn} %(value)s WHERE `{keycol}` = '{keycolvals}';")
        else:
            query = (f"UPDATE `{table}` SET `{colname}` = `{colname}` {sgn} %(value)s WHERE `{keycol}` IN {keycolvals};")
        
        try:
            self.cur.execute(query, {'value': value})
            return True
        except Exception as Err:
            print("Couldn't update entries!")
            print(Err)
            return False

    def getcolsum(self, table, username):
        try:
            query = ("""SELECT CONCAT('SELECT ', '`', group_concat(`COLUMN_NAME` SEPARATOR '`+`'), '`', ' FROM {}') 
                        FROM  `INFORMATION_SCHEMA`.`COLUMNS` 
                        WHERE `TABLE_SCHEMA` = (select database()) 
                        AND   `TABLE_NAME`   = '{}'
                        AND   `COLUMN_NAME`  <> 'username';""".format(table, table))
            self.cur.execute(query)
            newquery = (self.cur.fetchall()[0][0] + " WHERE username = %(username)s;")
            self.cur.execute(newquery, {'username': username})
            ret = self.cur.fetchall()
            return ret
        except Exception as Err:
            print("Couldn't sum Columns!")
            print(Err)
            return False

    def getoldrows(self, key1, key2, tcol, tm, table:str=None):
        # the only parameter that is read from user is value, that is why we only use that in our injection prevention
        if not table:
            table = self.DEFAULT_TABLE_NAME
        query = (f"SELECT `{key1}`, `{key2}` FROM `{table}` "
                 f"WHERE DATE_ADD(`{tcol}`, INTERVAL {tm} MINUTE) < NOW();")
        self.cur.execute(query)
        ret = self.cur.fetchall()
        return list(ret) if ret else None

    def delrows(self, key, rows, table:str=None):
        if not table:
            table = self.DEFAULT_TABLE_NAME
        if len(rows)==1:
            rows = f'{rows[0]}'
            query = (f"DELETE FROM `{table}` "
                     f"WHERE `{key}`='{rows}';")
        else:
            query = (f"DELETE FROM `{table}` "
                     f"WHERE `{key}`IN {rows};")
        self.cur.execute(query)
        return True

    def countrows(self, key:str=None, value:str=None, table:str=None):
        if not table:
            table = self.DEFAULT_TABLE_NAME
        if key and value:
            query = (f"SELECT COUNT(*) FROM `{table}`"
                     f"WHERE `{key}`='{value}';")
        else:    
            query = (f"SELECT COUNT(*) FROM `{table}`;")
        self.cur.execute(query)
        return self.cur.fetchall()[0][0]

    def countyoungrows(self, key, time_given, table:str=None):
        if not table:
            table = self.DEFAULT_TABLE_NAME
        query = (f"SELECT COUNT(*) FROM `{table}`"
                 f"WHERE `{key}`>='{time_given}';")

        print(query)
        self.cur.execute(query)
        return self.cur.fetchall()[0][0]

if __name__ == "__main__":
    
    inst = sqshell()
    # print(inst.conn.is_connected())
    # inst.dbdiss()
    # print(inst.conn.is_connected())
    # print(inst.getrow('username', 'abs'))
    # print(inst.delrow('session_id', '4999b0dbbae4cc80b4abdea4d88a', table='syncer'))
    # print(inst.getcol('username', 'userbase'))
    # print(inst.getcollike('username', 'user%', 'userbase'))
    # params = {  'session_id': 'ghasem',
    #             'username': 'abs',
    #             'nasip': '127.0.0.1',
    #             'service': 'ocserv',
    #             'last_alive': '2021-01-30 00:06:00'}
    # params = {  'username': 'khanadmin',
    #             'password': 'JjvHtKxG',
    #             'access': 2,
    #             'active': 0,
    #             'adminer': 'absmaster'}

    # inst.setrow(params, table='userbase')
    print(inst.colupdate('logged', 0, 'username', 'user211'))
    # inst.colupdate('exptime', "2021-08-12", 'username', 'user177')
    # print(inst.colplus('nlogs', 1, 'username', 'abs'))
    # ret = inst.getcolsum('syncer', 'nabi')
    # print(ret)
    # print(inst.TABLES_INFO['userbase'])
    # ret = inst.getoldrows('session_id', 'username', 'last_alive', 3, table='syncer')
    # print(ret)
    # session_ids = tuple()
    # usernames = tuple()
    # for item in ret:
    #     session_ids += (item[0],)
    #     usernames   += (item[1],)

    # print(session_ids)
    # ret = inst.delrows('session_id', session_ids, table='syncer')
    # print(usernames)
    # ret = inst.colpluss('logged', -1, 'username', usernames, table='userbase')
    # print(inst.getcollike('username', 'user%', table='userbase'))
    # print(inst.countrows('service', 'openvpn_GE001', table = 'syncer'))
    # print(inst.countrows('userbase'))
    # print(inst.countyoungrows('last_activity', '2020-09-02 00:00:00 ', table='userbase'))