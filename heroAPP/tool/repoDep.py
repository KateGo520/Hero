import time

import pymysql

from . import repo
# import repo


def get_repo_insert_db():
    return 'repo_dep'


def get_dir_up_num_from_db(repo_name, repo_version, repo_hash):
    (host, user, password, db_name) = repo.get_db_insert()
    insert_db = get_repo_insert_db()
    sql = "SELECT count(*) FROM " + insert_db
    sql = sql + " WHERE d_repo='%s' AND (d_hash='%s' OR d_version='%s')" % (repo_name, repo_hash, repo_version)
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            return 1, check_result[0][0]
        else:
            return 0, 0
    except Exception as exp:
        print("check repos dep ", repo_name, repo_version, repo_hash, " from ", insert_db, " error:", exp)
        return -1, 0


def get_dir_up_from_db(repo_name, repo_version, repo_hash):
    (host, user, password, db_name) = repo.get_db_insert()
    insert_db = get_repo_insert_db()
    sql = "SELECT u_repo,u_mod,u_version,u_hash FROM " + insert_db
    sql = sql + " WHERE d_repo='%s' AND (d_hash='%s' OR d_version='%s')" % (repo_name, repo_hash, repo_version)
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
                if [r[0], r[1], r[2], r[3]] not in data_list:
                    data_list.append([r[0], r[1], r[2], r[3]])
            return 1, data_list
        else:
            return 0, []
    except Exception as exp:
        print("check repos dep ", repo_name, repo_version, repo_hash, " from ", insert_db, " error:", exp)
        return -1, []


def get_dep_msg_from_db(repo_name, repo_version, repo_hash):
    (host, user, password, db_name) = repo.get_db_insert()
    insert_db = get_repo_insert_db()
    sql = "SELECT d_repo,d_mod,d_version,d_hash,u_repo,u_mod,u_version,u_hash FROM " + insert_db
    sql = sql + " WHERE d_repo='%s' AND (d_hash='%s' OR d_version='%s')" % (repo_name, repo_hash, repo_version)
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            return 1, check_result
        else:
            return 0, []
    except Exception as exp:
        print("check repos dep ", repo_name, repo_version, repo_hash, " from ", insert_db, " error:", exp)
        return -1, []


def get_all_up_layer(repo_name, repo_version, repo_hash, all_up_list, layer):
    layer = layer - 1
    if repo_version:
        r_name = repo_name + '(' + repo_version + ')'
    else:
        r_name = repo_name + '(' + repo_hash + ')'
    if layer > 1:
        (r, up_list) = get_dep_msg_from_db(repo_name, repo_version, repo_hash)
        if r > 0:
            for up in up_list:
                if up[6]:
                    u_name = up[4] + '(' + up[6] + ')'
                else:
                    u_name = up[4] + '(' + up[7] + ')'
                dep_msg = [r_name, up[1], u_name, up[5]]
                if dep_msg not in all_up_list:
                    all_up_list.append(dep_msg)
            for up in up_list:
                l_n = layer
                (all_up_list, l_n) = get_all_up_layer(up[4], up[6], up[7], all_up_list, l_n)
    return all_up_list, layer


def get_all_up(repo_name, repo_version, repo_hash, all_up_list):
    layer = 4
    if repo_version:
        r_name = repo_name + '(' + repo_version + ')'
    else:
        r_name = repo_name + '(' + repo_hash + ')'
    # all_up_list = []
    (r, up_list) = get_dep_msg_from_db(repo_name, repo_version, repo_hash)
    for up in up_list:
        # d_repo,d_mod,d_version,d_hash,u_repo,u_mod,u_version,u_hash
        if up[6]:
            u_name = up[4] + '(' + up[6] + ')'
        else:
            u_name = up[4] + '(' + up[7] + ')'
        dep_msg = [r_name, up[1], u_name, up[5]]
        if dep_msg not in all_up_list:
            all_up_list.append(dep_msg)
    if r > 0:
        for up in up_list:
            l_n = layer
            (all_up_list, l_n) = get_all_up_layer(repo_name, repo_version, repo_hash, all_up_list, layer)
            # (r_2, up_list_2) = get_dep_msg_from_db(up[4], up[6], up[7])
            # for up_2 in up_list_2:
            #     dep_msg_2 = [up_2[0], up_2[1], up_2[4], up_2[5]]
            #     if dep_msg_2 not in all_up_list:
            #         all_up_list.append(dep_msg_2)

                    # all_up_list = get_all_up(repo_name, repo_version, repo_hash, all_up_list)
            # all_up_list = get_all_up(up[4], up[6], up[7], all_up_list)
    return all_up_list


