import time

import pymysql


def get_repo_insert_db():
    return 'down_dep'


def get_db_insert():
    host = '47.88.48.19'
    user = 'root'
    password = 'Ella1996'
    db_name = 'hero-tool'
    return host, user, password, db_name


def get_dr_from_db(repo_name):
    (host, user, password, db_name) = get_db_insert()
    insert_db = get_repo_insert_db()
    sql = "SELECT d_repo,d_mod FROM " + insert_db
    sql = sql + " WHERE u_repo='%s'" % repo_name
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            data_list = []
            for r in check_result:
                if [r[0], r[1]] not in data_list:
                    data_list.append([r[0], r[1]])
            return 1, data_list
        else:
            return 0, []
    except Exception as exp:
        print("check repos dep ", repo_name, " from ", insert_db, " error:", exp)
        return -1, []


def get_dm_dr_from_db(repo_name, d_mod):
    (host, user, password, db_name) = get_db_insert()
    insert_db = get_repo_insert_db()
    sql = "SELECT d_repo FROM " + insert_db
    sql = sql + " WHERE u_repo='%s' AND d_mod='%d'" % (repo_name, d_mod)
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            data_list = []
            for r in check_result:
                if r[0] not in data_list:
                    data_list.append(r[0])
            return data_list
        else:
            return []
    except Exception as exp:
        print("check repos dep ", repo_name, " from ", insert_db, " error:", exp)
        return []


class DownDep:
    search_e = 0
    insert_e = 0
    insert_s = 0
    update_e = 0
    update_s = 0

    def __init__(self, d_repo, d_mod, u_repo):
        self.d_repo = d_repo
        self.d_mod = d_mod
        self.u_repo = u_repo
        # id_time = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        self.id = self.d_repo + '=' + self.u_repo
        self.insert_repo()

    def check_repo_db(self):
        (host, user, password, db_name) = get_db_insert()
        insert_db = get_repo_insert_db()
        sql = "SELECT count(*) FROM " + insert_db
        sql = sql + " WHERE d_repo='%s' AND u_repo='%s'" % (self.d_repo, self.u_repo)
        try:
            # 执行sql语句
            db_check = pymysql.connect(host, user, password, db_name)
            check_cursor = db_check.cursor()
            check_cursor.execute(sql)
            check_result = check_cursor.fetchone()
            check_cursor.close()
            db_check.close()
            if check_result:
                return check_result[0]
            else:
                return 0
        except Exception as exp:
            self.search_e = self.search_e + 1
            print("check repos dep ", self.d_repo, self.u_repo, " from ", insert_db, " error:", exp)
            return -1

    def insert_repo(self):
        (host, user, password, db_name) = get_db_insert()
        insert_db = get_repo_insert_db()
        check_result = self.check_repo_db()
        sql = ''
        if check_result < 1:
            insert_sql = "INSERT INTO " + insert_db
            insert_sql = insert_sql + " (id,d_repo,d_mod,u_repo) VALUES ('%s','%s','%d'," \
                                      "'%s')" % (self.id, self.d_repo, self.d_mod, self.u_repo)
            db = pymysql.connect(host, user, password, db_name)
            # print(insert_sql)
            sql = insert_sql
            try:
                insert_cursor = db.cursor()
                # 执行sql语句
                insert_cursor.execute(insert_sql)
                db.commit()
                insert_cursor.close()
                print('-------------insert ', insert_db, ' successful', self.d_repo, '==', self.u_repo)
            except Exception as exp:
                print('-------------insert ', insert_db, ' error exception is:', exp)
                print('-------------insert ', insert_db, ' error sql:', insert_sql)
                self.insert_e = self.insert_e + 1
                # 发生错误时回滚
                db.rollback()
            db.close()
