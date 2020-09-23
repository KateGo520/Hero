import re
import pymysql

from . import repo


def get_repo_insert_db():
    return 'repo_issues'


def check_is_redirected(dep):
    repo_name = dep.replace('github.com/', '')
    repo_name_list = repo_name.split('/')
    if len(repo_name_list) >= 2:
        fullname = repo_name_list[0] + '/' + repo_name_list[1]
    else:
        fullname = repo_name
    (host, user, password, db_name) = repo.get_db_search()
    sql = "SELECT now_repo_name FROM repo_name_update WHERE old_repo_name='%s'" % fullname
    try:
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            print('This special url have related github url：', check_result[0][0])
            return 1, check_result[0][0]
        else:
            return 0, ''
    except Exception as exp:
        print("check new_web_name error:", exp, '-------------------------------------------------------------')
        return -1, ''


class ISSUE:
    bug_type_num = [0, 0, 0, 0, 0, 0]
    bug_list = ['', '', '', '', '', '']
    break_type_num = [0, 0, 0]
    break_list = ['', '', '']
    issue = ''
    sql_list = []
    old_impact = -1
    new_impact = -1
    check_list_mod = []

    def __init__(self, repo_name, insert_version):
        self.repo_name = repo_name
        self.repo_c = repo.Repo(repo_name, insert_version)
        self.repo_c.init_all()
        sql = self.repo_c.insert_repo()
        self.sql_list.append(sql)
        (self.search_e, self.insert_e, self.insert_s, self.update_e, self.update_s) = self.repo_c.get_e_s_param()
        self.id = self.repo_c.id
        self.repo_name = self.repo_c.repo_name
        self.v_name = self.repo_c.v_name
        self.v_hash = self.repo_c.v_hash
        self.init_from_repo_db()
        # self.repo_c.get_dep_tree()

    def init_with_dep_tree(self):
        self.repo_c.get_dep_tree()

    def init_from_repo_db(self):
        (host, user, password, db_name) = repo.get_db_insert()
        insert_db = get_repo_insert_db()
        sql = "SELECT v_name,v_hash,num1_0,list1_0,num1_1,list1_1,break1,break_list1,num2_0,list2_0,num2_1,list2_1," \
              "break2,break_list2,num3_0,list3_0,num3_1,list3_1,break3,break_list3,old_impact,new_impact " \
              "FROM " + insert_db
        sql = sql + " WHERE id='%s'" % self.id
        try:
            db_check = pymysql.connect(host, user, password, db_name)
            check_cursor = db_check.cursor()
            check_cursor.execute(sql)
            check_result = check_cursor.fetchall()
            check_cursor.close()
            db_check.close()
            if check_result:
                # v_name,v_hash,num1_0,list1_0,num1_1,list1_1,break1,break_list1,num2_0,list2_0,num2_1,list2_1,
                # break2,break_list2,num3_0,list3_0,num3_1,list3_1,break3,break_list3,old_impact,new_impact
                if self.v_name != check_result[0][0] and check_result[0][0]:
                    if not self.v_name:
                        self.v_name = check_result[0][0]
                if self.v_hash != check_result[0][1] and check_result[0][1]:
                    if not self.v_hash:
                        self.v_hash = check_result[0][1]
                self.bug_type_num = [check_result[0][2], check_result[0][4], check_result[0][8], check_result[0][10],
                                     check_result[0][14], check_result[0][16]]
                self.bug_list = [check_result[0][3], check_result[0][5], check_result[0][9], check_result[0][11],
                                 check_result[0][15], check_result[0][17]]
                self.break_type_num = [check_result[0][6], check_result[0][12], check_result[0][18]]
                self.break_list = [check_result[0][7], check_result[0][13], check_result[0][19]]
                self.old_impact = check_result[0][20]
                self.new_impact = check_result[0][21]
        except Exception as exp:
            self.search_e = self.search_e + 1
            print("get repos ", self.id, self.repo_name, self.v_name, self.v_hash, " from ", insert_db, " error:", exp)

    def check_issue(self):
        if self.repo_c.r_type == 4:
            self.bug_type_num[4] = self.bug_type_num[4] + 1
            self.bug_list[4] = self.bug_list[4] + '$' + '3-1' + ':' + self.id.replace('=', '/')
        elif self.repo_c.r_type == 10:
            self.bug_type_num[4] = self.bug_type_num[4] + 1
            self.bug_list[4] = self.bug_list[4] + '$' + '3-3' + ':' + self.id.replace('=', '/')
        elif self.repo_c.v_siv == 1:
            # version not siv
            self.bug_type_num[4] = self.bug_type_num[4] + 1
            self.bug_list[4] = self.bug_list[4] + '$3-2:' + self.id.replace('=', '/')
        elif (self.repo_c.r_type == 2 or (self.repo_c.mod_siv == 2 and self.repo_c.v_dir == 0)) \
                and not re.findall(r"^(gopkg\.in/.+?)\.v\d", self.repo_c.mod_full_path):  # virtual path
            self.repo_c.get_all_direct_depmod()
            if self.repo_c.self_ref > 0:
                self.bug_type_num[0] = self.bug_type_num[0] + 1
                self.bug_list[0] = self.bug_list[0] + '$1--:' + self.id.replace('=', '/')

        if self.repo_c.mod_num > 0:
            print('*module*')
            self.check_bug_new_repo()
        else:
            print('*non-module*')
            self.check_bug_old_repo()
        impact = [0, 0]
        insert = 0
        replace = 0
        for bug_type in range(0, 6):
            if self.bug_type_num[bug_type] > 0:
                insert = insert + 1
                print('bug: ', bug_type, ':', self.bug_list[bug_type])
                if bug_type <= 1:
                    impact[0] = impact[0] + 1
                else:
                    impact[1] = impact[1] + 1
        for break_type in range(0, 3):
            if self.break_type_num[break_type] > 0:
                insert = insert + 1
                print('break: ', break_type, ':', self.break_list[break_type])
                if break_type <= 0:
                    impact[0] = impact[0] + 1
                else:
                    impact[1] = impact[1] + 1
        self.old_impact = impact[0]
        self.new_impact = impact[1]
        self.insert_repo()

    def check_bug_new_repo(self):
        # repo_c.mod_dep_list
        for dep in self.repo_c.mod_dep_list:
            if not re.findall(r"^github\.com/", dep[0]):
                dep_name = dep[0]
                dep_version = dep[1]
                (insert_error, repo_name, repo_version, repo_name_n) = repo.deal_repo_name_version(dep_name, dep_version)
                if insert_error == 0:
                    dep_c = repo.Repo(repo_name, repo_version)
                    dep_c.init_all()
                    d_sql = dep_c.insert_repo()
                    if dep_c.r_type > 0:
                        siv_path = ''
                        if re.findall(r"/v\d+?$", dep[0]):
                            siv_path = re.findall(r"(/v\d+?)$", dep[0])[0]
                        elif re.findall(r"\.v\d+?$", dep[0]):
                            siv_path = re.findall(r"(\.v\d+?)$", dep[0])[0]
                        if (dep_c.mod_full_path != dep[0].replace(siv_path, '')) and dep_c.mod_full_path:
                            self.break_type_num[2] = self.break_type_num[2] + 1
                            self.bug_list[2] = self.bug_list[2] + '$3-3:' + dep_c.id.replace('=', '/')
                        elif dep_c.r_type == 10:
                            self.break_type_num[2] = self.break_type_num[2] + 1
                            self.bug_list[2] = self.bug_list[2] + '$3-3:' + dep_c.id.replace('=', '/')
                        elif dep_c.r_type == 4:
                            self.break_type_num[2] = self.break_type_num[2] + 1
                            self.bug_list[2] = self.bug_list[2] + '$3-1:' + dep_c.id.replace('=', '/')
                        elif dep_c.v_siv == 1:
                            self.break_type_num[2] = self.break_type_num[2] + 1
                            self.bug_list[2] = self.bug_list[2] + '$3-2:' + dep_c.id.replace('=', '/')
                        elif (dep_c.r_type == 2 or (dep_c.mod_siv == 2 and dep_c.v_dir == 0)) \
                                and not re.findall(r"^(gopkg\.in/.+?)\.v\d", dep_c.mod_full_path):  # virtual path
                            dep_c.get_all_direct_depmod()
                            if dep_c.self_ref > 0:
                                self.bug_type_num[0] = self.bug_type_num[0] + 1
                                self.bug_list[0] = self.bug_list[0] + '$1--:' + dep_c.id.replace('=', '/')
            else:
                repo_name_n = ''
                dep_name = dep[0]
                dep_version = dep[1]
                (insert_error, repo_name, repo_version, repo_name_n) = repo.deal_repo_name_version(dep_name, dep_version)
                # if insert_error == 0:
                # ** consider def mecthod **
                if dep[2] == 1:
                    if insert_error == 0:
                        dep_c = repo.Repo(repo_name, repo_version)
                        dep_c.init_all()
                        d_sql = dep_c.insert_repo()
                        if dep_c.r_type > 0:
                            if dep_c.r_type == 10:
                                if not repo_name_n:
                                    self.break_type_num[2] = self.break_type_num[2] + 1
                                    self.break_list[2] = self.break_list[2] + '$3-3:' + dep_c.id.replace('=', '/')
                                elif not re.findall(r"^github.com/" + repo_name_n, dep_c.mod_full_path) and repo_name_n:
                                    self.break_type_num[2] = self.break_type_num[2] + 1
                                    self.break_list[2] = self.break_list[2] + '$3-3:' + repo_name_n
                            elif repo_name_n and not re.findall(r"^github.com/" + repo_name_n, dep_c.mod_full_path):
                                self.break_type_num[1] = self.break_type_num[1] + 1
                                self.break_list[1] = self.break_list[1] + '$2-2:' + repo_name_n
                            elif dep_c.r_type == 4:
                                self.break_type_num[2] = self.break_type_num[2] + 1
                                self.break_list[2] = self.break_list[2] + '$3-1:' + dep_c.id.replace('=', '/')
                            elif dep_c.v_siv == 1:
                                self.break_type_num[2] = self.break_type_num[2] + 1
                                self.break_list[2] = self.break_list[2] + '$3-2:' + dep_c.id.replace('=', '/')
                            elif (dep_c.r_type == 2 or (dep_c.mod_siv == 2 and dep_c.v_dir == 0)) \
                                    and not re.findall(r"^(gopkg\.in/.+?)\.v\d", dep_c.mod_full_path):  # virtual path
                                dep_c.get_all_direct_depmod()
                                if dep_c.self_ref > 0:
                                    self.bug_type_num[0] = self.bug_type_num[0] + 1
                                    self.bug_list[0] = self.bug_list[0] + '$1--:' + dep_c.id.replace('=', '/')
                    elif insert_error < 0:
                        self.bug_type_num[3] = self.bug_type_num[3] + 1
                        self.bug_list[3] = self.bug_list[3] + '$2-2:' + repo_name

                elif dep[2] == 2:
                    if insert_error == 0:
                        dep_c = repo.Repo(repo_name, dep_version)
                        dep_c.init_all()
                        d_sql = dep_c.insert_repo()
                        if dep_c.r_type > 0:
                            if dep_c.r_type == 10:
                                if not repo_name_n:
                                    self.break_type_num[1] = self.break_type_num[1] + 1
                                    self.break_list[1] = self.break_list[1] + '$3-3:' + dep_c.id.replace('=', '/')
                                elif not re.findall(r"^github.com/" + repo_name_n, dep_c.mod_full_path) and repo_name_n:
                                    self.break_type_num[1] = self.break_type_num[1] + 1
                                    self.break_list[1] = self.break_list[1] + '$3-3:' + repo_name_n
                            elif repo_name_n and not re.findall(r"^github.com/" + repo_name_n, dep_c.mod_full_path):
                                self.break_type_num[1] = self.break_type_num[1] + 1
                                self.break_list[1] = self.break_list[1] + '$2-2:' + repo_name_n
                            elif dep_c.r_type == 4:
                                self.break_type_num[1] = self.break_type_num[1] + 1
                                self.break_list[1] = self.break_list[1] + '$3-1:' + dep_c.id.replace('=', '/')
                            elif dep_c.v_siv == 1:
                                self.break_type_num[1] = self.break_type_num[1] + 1
                                self.bug_list[1] = self.bug_list[1] + '$3-2:' + dep_c.id.replace('=', '/')
                    elif insert_error < 0:
                        self.bug_type_num[3] = self.bug_type_num[3] + 1
                        self.bug_list[3] = self.bug_list[3] + '$2-2:' + repo_name

    def check_bug_old_repo(self):
        # self.repo_c.all_dep_list
        # self.direct_repo_list
        for dep in self.repo_c.direct_repo_list:
            if not dep[1]:
                dep_name = dep[0]
                dep_version = dep[1]
                (insert_error, repo_name, repo_version, repo_name_n) = repo.deal_repo_name_version(dep_name, dep_version)
                if repo_name_n and insert_error == 0:
                    dep_c = repo.Repo(repo_name, repo_version)
                    dep_c.init_all()
                    d_sql = dep_c.insert_repo()
                    if not re.findall(r"github\.com/" + repo_name_n, dep_c.mod_full_path) and dep_c.mod_full_path:
                        self.bug_type_num[2] = self.bug_type_num[2] + 1
                        self.bug_list[2] = self.bug_list[2] + '$2-2:' + repo_name_n
                else:
                    if dep[2]:
                        self.bug_type_num[2] = self.bug_type_num[2] + 1
                        self.bug_list[2] = self.bug_list[2] + '$2-2:' + dep[2]
                    else:
                        self.bug_type_num[2] = self.bug_type_num[2] + 1
                        self.bug_list[2] = self.bug_list[2] + '$2-2:' + dep[0]
            elif dep[1]:
                dep_name = dep[0]
                dep_version = dep[1]
                (insert_error, repo_name, repo_version, repo_name_n) = repo.deal_repo_name_version(dep_name, dep_version)
                if insert_error == 0:
                    dep_c = repo.Repo(repo_name, repo_version)
                    dep_c.init_all()
                    d_sql = dep_c.insert_repo()
                    if dep_c.r_type > 0:
                        if dep_c.r_type == 10:
                            if not dep[2]:
                                self.bug_type_num[2] = self.bug_type_num[2] + 1
                                self.bug_list[2] = self.bug_list[2] + '$3-3:' + dep_c.id.replace('=', '/')
                            elif not re.findall(r"^github.com/" + dep[2], dep_c.mod_full_path) and dep_c.mod_full_path:
                                self.bug_type_num[2] = self.bug_type_num[2] + 1
                                self.bug_list[2] = self.bug_list[2] + '$3-3:' + dep[2]
                        elif not re.findall(r"^github.com/" + dep[2], dep_c.mod_full_path) and dep_c.mod_full_path and \
                                dep[2]:
                            self.bug_type_num[2] = self.bug_type_num[2] + 1
                            self.bug_list[2] = self.bug_list[2] + '$2-2:' + dep[2]
                        elif dep_c.r_type == 4:
                            self.bug_type_num[2] = self.bug_type_num[2] + 1
                            self.bug_list[2] = self.bug_list[2] + '$3-1:' + dep_c.id.replace('=', '/')
                        elif dep_c.v_siv == 1:
                            self.bug_type_num[2] = self.bug_type_num[2] + 1
                            self.bug_list[2] = self.bug_list[2] + '$3-2:' + dep_c.id.replace('=', '/')
                        elif (dep_c.r_type == 2 or (dep_c.mod_siv == 2 and dep_c.v_dir == 0)) \
                                and not re.findall(r"^(gopkg\.in/.+?)\.v\d", dep_c.mod_full_path):  # virtual path
                            dep_c.get_all_direct_depmod()
                            if dep_c.self_ref > 0 and self.repo_c.tool_num > 0:
                                self.bug_type_num[0] = self.bug_type_num[0] + 1
                                self.bug_list[0] = self.bug_list[0] + '$1--:' + dep_c.id.replace('=', '/')
                    if dep_c.mod_num > 0:
                        if dep_c.v_hash:
                            dep_c_issue = ISSUE(dep_c.repo_name, dep_c.v_hash)
                        else:
                            dep_c_issue = ISSUE(dep_c.repo_name, dep_c.v_name)
                        dep_c_issue.check_issue()
                        if dep_c_issue.bug_type_num[0] > 0 and self.repo_c.tool_num > 0:
                            self.bug_type_num[1] = self.bug_type_num[1] + dep_c_issue.bug_type_num[0]
                            self.bug_list[1] = self.bug_list[1] + dep_c_issue.bug_list[0]

    def check_repo_db(self):
        (host, user, password, db_name) = repo.get_db_insert()
        insert_db = get_repo_insert_db()
        sql = "SELECT v_name,v_hash,num1_0,list1_0,num1_1,list1_1,break1,break_list1,num2_0,list2_0,num2_1,list2_1," \
              "break2,break_list2,num3_0,list3_0,num3_1,list3_1,break3,break_list3,old_impact,new_impact " \
              "FROM " + insert_db
        sql = sql + " WHERE v_name='%s' OR v_hash='%s'" % (self.v_name, self.v_hash)
        try:
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
            print("get repos ", self.id, self.repo_name, self.v_name, self.v_hash, " from ", insert_db, " error:", exp)
            return -1, []

    def insert_repo(self):
        (host, user, password, db_name) = repo.get_db_insert()
        insert_db = get_repo_insert_db()
        (check_result, result_list) = self.check_repo_db()
        sql = ''
        if check_result < 1:
            # v_name,v_hash,num1_0,list1_0,num1_1,list1_1,break1,break_list1,num2_0,list2_0,num2_1,list2_1,
            # break2,break_list2,num3_0,list3_0,num3_1,list3_1,break3,break_list3,old_impact,new_impact
            insert_sql = "INSERT INTO " + insert_db
            insert_sql = insert_sql + " (id,repo_name,v_name,v_hash,num1_0,list1_0,num1_1,list1_1,break1,break_list1," \
                                      "num2_0,list2_0,num2_1,list2_1,break2,break_list2,num3_0,list3_0,num3_1," \
                                      "list3_1,break3,break_list3,old_impact,new_impact) VALUES ('%s','%s','%s','%s'," \
                                      "'%d','%s','%d','%s','%d','%s','%d','%s','%d','%s','%d','%s','%d','%s','%d'," \
                                      "'%s','%d','%s','%d'," \
                                      "'%d')" % (self.id, self.repo_name, self.v_name, self.v_hash,
                                                 self.bug_type_num[0], self.bug_list[0], self.bug_type_num[1],
                                                 self.bug_list[1], self.break_type_num[0], self.break_list[0],
                                                 self.bug_type_num[2], self.bug_list[2], self.bug_type_num[3],
                                                 self.bug_list[3], self.break_type_num[1], self.break_list[1],
                                                 self.bug_type_num[4], self.bug_list[4], self.bug_type_num[5],
                                                 self.bug_list[5], self.break_type_num[2], self.break_list[2],
                                                 self.old_impact, self.new_impact)
            db = pymysql.connect(host, user, password, db_name)
            # print(insert_sql)
            sql = insert_sql
            try:
                insert_cursor = db.cursor()
                insert_cursor.execute(insert_sql)
                db.commit()
                insert_cursor.close()
                print('insert ', insert_db, ' successful', self.repo_name, self.v_name, self.v_hash)
                self.insert_s = self.insert_s + 1
            except Exception as exp:
                print('insert ', insert_db, ' error exception is:', exp)
                print('insert ', insert_db, ' error sql:', insert_sql)
                self.insert_e = self.insert_e + 1
                db.rollback()
            db.close()
        else:
            # v_name,v_hash,num1_0,list1_0,num1_1,list1_1,break1,break_list1,num2_0,list2_0,num2_1,list2_1,
            # break2,break_list2,num3_0,list3_0,num3_1,list3_1,break3,break_list3,old_impact,new_impact
            class_list = [self.v_name, self.v_hash, self.bug_type_num[0], self.bug_list[0], self.bug_type_num[1],
                          self.bug_list[1], self.break_type_num[0], self.break_list[0], self.bug_type_num[2],
                          self.bug_list[2], self.bug_type_num[3], self.bug_list[3], self.break_type_num[1],
                          self.break_list[1], self.bug_type_num[4], self.bug_list[4], self.bug_type_num[5],
                          self.bug_list[5], self.break_type_num[2], self.break_list[2], self.old_impact,
                          self.new_impact]
            change = 0
            for i in range(0, len(class_list)):
                if result_list[i] != class_list[i] and class_list[i] != '' and class_list[i] != -1 \
                        and class_list[i] != '-1':
                    change = change + 1
            if change > 0:
                update_sql = "UPDATE " + insert_db
                update_sql = update_sql + " SET v_name='%s',v_hash='%s',num1_0='%d',list1_0='%s',num1_1='%d'," \
                                          "list1_1='%s',break1='%d',break_list1='%s',num2_0='%d',list2_0='%s'," \
                                          "num2_1='%d',list2_1='%s',break2='%d',break_list2='%s',num3_0='%d'," \
                                          "list3_0='%s',num3_1='%d',list3_1='%s',break3='%d',break_list3='%s'," \
                                          "old_impact='%d',new_impact='%d' " \
                                          "WHERE id='%s'" % (self.v_name, self.v_hash, self.bug_type_num[0],
                                                             self.bug_list[0], self.bug_type_num[1], self.bug_list[1],
                                                             self.break_type_num[0], self.break_list[0],
                                                             self.bug_type_num[2], self.bug_list[2],
                                                             self.bug_type_num[3], self.bug_list[3],
                                                             self.break_type_num[1], self.break_list[1],
                                                             self.bug_type_num[4], self.bug_list[4],
                                                             self.bug_type_num[5], self.bug_list[5],
                                                             self.break_type_num[2], self.break_list[2],
                                                             self.old_impact, self.new_impact, self.id)
                db = pymysql.connect(host, user, password, db_name)
                print(update_sql)
                sql = update_sql
                try:
                    update_cursor = db.cursor()
                    update_cursor.execute(update_sql)
                    db.commit()
                    update_cursor.close()
                    print('update ', insert_db, ' successful', self.repo_name, self.v_name, self.v_hash)
                    self.update_s = self.update_s + 1
                except Exception as exp:
                    print('update ', insert_db, ' error exception is:', exp)
                    print('update ', insert_db, ' error sql:', update_sql)
                    self.update_e = self.update_e + 1
                    db.rollback()
                db.close()
        return sql

    def return_issues(self):
        (host, user, password, db_name) = repo.get_db_insert()
        insert_db = get_repo_insert_db()
        sql = "SELECT num1_0,list1_0,num1_1,list1_1,break1,break_list1,num2_0,list2_0,num2_1,list2_1," \
              "break2,break_list2,num3_0,list3_0,num3_1,list3_1,break3,break_list3,old_impact,new_impact " \
              "FROM " + insert_db
        sql = sql + " WHERE v_name='%s' OR v_hash='%s'" % (self.v_name, self.v_hash)
        try:
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
            print("get repos ", self.id, self.repo_name, self.v_name, self.v_hash, " from ", insert_db, " error:", exp)
            return -1, []