def get_dep_down_msg_from_db(repo_name, repo_version, repo_hash):
    (host, user, password, db_name) = repo.get_db_insert()
    insert_db = get_repo_insert_db()
    sql = "SELECT d_repo,d_mod,d_version,d_hash,u_repo,u_mod,u_version,u_hash FROM " + insert_db
    sql = sql + " WHERE u_repo='%s' AND (u_hash='%s' OR u_version='%s')" % (repo_name, repo_hash, repo_version)
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            return 1, check_result
        else:
            return 0, []
    except Exception as exp:
        print("check repos dep ", repo_name, repo_version, repo_hash, " from ", insert_db, " error:", exp)
        return -1, []


def get_all_down_layer(repo_name, repo_version, repo_hash, all_down_list, layer):
    layer = layer - 1
    if repo_version:
        r_name = repo_name + '(' + repo_version + ')'
    else:
        r_name = repo_name + '(' + repo_hash + ')'
    if layer > 1:
        (r, down_list) = get_dep_down_msg_from_db(repo_name, repo_version, repo_hash)
        if r > 0:
            for d in down_list:
                if d[2]:
                    d_name = d[0] + '(' + d[2] + ')'
                else:
                    d_name = d[0] + '(' + d[3] + ')'
                dep_msg = [d_name, d[1], r_name, d[5]]
                if dep_msg not in all_down_list:
                    all_down_list.append(dep_msg)
            for d in down_list:
                l_n = layer
                (all_down_list, l_n) = get_all_down_layer(d[4], d[6], d[7], all_down_list, l_n)
    return all_down_list, layer


def get_all_down(repo_name, repo_version, repo_hash, all_down_list):
    layer = 3
    if repo_version:
        r_name = repo_name + '(' + repo_version + ')'
    else:
        r_name = repo_name + '(' + repo_hash + ')'
    # all_up_list = []
    (r, down_list) = get_dep_down_msg_from_db(repo_name, repo_version, repo_hash)
    for d in down_list:
        if d[2]:
            d_name = d[0] + '(' + d[2] + ')'
        else:
            d_name = d[0] + '(' + d[3] + ')'
        # d_repo,d_mod,d_version,d_hash,u_repo,u_mod,u_version,u_hash
        dep_msg = [d_name, d[1], r_name, d[5]]
        if dep_msg not in all_down_list:
            all_down_list.append(dep_msg)
    if r > 0:
        for d in down_list:
            l_n = layer
            (all_down_list, l_n) = get_all_down_layer(repo_name, repo_version, repo_hash, all_down_list, layer)
            # (r_2, up_list_2) = get_dep_msg_from_db(up[4], up[6], up[7])
            # for up_2 in up_list_2:
            #     dep_msg_2 = [up_2[0], up_2[1], up_2[4], up_2[5]]
            #     if dep_msg_2 not in all_up_list:
            #         all_up_list.append(dep_msg_2)

                    # all_up_list = get_all_up(repo_name, repo_version, repo_hash, all_up_list)
            # all_up_list = get_all_up(up[4], up[6], up[7], all_up_list)
    return all_down_list


class RepoDep:
    # d_repo, d_mod, d_version, d_hash, d_stars
    d_mod = -1
    d_stars = -1
    u_mod = -1
    u_stars = -1
    issues = '-1'
    search_e = 0
    insert_e = 0
    insert_s = 0
    update_e = 0
    update_s = 0

    def __init__(self, d_list, u_list):
        self.d_repo = d_list[0]
        self.d_version = d_list[1]
        self.d_hash = d_list[2]
        self.u_repo = u_list[0]
        self.u_version = u_list[1]
        self.u_hash = u_list[2]
        id_time = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        self.id = id_time + self.d_repo + '=' + self.u_repo
        self.init_from_repo_db()
        if self.d_hash == '' and d_list[2]:
            self.d_hash = d_list[2]
        elif self.d_version == '' and d_list[1]:
            self.d_version = d_list[1]
        if self.u_hash == '' and u_list[2]:
            self.u_hash = u_list[2]
        elif self.u_version == '' and u_list[1]:
            self.u_version = u_list[1]

    def init_no_issue(self, d_list, u_list):
        self.d_mod = d_list[0]
        self.d_stars = d_list[1]
        self.u_mod = u_list[0]
        self.u_stars = u_list[1]

    def init_from_repo_db(self):
        (host, user, password, db_name) = repo.get_db_insert()
        insert_db = get_repo_insert_db()
        sql = "SELECT id,d_mod,d_version,d_hash,d_stars,u_mod,u_version,u_hash,u_stars,issues FROM " + insert_db
        sql = sql + " WHERE d_repo='%s' AND u_repo='%s'" % (self.d_repo, self.u_repo)
        sql = sql + "AND (d_hash='%s' OR d_version='%s')" % (self.d_hash, self.d_version)
        sql = sql + "AND (u_hash='%s' OR u_version='%s')" % (self.u_hash, self.u_version)
        try:
            # 执行sql语句
            db_check = pymysql.connect(host, user, password, db_name)
            check_cursor = db_check.cursor()
            check_cursor.execute(sql)
            check_result = check_cursor.fetchall()
            check_cursor.close()
            db_check.close()
            if check_result:
                # id,d_mod,d_version,d_hash,d_stars,u_mod,u_version,u_hash,u_stars,issues
                self.id = check_result[0][0]  # update id
                self.d_mod = check_result[0][1]
                if self.d_version != check_result[0][2] and check_result[0][2]:
                    if not self.d_version:
                        self.d_version = check_result[0][2]
                if self.d_hash != check_result[0][3] and check_result[0][3]:
                    if not self.d_hash:
                        self.d_hash = check_result[0][3]
                self.d_stars = check_result[0][4]
                self.u_mod = check_result[0][5]
                if self.u_version != check_result[0][6] and check_result[0][6]:
                    if not self.u_version:
                        self.u_version = check_result[0][6]
                if self.u_hash != check_result[0][7] and check_result[0][7]:
                    if not self.u_hash:
                        self.u_hash = check_result[0][7]
                self.u_stars = check_result[0][8]
                self.issues = check_result[0][9]
        except Exception as exp:
            self.search_e = self.search_e + 1
            print("get repos dep ", self.d_repo, self.d_version, self.d_hash, '==', self.u_repo, self.u_version,
                  self.u_hash, " from ", insert_db, " error:", exp)

    def check_repo_db(self):
        (host, user, password, db_name) = repo.get_db_insert()
        insert_db = get_repo_insert_db()
        sql = "SELECT d_mod,d_version,d_hash,d_stars,u_mod,u_version,u_hash,u_stars,issues FROM " + insert_db
        sql = sql + " WHERE d_repo='%s' AND u_repo='%s'" % (self.d_repo, self.u_repo)
        sql = sql + "AND (d_hash='%s' OR d_version='%s')" % (self.d_hash, self.d_version)
        sql = sql + "AND (u_hash='%s' OR u_version='%s')" % (self.u_hash, self.u_version)
        try:
            # 执行sql语句
            db_check = pymysql.connect(host, user, password, db_name)
            check_cursor = db_check.cursor()
            check_cursor.execute(sql)
            check_result = check_cursor.fetchall()
            check_cursor.close()
            db_check.close()
            if check_result:
                return 1, check_result[0]
            else:
                return 0, []
        except Exception as exp:
            self.search_e = self.search_e + 1
            print("check repos dep ", self.d_repo, self.d_version, self.d_hash, '==', self.u_repo, self.u_version,
                  self.u_hash, " from ", insert_db, " error:", exp)
            return -1, []

    def insert_repo(self):
        (host, user, password, db_name) = repo.get_db_insert()
        insert_db = get_repo_insert_db()
        (check_result, result_list) = self.check_repo_db()
        sql = ''
        if check_result < 1:
            insert_sql = "INSERT INTO " + insert_db
            insert_sql = insert_sql + " (id,d_repo,d_mod,d_version,d_hash,d_stars,u_repo,u_mod,u_version,u_hash," \
                                      "u_stars,issues) VALUES ('%s','%s','%d','%s','%s','%d','%s','%d','%s','%s'," \
                                      "'%d','%s')" % (self.id, self.d_repo, self.d_mod, self.d_version, self.d_hash,
                                                      self.d_stars, self.u_repo, self.u_mod, self.u_version,
                                                      self.u_hash, self.u_stars, self.issues)
            db = pymysql.connect(host, user, password, db_name)
            # print(insert_sql)
            sql = insert_sql
            try:
                insert_cursor = db.cursor()
                # 执行sql语句
                insert_cursor.execute(insert_sql)
                db.commit()
                insert_cursor.close()
                print('@insert ', insert_db, ' successful', self.d_repo, self.d_version, self.d_hash, '==', self.u_repo,
                      self.u_version, self.u_hash)
                self.insert_s = self.insert_s + 1
            except Exception as exp:
                print('*insert ', insert_db, ' error exception is:', exp)
                print('**insert ', insert_db, ' error sql:', insert_sql)
                self.insert_e = self.insert_e + 1
                # 发生错误时回滚
                db.rollback()
            db.close()
        else:
            # d_mod,d_version,d_hash,d_stars,u_mod,u_version,u_hash,u_stars,issues
            class_list = [self.d_mod, self.d_version, self.d_hash, self.d_stars, self.u_mod, self.u_version,
                          self.u_hash, self.u_stars, self.issues]
            change = 0
            for i in range(0, len(class_list)):
                if result_list[i] != class_list[i] and class_list[i] != '' and class_list[i] != -1 \
                        and class_list[i] != '-1':
                    change = change + 1
            if change > 0:
                update_sql = "UPDATE " + insert_db
                update_sql = update_sql + " SET d_mod='%d',d_version='%s',d_hash='%s',d_stars='%d',u_mod='%d'," \
                                          "u_version='%s',u_hash='%s',u_stars='%d',issues='%s' " \
                                          "WHERE id='%s'" % (self.d_mod, self.d_version, self.d_hash, self.d_stars,
                                                             self.u_mod, self.u_version, self.u_hash, self.u_stars,
                                                             self.issues, self.id)
                db = pymysql.connect(host, user, password, db_name)
                # print(update_sql)
                sql = update_sql
                try:
                    update_cursor = db.cursor()
                    # 执行sql语句
                    update_cursor.execute(update_sql)
                    db.commit()
                    update_cursor.close()
                    # print('@update ', insert_db, ' successful', self.d_repo, self.d_version, self.d_hash, '==',
                    #       self.u_repo, self.u_version, self.u_hash)
                    self.update_s = self.update_s + 1
                except Exception as exp:
                    print('*update ', insert_db, ' error exception is:', exp)
                    print('**update ', insert_db, ' error sql:', update_sql)
                    self.update_e = self.update_e + 1
                    # 发生错误时回滚
                    db.rollback()
                db.close()
            # else:
            #     print('This RepoDep already exit!')
        return sql
