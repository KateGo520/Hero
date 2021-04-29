import re
import pymysql

from . import repo
# import repo


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
        # 执行sql语句
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
    search_e = 0
    insert_e = 0
    insert_s = 0
    update_e = 0
    update_s = 0

    def __init__(self, repo_name, insert_version):

        (htv_r, r_version) = repo.check_hashToVersion(repo_name, insert_version)
        # print('check_hashToVersion', htv_r, r_version)
        if htv_r == 1:
            self.repo_c = repo.Repo(repo_name, [r_version, insert_version])
        else:
            self.repo_c = repo.Repo(repo_name, insert_version)

        self.id = self.repo_c.id
        self.repo_name = self.repo_c.repo_name
        self.v_name = self.repo_c.v_name
        self.v_hash = self.repo_c.v_hash
        # self.init_from_repo_db()
        (self.search_e, self.insert_e, self.insert_s, self.update_e, self.update_s) = self.repo_c.get_e_s_param()
        self.new_impact = -1

        if self.new_impact < 0 or self.old_impact < 0:
            self.bug_type_num = [0, 0, 0, 0, 0, 0]
            self.bug_list = ['', '', '', '', '', '']
            self.break_type_num = [0, 0, 0]
            self.break_list = ['', '', '']
            self.issue = ''
            self.sql_list = []
            self.old_impact = -1
            self.new_impact = -1
            self.heck_list_mod = []
            self.repo_c.init_all()
            sql = self.repo_c.insert_repo()
            self.sql_list.append(sql)
            (self.search_e, self.insert_e, self.insert_s, self.update_e, self.update_s) = self.repo_c.get_e_s_param()
            # self.init_from_repo_db()
            # self.repo_c.get_dep_tree()
        if self.repo_c.path_match == -1 or self.repo_c.r_type == -1:
            self.repo_c.init_all()
            sql = self.repo_c.insert_repo()
            self.sql_list.append(sql)

    def init_with_dep_tree(self):
        self.repo_c.init_with_dep_tree()

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
        (f_r, f_list) = repo.get_fake_version_list()
        mod_siv = repo.get_imp_siv_path(self.repo_c.mod_full_path)
        # print(self.repo_c.r_type)
        if self.repo_c.r_type == 4:
            # 3-1,C,down module user warning
            self.bug_type_num[4] = self.bug_type_num[4] + 1
            self.bug_list[4] = self.bug_list[4] + '$3-1:' + self.id.replace('=', '/')
        elif [self.repo_c.repo_name, self.repo_c.v_hash, '3-1'] in f_list:
            fake_version = repo.get_fake_version(self.repo_c.repo_name, self.repo_c.v_hash)
            i_id = self.repo_c.repo_name + '@' + fake_version
            # 3-1,C,down module user warning
            self.bug_type_num[4] = self.bug_type_num[4] + 1
            self.bug_list[4] = self.bug_list[4] + '$3-1:' + i_id
        elif not mod_siv and self.repo_c.mod_num >= 2:
            # 3-1,C,down module user warning
            self.bug_type_num[4] = self.bug_type_num[4] + 1
            self.bug_list[4] = self.bug_list[4] + '$3-1:' + self.id.replace('=', '/')
        if self.repo_c.r_type == 10:
            siv_path = repo.get_imp_siv_path(self.repo_c.mod_full_path)
            mod_name = self.repo_c.mod_full_path.replace(siv_path, '').strip('/')
            git_name = repo.get_github_name_db(mod_name)
            if not git_name:
                # 3-3,C,down module user warning
                self.bug_type_num[4] = self.bug_type_num[4] + 1
                self.bug_list[4] = self.bug_list[4] + '$3-3:' + self.repo_name + '@' + self.repo_c.mod_full_path
        if self.repo_c.v_siv == 1 and self.repo_c.mod_num > 0:
            # version not siv
            # 3-2,C,down module user warning
            self.bug_type_num[4] = self.bug_type_num[4] + 1
            self.bug_list[4] = self.bug_list[4] + '$3-2:' + self.id.replace('=', '/')
        elif [self.repo_c.repo_name, self.repo_c.v_hash, '3-2'] in f_list:
            fake_version = repo.get_fake_version(self.repo_c.repo_name, self.repo_c.v_hash)
            i_id = self.repo_c.repo_name + '@' + fake_version
            # version not siv
            #  3-2,C,down module user warning
            self.bug_type_num[4] = self.bug_type_num[4] + 1
            self.bug_list[4] = self.bug_list[4] + '$3-2:' + i_id
        if (self.repo_c.r_type == 2 or (self.repo_c.mod_siv == 2 and self.repo_c.v_dir == 0)) \
                and not re.findall(r"^(gopkg\.in/.+?)\.v\d", self.repo_c.mod_full_path):  # virtual path

            # close for now ~~~~
            # self.repo_c.get_dm_local_new()
            # if self.repo_c.self_ref > 0:

            # 1-0,A,downstream warning
            self.bug_type_num[0] = self.bug_type_num[0] + 1
            self.bug_list[0] = self.bug_list[0] + '$1--:' + self.id.replace('=', '/')

        if self.repo_c.mod_num > 0 and (self.repo_c.tool_num == 0 or self.repo_c.mod_url[0] == '/'):
            # Go Modules
            print('*module*')
            self.check_bug_new_repo()
        else:
            # GOPATH
            print('*non-module*')
            self.check_bug_old_repo()
        impact = [0, 0]
        insert = 0
        replace = 0
        for bug_type in range(0, 6):
            if self.bug_type_num[bug_type] > 0:
                insert = insert + 1
                print('bug_issues', bug_type, ':', self.bug_list[bug_type])
                if bug_type <= 1:
                    impact[0] = impact[0] + 1
                else:
                    impact[1] = impact[1] + 1
        for break_type in range(0, 3):
            if self.break_type_num[break_type] > 0:
                insert = insert + 1
                print('break_issues', break_type, ':', self.break_list[break_type])
                if break_type <= 0:
                    impact[0] = impact[0] + 1
                else:
                    impact[1] = impact[1] + 1
        self.old_impact = impact[0]
        self.new_impact = impact[1]
        self.insert_repo()

    def check_bug_new_repo(self):
        # repo_c.mod_dep_list
        issue_22 = 0
        if not self.repo_c.direct_dep_list:
            self.repo_c.get_dm_local_new()
        delete_list = []
        for dep in self.repo_c.direct_dep_list:
            if dep[0] == self.repo_name:
                delete_list.append(dep)
        self.repo_c.self_ref = len(delete_list)
        for dep in delete_list:
            self.repo_c.direct_dep_list.remove(dep)
        for dep in self.repo_c.direct_dep_list:
            repo_name_n = ''
            dep_name = dep[0]
            dep_version = dep[1]
            if not dep[2]:
                new_url = repo.get_new_url('github.com/' + dep_name)
                if new_url:
                    issue_22 += 1
                    # 问题2-2，C，更新可能会遇到问题
                    self.bug_type_num[3] = self.bug_type_num[3] + 1
                    self.bug_list[3] = self.bug_list[3] + '$2-2:' + 'github.com/' + dep[0] + '@' + new_url
            if dep[4] == 1:
                issue_22 += 1
                # 问题2-2，C，更新可能会遇到问题
                if dep[0] == '0' or not dep[0]:
                    r = dep[0]
                else:
                    r = 'github.com/' + dep[0]
                self.bug_type_num[3] = self.bug_type_num[3] + 1
                self.bug_list[3] = self.bug_list[3] + '$2-2:' + 'github.com/' + dep[2] + '@' + r

            (insert_error, repo_name, repo_version,
             repo_name_n) = repo.deal_repo_name_version(dep_name, dep_version)
            if insert_error == 0:
                dep_c = repo.Repo(repo_name, repo_version)
                dep_c.init_all()
                d_sql = dep_c.insert_repo()
                if dep_c.r_type > 0:
                    if dep_c.r_type == 10:
                        if not dep[2]:
                            # 问题3-3，C，已经发生
                            self.break_type_num[2] = self.break_type_num[2] + 1
                            self.break_list[2] = self.break_list[2] + '$3-3:' + repo_name + '@' + dep_c.mod_full_path
                        elif not re.findall(r"^github.com/" + dep[2], dep_c.mod_full_path) and dep[2]:
                            # 问题3-3，C，已经发生
                            self.break_type_num[2] = self.break_type_num[2] + 1
                            self.break_list[2] = self.break_list[2] + '$3-3:' + dep[2] + '@' + dep_c.mod_full_path
                    elif dep_c.r_type == 4:
                        # 问题3-1，C，已经发生
                        self.break_type_num[2] = self.break_type_num[2] + 1
                        self.break_list[2] = self.break_list[2] + '$3-1:' + dep_c.id.replace('=', '/')
                    elif dep_c.v_siv == 1:
                        # 问题3-2，C，已经发生
                        self.break_type_num[2] = self.break_type_num[2] + 1
                        self.break_list[2] = self.break_list[2] + '$3-2:' + dep_c.repo_name + '@' + dep_c.v_name
                    elif (dep_c.r_type == 2 or (dep_c.mod_siv == 2 and dep_c.v_dir == 0)) \
                            and not re.findall(r"^(gopkg\.in/.+?)\.v\d", dep_c.mod_full_path):  # virtual path

                        # 暂时放开该问题的检测，后续需要重开并重跑 ~~~~
                        # 检测该项目是否存在自身调用，因为如果本项目是分支法创建的v>=2的，且本地有调用自己的代码则会出现影响下游的情况。
                        # dep_c.get_dm_local_new()
                        # if dep_c.self_ref > 0:

                        # 问题1-0，A，下游预警
                        self.bug_type_num[0] = self.bug_type_num[0] + 1
                        self.bug_list[0] = self.bug_list[0] + '$1--:' + dep_c.id.replace('=', '/')
            # elif insert_error < 0 and not dep[2]:
            #     # issue_22 += 1
            #     # 问题2-2，C，更新可能会遇到问题
            #     self.bug_type_num[3] = self.bug_type_num[3] + 1
            #     self.bug_list[3] = self.bug_list[3] + '$2-2:' + 'github.com/' + dep[0] + '@0'

        # 问题2-1
        issue_repo_list = self.repo_c.diagnosis_issue_2()
        if issue_repo_list:
            for i in issue_repo_list:
                if i[1] == 1:
                    # 问题2-1，B.b，更新可能会遇到问题
                    self.bug_type_num[3] = self.bug_type_num[3] + 1
                    self.bug_list[3] = self.bug_list[3] + '$2-1:' + i[0]
                if i[1] > 1:
                    # 问题2-1，B.b，更新可能会遇到问题
                    self.bug_type_num[3] = self.bug_type_num[3] + 1
                    self.bug_list[3] = self.bug_list[3] + '$2-3:' + i[0]
                else:
                    if issue_22 == 0:
                        # 问题2-2，B.b，更新可能会遇到问题
                        self.bug_type_num[2] = self.bug_type_num[2] + 1
                        self.bug_list[2] = self.bug_list[2] + '$2-2:' + i[0]

    # direct_repo_list = [git_name, version, befor_name, siv_path, old]  old: 1 是旧路径；0 是新路径
    def check_bug_old_repo(self):
        # self.repo_c.all_dep_list
        # self.direct_repo_list
        issue_22 = 0
        delete_list = []
        for dep in self.repo_c.direct_dep_list:
            if dep[0] == self.repo_name:
                delete_list.append(dep)
        for dep in delete_list:
            self.repo_c.direct_dep_list.remove(dep)
        self.repo_c.self_ref = len(delete_list)
        # print('all direct dep: ', self.repo_c.direct_dep_list)
        for dep in self.repo_c.direct_dep_list:
            # 如果不存在版本号  极个别情况
            if not dep[1]:
                (dep_version, dep_semantic) = repo.get_last_version(dep[0])
                if not dep_semantic:
                    dep_version = repo.get_last_hash(dep[0])
                    (v_name, v_hash, search_e) = repo.get_last_version_or_hashi(dep[0], self.search_e)
                    if v_name:
                        dep[1] = v_name
                    else:
                        dep[1] = v_hash

            dep_name = dep[0]
            dep_version = dep[1]
            # dep[2]为空
            if not dep[2]:
                new_url = repo.get_new_url('github.com/' + dep_name)
                if new_url:
                    issue_22 += 1
                    # 问题2-2，C，更新可能会遇到问题

                    self.bug_type_num[3] = self.bug_type_num[3] + 1
                    self.bug_list[3] = self.bug_list[3] + '$2-2:' + 'github.com/' + dep[0] + '@' + new_url
                    print('##################-----1111111111', dep)

            if dep[4] == 1:
                issue_22 += 1
                # 问题2-2，C，更新可能会遇到问题

                if dep[0] == '0' or not dep[0]:
                    r = dep[0]
                else:
                    r = 'github.com/' + dep[0]
                self.bug_type_num[3] = self.bug_type_num[3] + 1
                self.bug_list[3] = self.bug_list[3] + '$2-2:' + 'github.com/' + dep[2] + '@' + r
                print('##################-----22222222222', dep)

            (insert_error, repo_name, repo_version,
             repo_name_n) = repo.deal_repo_name_version(dep_name, dep_version)
            if insert_error == 0:
                dep_c = repo.Repo(repo_name, repo_version)
                dep_c.init_all()
                d_sql = dep_c.insert_repo()
                print('check1 ', dep_c.repo_name, dep_c.v_name, dep_c.mod_full_path, dep_c.r_type)
                issue_11 = 0
                if dep_c.r_type > 0:
                    if dep_c.r_type == 10:
                        if not dep[2]:
                            # 问题3-3，C，下游可能引发问题2-1
                            self.bug_type_num[2] = self.bug_type_num[2] + 1
                            self.bug_list[2] = self.bug_list[2] + '$3-3:' + dep_c.repo_name + '@' + dep_c.mod_full_path
                        elif not re.findall(r"^github.com/" + dep[2], dep_c.mod_full_path) and dep_c.mod_full_path:
                            # 问题3-3，C，下游可能引发问题2-1
                            self.bug_type_num[2] = self.bug_type_num[2] + 1
                            self.bug_list[2] = self.bug_list[2] + '$3-3:' + dep_c.repo_name + '@' + dep_c.mod_full_path

                    if dep_c.r_type == 4:
                        # 问题3-1，C，下游可能引发问题3-1
                        self.bug_type_num[2] = self.bug_type_num[2] + 1
                        self.bug_list[2] = self.bug_list[2] + '$3-1:' + dep_c.id.replace('=', '/')
                    if dep_c.v_siv == 1:
                        # 问题3-2，C，下游可能引发问题3-2
                        self.bug_type_num[2] = self.bug_type_num[2] + 1
                        self.bug_list[2] = self.bug_list[2] + '$3-2:' + dep_c.id.replace('=', '/')
                    if dep_c.r_type == 2 or (dep_c.mod_siv == 2 and dep_c.v_dir <= 0):  # virtual path
                        print('virtual path')
                        if not re.findall(r"^(gopkg\.in/.+?)\.v\d", dep_c.mod_full_path):
                            dep_mod_siv = repo.get_imp_siv_path(dep_c.mod_full_path)
                            if not dep[3] or re.findall(r"^\.v\d", dep[3]) or dep_mod_siv != dep[3]:
                                # 暂时放开该问题的检测，后续需要重开并重跑 ~~~~
                                # 检测该项目是否存在自身调用，因为如果本项目是分支法创建的v>=2的，且本地有调用自己的代码则会出现影响下游的情况。
                                # dep_c.get_dm_local_new()
                                # if dep_c.self_ref > 0:

                                issue_11 = 1
                                # 问题1-1，A，升级预警
                                self.bug_type_num[1] = self.bug_type_num[1] + 1
                                self.bug_list[1] = self.bug_list[1] + '$1--:' + dep_c.id.replace('=', '/') + '@' + dep[2]
                if dep_c.mod_num > 0 and issue_11 == 0:
                    virtual_list = dep_c.diagnosis_issue_1()
                    if virtual_list:
                        # 问题1-1，A，升级预警
                        self.bug_type_num[1] = self.bug_type_num[1] + 1
                        self.bug_list[1] = self.bug_list[1] + '$1--:' + dep_c.id.replace('=', '/')
                    # if dep_c.v_hash:
                    #     dep_c_issue = ISSUE(dep_c.repo_name, dep_c.v_hash)
                    # else:
                    #     dep_c_issue = ISSUE(dep_c.repo_name, dep_c.v_name)
                    # dep_c_issue.check_issue()
                    # if dep_c_issue.bug_type_num[0] > 0 and self.repo_c.tool_num > 0:
                    #     self.bug_type_num[1] = self.bug_type_num[1] + dep_c_issue.bug_type_num[0]
                    #     self.bug_list[1] = self.bug_list[1] + dep_c_issue.bug_list[0]

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

    def get_bug_report_with_dmsg(self, d_msg_list):
        bug_list = []
        report_list = []
        # 3-1
        if self.bug_type_num[4] > 0:
            b_l = self.bug_list[4].split('$')
            b_l_d = []
            for b in b_l:
                if re.findall(r".+?:.+?", b):
                    b_l_d.append(b)
            for b in b_l_d:
                b_d_l = b.split(':')
                b_type = b_d_l[0]
                b_detail = b_d_l[1]
                bug_list.append(['3-0', b_type, b_detail])

        if self.bug_type_num[3] > 0:
            b_l = self.bug_list[3].split('$')
            b_l_d = []
            for b in b_l:
                if re.findall(r".+?:.+?", b):
                    b_l_d.append(b)
            for b in b_l_d:
                b_d_l = b.split(':')
                b_type = b_d_l[0]
                b_detail = b_d_l[1]
                bug_list.append(['2', b_type, b_detail])

        if self.bug_type_num[2] > 0:
            b_l = self.bug_list[2].split('$')
            b_l_d = []
            for b in b_l:
                if re.findall(r".+?:.+?", b):
                    b_l_d.append(b)
            for b in b_l_d:
                b_d_l = b.split(':')
                b_type = b_d_l[0]
                b_detail = b_d_l[1]
                bug_list.append(['2', b_type, b_detail])

        if self.bug_type_num[1] > 0:
            b_l = self.bug_list[1].split('$')
            b_l_d = []
            for b in b_l:
                if re.findall(r".+?:.+?", b):
                    b_l_d.append(b)
            for b in b_l_d:
                b_d_l = b.split(':')
                b_type = b_d_l[0]
                b_detail = b_d_l[1]
                bug_list.append(['1-1', b_type, b_detail])

        if self.break_type_num[1] > 0:
            b_l = self.break_list[1].split('$')
            b_l_d = []
            for b in b_l:
                if re.findall(r".+?:.+?", b):
                    b_l_d.append(b)
            for b in b_l_d:
                b_d_l = b.split(':')
                b_type = b_d_l[0]
                b_detail = b_d_l[1]
                bug_list.append(['2', b_type, b_detail])

        if self.break_type_num[2] > 0:
            b_l = self.break_list[2].split('$')
            b_l_d = []
            for b in b_l:
                if re.findall(r".+?:.+?", b):
                    b_l_d.append(b)
            for b in b_l_d:
                b_d_l = b.split(':')
                b_type = b_d_l[0]
                b_detail = b_d_l[1]
                bug_list.append(['3-2', b_type, b_detail])

        r_id = self.repo_name + '@' + self.v_hash
        bug_type = repo.check_report_bug_type_dr(r_id)
        if bug_type == '1-1':
            order_list = ['1-1', '3-0=3-1', '3-0=3-3', '2-1=2-1', '2-2=2-2', '3-0=3-2']
        elif bug_type == '2-1=2-1':
            order_list = ['2-1=2-1', '3-0=3-1', '3-0=3-3', '1-1', '2-2=2-2', '3-0=3-2']
        elif bug_type == '2-2=2-2':
            order_list = ['2-2=2-2', '2-1=2-1', '3-0=3-1', '3-0=3-3', '1-1', '3-0=3-2']
        elif bug_type == '3=3':
            order_list = ['3-0=3-1', '3-0=3-3', '3-0=3-2', '2-2=2-2', '2-1=2-1', '1-1']
        else:
            order_list = ['3-0=3-1', '3-0=3-3', '2-1=2-1', '1-1', '2-2=2-2', '3-0=3-2']
        r_11_list = []
        r_21_list = []
        r_23_list = []
        r_21_21_list = []
        r_22_22_list = []
        s_22_22_list = []
        for b in bug_list:
            if b[0] == '3-0' and b[1] == '3-1':
                if len(b[2].split('@')) >= 3:
                    repo_name = b[2].split('@')[0]
                    version_str = b[2].split('@')[1]
                    v_num_str = b[2].split('@')[2].replace('v', '')
                else:
                    version_str = self.repo_c.v_name
                    v_num_str = self.repo_c.v_num.replace('v', '')
                r_30_31_str = '<h3>ISSUE Type C.a :</h3>Project <em> ' + self.repo_c.repo_name + ' ' + version_str
                r_30_31_str += ' </em> uses Go modules. According to the specification of "Releasing Modules ' \
                               'for v2 or higher", available in the <a href="https://github.com/golang/go/wiki/' \
                               'Modules#releasing-modules-v2-or-higher">Modules documentation</a>, the module path ' \
                               'should be <em> "' + self.repo_c.mod_name + '/v' + v_num_str + '" </em> . '
                r_30_31_str += '<br />However, <em> ' + self.repo_c.repo_name + ' ' + version_str + '\'s </em> '
                r_30_31_str += 'module path is	<em> "' + self.repo_c.mod_name + '" </em>, which will introduce the '
                r_30_31_str += 'following error into its downstream modules users:<br/><div class="code-div">'
                r_30_31_str += '>invalid version: module contains a go.mod file, so major version must be ' \
                               'compatible: should be v0 or v1, not v' + v_num_str + '</div><br/>'
                s_30_31_str = '<h3>1. Roll back to GOPATH.</h3>This solution cancels previous Go Modules migration ' \
                              'to fix the issue by solving migration’s caused incompatibility.<br/>' \
                              '<span class="b_class">Benefit:</span> This solution supports downstream ' \
                              'projects without module awareness.<br/><span class="c_class">Cost:</span>This ' \
                              'solution hinders the migration status to the ecosystem.<br/>' \
                              '<h4>2. Fix configuration items to follow Semantic Import Versioning rules.</h4>' \
                              'Patch your go.mod file to declare your module path as ' \
                              '<em> "' + self.repo_c.mod_name + '/v' + v_num_str + '" </em>  '
                s_30_31_str += 'as per <a href="https://github.com/golang/go/wiki/Modules#releasing-modules-v2-' \
                              'or-higher">the specs</a>. And adjust all your internal import paths.<br/>' \
                              '<span class="b_class">Benefit:</span> This solution supports downstream projects ' \
                              'in Go Modules. <br/><span class="c_class">Cost:</span> This solution will ' \
                              'break compatibility with downstream projects without module awareness.<br/>' \

                if d_msg_list[2] > 0:
                    if d_msg_list[2] >= 2:
                        usr_str = 'users'
                    else:
                        usr_str = 'user'
                    s_30_31_str += '[*] You can see which module-unaware downstream projects will ' \
                                   'be affected here: (<em>'
                    s_30_31_str += str(d_msg_list[2]) + ' module-unaware</em> ' + usr_str + ', e.g.'
                    if d_msg_list[2] >= 3:
                        if len(d_msg_list[5]) >= 3:
                            s_30_31_str += ', ' + d_msg_list[5][0] + ', ' + d_msg_list[5][1] + ', ' + d_msg_list[5][2]
                            s_30_31_str += ')<br/>'
                        else:
                            for d in d_msg_list[5]:
                                s_30_31_str = s_30_31_str + ', ' + d
                            s_30_31_str += ')<br/>'
                    else:
                        for d in d_msg_list[5]:
                            s_30_31_str = s_30_31_str + ', ' + d
                        s_30_31_str += ')<br/>'
                    for u in range(0, len(d_msg_list[3])):
                        if len(d_msg_list[3]) == 1:
                            link_str = 'LINK'
                        else:
                            link_str = 'LINK-' + str(u + 1)
                        s_30_31_str = s_30_31_str + '<a href="' + d_msg_list[3][u] + '">' + link_str + '</a>&nbsp;&nbsp;&nbsp;&nbsp;'

                s_30_31_str += '<h4>3. Suggest downstream module users use hash commit ID for a specific version ' \
                               'to replace a problematic version number in library referencing.</h4>' \
                               'If the standard rule of go modules conflicts with your development mode, ' \
                               'you can’t comply with the specification of "Releasing Modules for v2 or higher" ' \
                               'available in the Modules documentation. Then your downstream module users can ' \
                               'avoids referencing problematic version numbers and encountering errors, by a ' \
                               'require directive with a specific hash commit ID. The specific operations ' \
                               'are as follows: <br/><div class="code-div">(1) Search for the tag you want ' \
                               '(in browser);<br/>(2) Get the commit hash of the tag you want;<br/>' \
                               '(3) Run <em>go get ' + self.repo_c.mod_name + '@commit-hash</em> ;<br/>'
                s_30_31_str += '(4) Edit the go.mod file to put a comment about which version ' \
                               'you actually used.<br/></div><span class="c_class">Cost:</span> This will make ' \
                               'it difficult for downstream module users to get and ' \
                               'upgrade <em>' + self.repo_c.repo_name + '</em>, increasing maintenancecost.<br/>'
                if d_msg_list[0] > 0:
                    if d_msg_list[0] >= 2:
                        usr_str = 'users'
                    else:
                        usr_str = 'user'
                    s_30_31_str += '[*] You can see which module-aware downstream projects will be affected here: (<em>'
                    s_30_31_str += str(d_msg_list[0]) + ' module</em> ' + usr_str + ', e.g.'
                    if d_msg_list[0] >= 3:
                        if len(d_msg_list[4]) >= 3:
                            s_30_31_str += ', ' + d_msg_list[4][0] + ', ' + d_msg_list[4][1] + ', ' + d_msg_list[4][2]
                            s_30_31_str += ')<br/>'
                        else:
                            for d in d_msg_list[4]:
                                s_30_31_str = s_30_31_str + ', ' + d
                            s_30_31_str += ')<br/>'
                    else:
                        for d in d_msg_list[4]:
                            s_30_31_str = s_30_31_str + ', ' + d
                        s_30_31_str += ')<br/>'
                    for u in range(0, len(d_msg_list[1])):
                        if len(d_msg_list[1]) == 1:
                            link_str = 'LINK'
                        else:
                            link_str = 'LINK-' + str(u + 1)
                        s_30_31_str = s_30_31_str + '<a href="' + d_msg_list[1][u] + '">' + link_str + '</a>&nbsp;&nbsp;&nbsp;&nbsp;'
                s_30_31_str += '</br>'
                if [r_30_31_str, s_30_31_str, order_list.index('3-0=3-1')] not in report_list:
                    report_list.append([r_30_31_str, s_30_31_str, order_list.index('3-0=3-1')])
            if b[0] == '3-0' and b[1] == '3-3':
                if self.repo_c.v_name:
                    version_str = self.repo_c.v_name
                else:
                    version_str = self.repo_c.v_hash
                r_30_33_str = '<h3>ISSUE Type C.c :</h3>Module path in your go.mod file is inconsistent with ' \
                              'your URL on the hosting site. Module path is <em> "' + self.repo_c.mod_name
                r_30_33_str += '" </em>, but URL on the hosting site is <em> "github.com/' + self.repo_c.repo_name
                r_30_33_str += '" </em>. Running <em>go get github.com/' + self.repo_c.repo_name
                r_30_33_str += '</em> with GO111MODULE=on, will get the following errors:<br/><div class="code-div">' \
                               ' > go get: github.com/' + self.repo_c.repo_name + '@' + version_str
                r_30_33_str += ': parsing go.mod:<br/> > module declares its path as: ' + self.repo_c.mod_name
                r_30_33_str += '<br/> > but was required as: github.com/' + self.repo_c.repo_name + '</div><br/>'
                s_30_33_str = '<h3>1. Fix configuration items to follow Semantic Import Versioning rules.</h3>' \
                              'Fix your module path: Rename module path to be <em> "github.com/' \
                              + self.repo_c.repo_name
                s_30_33_str += '" </em>.<h4>2. Suggest downstream module users use a replace directive to ' \
                               'replace the original import path and avoid errors.</h4>Downstream module users ' \
                               'add this replace directive in their go.mod files:<br/><div class="code-div">replace ' \
                               'github.com/' + self.repo_c.repo_name + ' => ' + self.repo_c.mod_name + version_str
                s_30_33_str += '</div><br/>'
                if d_msg_list[0] > 0:
                    if d_msg_list[0] >= 2:
                        usr_str = 'users'
                    else:
                        usr_str = 'user'
                    s_30_33_str += '[*] You can see which module-aware downstream projects will be affected here: (<em>'
                    s_30_33_str += str(d_msg_list[0]) + ' module</em> ' + usr_str + ', e.g.'
                    if d_msg_list[0] >= 3:
                        if len(d_msg_list[4]) >= 3:
                            s_30_33_str += ', ' + d_msg_list[4][0] + ', ' + d_msg_list[4][1] + ', ' + d_msg_list[4][2]
                            s_30_33_str += ')<br/>'
                        else:
                            for d in d_msg_list[4]:
                                s_30_33_str = s_30_33_str + ', ' + d
                            s_30_33_str += ')<br/>'
                    else:
                        for d in d_msg_list[4]:
                            s_30_33_str = s_30_33_str + ', ' + d
                        s_30_33_str += ')<br/>'
                    for u in range(0, len(d_msg_list[1])):
                        if len(d_msg_list[1]) == 1:
                            link_str = 'LINK'
                        else:
                            link_str = 'LINK-' + str(u + 1)
                        s_30_33_str = s_30_33_str + '<a href="' + d_msg_list[1][u] + '">' + link_str + '</a>&nbsp;&nbsp;&nbsp;&nbsp;'

                s_30_33_str += '<br/>'
                if [r_30_33_str, s_30_33_str, order_list.index('3-0=3-3')] not in report_list:
                    report_list.append([r_30_33_str, s_30_33_str, order_list.index('3-0=3-3')])
            if b[0] == '3-0' and b[1] == '3-2':
                if len(b[2].split('@')) >= 2:
                    repo_name = b[2].split('@')[0]
                    version_str = b[2].split('@')[1]
                else:
                    if self.repo_c.v_name:
                        version_str = self.repo_c.v_name
                    else:
                        version_str = self.repo_c.v_hash
                r_30_32_str = '<h3>ISSUE Type C.b</h3>Project <em> ' + self.repo_c.repo_name + ' </em> already supports'
                r_30_32_str += ' Go modules. But sadly, the version tag <em> ' + version_str + ' </em> doesn\'t '
                r_30_32_str += 'follow <a href="https://semver.org/">Semantic Versioning</a>(the MAJOR.MINOR.PATCH ' \
                               'format), which means that the version tag will be ignored by Go modules and replaced ' \
                               'by pseudo-version when downstream module users try to get this version. ' \
                               'Pseudo-version is not very readable. It’s hard to verify which version is in use. ' \
                               'This is not conducive to version control.<br/>'
                s_30_32_str = '<h3>Fix configuration items to follow Semantic Import Versioning rules.</h3>' \
                              'Release version tags which follow Semantic Import Versioning rules, for example, ' \
                              'v1.0.1, v2.0.0, v3.1.0-alpha, v3.1.0-beta.2etc.<br/>'
                if d_msg_list[0] > 0:
                    if d_msg_list[0] >= 2:
                        usr_str = 'users'
                    else:
                        usr_str = 'user'
                    s_30_32_str += '[*] You can see which module-aware downstream projects will be affected here: (<em>'
                    s_30_32_str += str(d_msg_list[0]) + ' module</em> ' + usr_str + ', e.g.'
                    if d_msg_list[0] >= 3:
                        if len(d_msg_list[4]) >= 3:
                            s_30_32_str += ', ' + d_msg_list[4][0] + ', ' + d_msg_list[4][1] + ', ' + d_msg_list[4][2]
                            s_30_32_str += ')<br/>'
                        else:
                            for d in d_msg_list[4]:
                                s_30_32_str = s_30_32_str + ', ' + d
                            s_30_32_str += ')<br/>'
                    else:
                        for d in d_msg_list[4]:
                            s_30_32_str = s_30_32_str + ', ' + d
                        s_30_32_str += ')<br/>'
                    for u in range(0, len(d_msg_list[1])):
                        if len(d_msg_list[1]) == 1:
                            link_str = 'LINK'
                        else:
                            link_str = 'LINK-' + str(u + 1)
                        s_30_32_str = s_30_32_str + '<a href="' + d_msg_list[1][u] + '">' + link_str + '</a>&nbsp;&nbsp;&nbsp;&nbsp;'

                s_30_32_str += '</br>'
                if [r_30_32_str, s_30_32_str, order_list.index('3-0=3-2')] not in report_list:
                    report_list.append([r_30_32_str, s_30_32_str, order_list.index('3-0=3-2')])
            if b[0] == '2' and b[1] == '2-2':
                s_name_exit = 1
                if len(b[2].split('[')) >= 2:
                    dep_u_name = 'github.com/' + b[2].split('[')[0]  # old path
                    dep_s_name = 'github.com/' + b[2].split('[')[1].replace(']', '')  # new path
                    if not dep_s_name:
                        s_name_exit = 0
                elif len(b[2].split('@')) >= 2:
                    dep_u_name = b[2].split('@')[0]  # old path
                    dep_s_name = b[2].split('@')[1]  # new path
                    if dep_s_name == '0':
                        s_name_exit = 0
                else:
                    dep_u_name = b[2].replace('@', '')
                    dep_s_name = '0'
                    s_name_exit = 0
                if s_name_exit == 1:
                    r_22_22_str = 'This project <em>' + self.repo_c.repo_name + '</em> depends on '
                    r_22_22_str += '<em>' + dep_s_name + '</em> which already opted into module and redirects(or rename) ' \
                                                         'its import path from <em> "' + dep_u_name
                    r_22_22_str += '" </em> to <em> "' + dep_s_name
                    r_22_22_str += '" </em>. You import <em>' + dep_s_name + '</em> through the old path '
                    r_22_22_str += '<em> "' + dep_u_name + '" </em>. But when downstream module users '
                    r_22_22_str += 'try to get <em>' + dep_s_name + '</em> through the indirect path ' \
                                                                    '<em> "' + dep_u_name
                    r_22_22_str += '"</em> from <em>' + self.repo_c.repo_name + '</em>, they will easily get build errors:<br/>'
                    r_22_22_str += '<div class="code-div"> > go get: ' + dep_u_name
                    r_22_22_str += ' : parsing go.mod:<br/> > module declares its path as: ' + dep_s_name
                    r_22_22_str += '<br/> > but was required as: ' + dep_u_name + '<br/></div><br/>'
                    s_22_22_str = '<h3>Update import paths.</h3>Replace all the old import paths, replace ' \
                                  '"' + dep_u_name + '" with "' + dep_s_name + '".<br/>'
                else:
                    r_22_22_str = 'This project <em>' + self.repo_c.repo_name + '</em> depends on '
                    r_22_22_str += '<em>' + dep_u_name + '</em> which already be redirected(or rename) or deleted ' \
                                                         'its import path <em> "' + dep_u_name + '" </em>'
                    r_22_22_str += '. You import <em>' + dep_u_name + '</em> through the old path '
                    r_22_22_str += '<em> "' + dep_u_name + '" </em>. But when downstream module users '
                    r_22_22_str += 'try to get <em>' + dep_u_name + '</em> through the indirect path ' \
                                                                    '<em> "' + dep_u_name
                    r_22_22_str += '"</em> from <em>' + self.repo_c.repo_name + '</em>, they will easily get build '
                    r_22_22_str += 'errors.<br/>'
                    s_22_22_str = '<h3>Update import paths.</h3>Replace all the old import paths, or change ' \
                                  'the dependencies.<br/>'
                # https://github.com/remp2020/remp/search?q=github.com%2FSirupsen%2Flogrus
                link_url_str = 'https://github.com/' + self.repo_c.repo_name + '/search?q='
                link_url_str += dep_u_name.replace('github.com/', '').replace('/', '%2F')
                s_22_22_str += 'Where did you import it: <br/><a href="' + link_url_str + '">LINK</a><br/>'
                r_22_22_list.append(r_22_22_str)
                s_22_22_list.append(s_22_22_str)
            if b[0] == '1-1':
                if b[2] not in r_11_list:
                    r_11_list.append(b[2])
            if b[0] == '2' and b[1] == '2-1':
                if len(b[2].split('=')) >= 2:
                    if b[2] not in r_21_21_list:
                        r_21_21_list.append(b[2])
                else:
                    if b[2] not in r_21_list:
                        r_21_list.append(b[2])
            if b[0] == '2' and b[1] == '2-3' and (b[2] not in r_23_list):
                r_23_list.append(b[2])

        if r_22_22_list:
            r_22_22_str = '<h3>ISSUE Type B.b :</h3>'
            s_22_22_str = ''
            for r in r_22_22_list:
                r_22_22_str = r_22_22_str + r + '<br/><br/>'
            for s in s_22_22_list:
                s_22_22_str = s_22_22_str + s + '<br/><br/>'
            r_22_22_str.strip('<br/><br/>') + '<br/>'

            if d_msg_list[0] > 0:
                if d_msg_list[0] >= 2:
                    usr_str = 'users'
                else:
                    usr_str = 'user'
                s_22_22_str += '[*] You can see which module-aware downstream projects will be affected here: (<em>'
                s_22_22_str += str(d_msg_list[0]) + ' module</em> ' + usr_str + ', e.g.'
                if d_msg_list[0] >= 3:
                    if len(d_msg_list[4]) >= 3:
                        s_22_22_str += ', ' + d_msg_list[4][0] + ', ' + d_msg_list[4][1] + ', ' + d_msg_list[4][2]
                        s_22_22_str += ')<br/>'
                    else:
                        for d in d_msg_list[4]:
                            s_22_22_str = s_22_22_str + ', ' + d
                        s_22_22_str += ')<br/>'
                else:
                    for d in d_msg_list[4]:
                        s_22_22_str = s_22_22_str + ', ' + d
                    s_22_22_str += ')<br/>'
                for u in range(0, len(d_msg_list[1])):
                    if len(d_msg_list[1]) == 1:
                        link_str = 'LINK'
                    else:
                        link_str = 'LINK-' + str(u + 1)
                    s_22_22_str = s_22_22_str + '<a href="' + d_msg_list[1][u] + '">' + link_str + '</a>&nbsp;&nbsp;&nbsp;&nbsp;'

                s_22_22_str += '<br/>'
            else:
                s_22_22_str.strip('<br/><br/>') + '<br/>'
            if [r_22_22_str, s_22_22_str, order_list.index('2-2=2-2')] not in report_list:
                report_list.append([r_22_22_str, s_22_22_str, order_list.index('2-2=2-2')])
        if r_11_list:
            r_11_str = '<h3>ISSUE Type A :</h3><h6>(This issue report warns you against the possible ' \
                       'problems when you try to upgrade the following dependencies.)</h6><em>' + self.repo_c.repo_name
            r_11_str += '</em> is module-unaware, and depends on projects: '
            r_list = []
            v_list = []
            for r in r_11_list:
                r_c = 0
                if len(r.split('@')) >= 2:
                    if len(r.split('@')) >= 3:
                        old_name = r.split('@')[2]
                        if old_name:
                            r_11 = old_name + '(now moved to : ' + r.split('@')[0] + ')'
                            if r_11 not in r_list:
                                r_list.append(r_11)
                                r_c = 1
                        else:
                            r_11 = r.split('@')[0]
                            if r_11 not in r_list:
                                r_list.append(r_11)
                                r_c = 1
                    else:
                        r_11 = r.split('@')[0]
                        if r_11 not in r_list:
                            r_list.append(r_11)
                            r_c = 1
                    if r_c:
                        v_list.append(r.split('@')[1])

            for r in r_list:
                r_11_str = r_11_str + '<em>' + r + '</em> ,'
            r_11_str = r_11_str.strip(',') + ' . <em>Build errors</em> will occur when upgrading these upstream ' \
                                             'projects, because these projects:<br/>'
            r_11_str += '1.	Add Go modules in the recent versions.<br/>2. Comply with the specification ' \
                        'of "Releasing Modules for v2 or higher" available in the Modules documentation.<br/>' \
                        '3.	Have the virtual paths with version suffixes (i.e., v2+), which cannot identified by ' \
                        'the module-unaware projects using legacy Golang versions or dependency manage tools (e.g., ' \
                        'dep, glide, govendor, etc.).<br/>See <a href="https://github.com/golang/dep/issues/1962">' \
                        'golang/dep#1962</a>&nbsp;&nbsp;&nbsp;&nbsp;<a href="https://github.com/golang/dep/issues' \
                        '/2139">golang/dep#2139<a> .<br/>'
            s_11_str = '<h3>1. Migrate to Go Modules.</h3><span class="b_class">Benefit:</span> This solution ' \
                       'encourages migration from GOPATH to Go Modules. (Go Modules is the general trend of ' \
                       'ecosystem. Migrating to Go Modules is a good choice for you to get a better upgrade package ' \
                       'experience.)<br/><span class="c_class">Cost:</span> This solution will break compatibility ' \
                       'with downstream projects without module awareness. (Migrating to modules will be accompanied ' \
                       'by the introduction of virtual paths. Thus the module-unaware downstream projects might ' \
                       'get build errors.)<br/>'
            if d_msg_list[2] > 0:
                if d_msg_list[2] >= 2:
                    usr_str = 'users'
                else:
                    usr_str = 'user'
                s_11_str += '[*] You can see which module-unaware downstream projects will be affected: (<em>'
                s_11_str += str(d_msg_list[2]) + ' module-unaware</em> ' + usr_str + ', e.g.'
                if d_msg_list[2] >= 3:
                    if len(d_msg_list[5]) >= 3:
                        s_11_str += ', ' + d_msg_list[5][0] + ', ' + d_msg_list[5][1] + ', ' + d_msg_list[5][2]
                        s_11_str += ')<br/>'
                    else:
                        for d in d_msg_list[5]:
                            s_11_str = s_11_str + ', ' + d
                        s_11_str += ')<br/>'
                else:
                    for d in d_msg_list[5]:
                        s_11_str = s_11_str + ', ' + d
                    s_11_str += ')<br/>'
                for u in range(0, len(d_msg_list[3])):
                    if len(d_msg_list[3]) == 1:
                        link_str = 'LINK'
                    else:
                        link_str = 'LINK-' + str(u + 1)
                    s_11_str = s_11_str + '<a href="' + d_msg_list[3][u] + '">' + link_str + '</a>&nbsp;&nbsp;&nbsp;&nbsp;'
            s_11_str += '<h4>2. Maintain v2+ libraries in Go Modules in your Vendor directory rather than ' \
                        'reference them by virtual import paths.</h4>Manually download the dependencies into your ' \
                        'vendor directory and do compatibility dispose(<em>Materialize the virtual path</em> or ' \
                        '<em>Delete the virtual part of the path</em>). <br/><span class="b_class">Benefit:</span> ' \
                        'Making a copy of libraries in your Vendor directory can avoid virtual import paths.<br/>' \
                        '<span class="c_class">Cost:</span> Your downstream module unaware projects have to ' \
                        'make a copy of your Vendor directory, causing extra maintenance overhead to downstream ' \
                        'projects. Meanwhile, as the import paths have different meanings for  module aware ' \
                        'projects and module unaware projects, materializing the virtual path is a better ' \
                        'way to solve the issue, while ensuring compatibility with downstream module users. ' \
                        'Deleting the virtual part of the path will hurt your downstream module users.<br/>'
            if d_msg_list[0] > 0:
                if d_msg_list[0] >= 2:
                    usr_str = 'users'
                else:
                    usr_str = 'user'
                s_11_str += '[*] You can see which module-unaware downstream projects will be affected:  (<em>'
                s_11_str += str(d_msg_list[0]) + ' module</em> ' + usr_str + ', e.g.'
                if d_msg_list[0] >= 3:
                    if len(d_msg_list[4]) >= 3:
                        s_11_str += ', ' + d_msg_list[4][0] + ', ' + d_msg_list[4][1] + ', ' + d_msg_list[4][2]
                        s_11_str += ')<br/>'
                    else:
                        for d in d_msg_list[4]:
                            s_11_str = s_11_str + ', ' + d
                        s_11_str += ')<br/>'
                else:
                    for d in d_msg_list[4]:
                        s_11_str = s_11_str + ', ' + d
                    s_11_str += ')<br/>'
                for u in range(0, len(d_msg_list[1])):
                    if len(d_msg_list[1]) == 1:
                        link_str = 'LINK'
                    else:
                        link_str = 'LINK-' + str(u + 1)
                    s_11_str = s_11_str + '<a href="' + d_msg_list[1][u] + '">' + link_str + '</a>&nbsp;&nbsp;&nbsp;&nbsp;'
            s_11_str += '<br/>'
            if [r_11_str, s_11_str, order_list.index('1-1')] not in report_list:
                report_list.append([r_11_str, s_11_str, order_list.index('1-1')])
        if r_21_list:
            r_list = []
            v_list = []
            for r in r_21_list:
                if len(r.split('@')) >= 2:
                    if r.split('@')[0] not in r_list:
                        r_list.append(r.split('@')[0])
                        v_list.append(r.split('@')[1])
            if r_list:
                project_name = r_list[0].replace('github.com/', '')
                path_name = 'github.com/' + r_list[0].replace('github.com/', '')
                if v_list[0] != '0' and v_list[0]:
                    r_21_21_str = '<h3>ISSUE Type B.a :</h3><em>' + self.repo_c.repo_name
                    r_21_21_str += '</em> has already opted into module and indirectly depends on <em>' + project_name
                    r_21_21_str += '</em> from a GOPATH project. And project <em>' + project_name
                    r_21_21_str += '</em> already opted into module and and redirects(or rename) its import path ' \
                                   'from <em> "' + path_name + '" </em> to <em> "' + v_list[0]
                    r_21_21_str += '" </em>. You indirectly import <em>' + project_name + '</em> through the old '
                    r_21_21_str += 'path <em> "' + path_name + '" </em> from a GOPATH project. In this case, you ' \
                                                               'will easily get build errors:<br/>'
                    r_21_21_str += '<div class="code-div"> > go get: ' + path_name
                    r_21_21_str += ' : parsing go.mod:<br/> > module declares its path as: ' + v_list[0]
                    r_21_21_str += '<br/> > but was required as: ' + path_name + '<br/></div><br/>"'

                    if len(r_list) >= 1:
                        r_21_21_str += 'Same to these indirect dependencies:'
                        for i in range(1, len(r_list)):
                            r_21_21_str += ' <em>' + r_list[i].replace('github.com/', '') + '</em> ,'
                        r_21_21_str = r_21_21_str.strip(',') + '.<br/>'
                else:
                    r_21_21_str = '<h3>ISSUE Type B.a :</h3><em>' + self.repo_c.repo_name
                    r_21_21_str += '</em> has already opted into module and indirectly depends on <em>' + project_name
                    r_21_21_str += '</em> through a GOPATH project. And project <em>' + project_name
                    r_21_21_str += '</em> already opted into module and redirected(or rename) or deleted its ' \
                                   'import path <em> "' + path_name + '" </em>. You indirectly import <em>'
                    r_21_21_str += project_name + '</em> through the old path <em> "' + path_name
                    r_21_21_str += '" </em> from a GOPATH project. In this case, you will easily get build ' \
                                   'errors(Cannot find package).'
                    if len(r_list) >= 1:
                        r_21_21_str += 'Same to these indirect dependencies:'
                        for i in range(1, len(r_list)):
                            r_21_21_str += ' <em>' + r_list[i].replace('github.com/', '') + '</em> ,'
                        r_21_21_str = r_21_21_str.strip(',') + '.<br/>'

                s_21_21_str = '<h3>Add a replace directive in your go.mod files, replace all the old import paths.</h3>'

                if [r_21_21_str, s_21_21_str, order_list.index('2-1=2-1')] not in report_list:
                    report_list.append([r_21_21_str, s_21_21_str, order_list.index('2-1=2-1')])
        if r_21_21_list or r_23_list:
            r_list = []
            v_list = []
            aready_fixed = 0
            if r_21_21_list:
                for r in r_21_21_list:
                    if len(r.split('=')) >= 2:
                        if r.split('=')[0] not in r_list:
                            r_list.append(r.split('=')[0])
                            v_list.append(r.split('=')[1])
            else:
                aready_fixed = 1
                for r in r_23_list:
                    if len(r.split('=')) >= 2:
                        if r.split('=')[0] not in r_list:
                            r_list.append(r.split('=')[0])
                            v_list.append(r.split('=')[1])
            if r_list:
                if len(r_list[0].split('@')) >= 2:
                    p_name = r_list[0].split('@')[0]
                    p_version = r_list[0].split('@')[1]
                else:
                    p_name = r_list[0].replace('@', '')
                    p_version = ''
                if len(v_list[0].split('@')) >= 2:
                    p_mode_path = v_list[0].split('@')[0]
                    p_new_version = v_list[0].split('@')[1]
                else:
                    p_mode_path = v_list[0].replace('@', '')
                    p_new_version = ''
                project_name = p_name.replace('github.com/', '')
                path_name = 'github.com/' + p_name.replace('github.com/', '')
                if aready_fixed:
                    r_a_f = '<h3>** Already Fixed **</h3>'
                else:
                    r_a_f = ''
                r_21_21_str = '<h3>ISSUE Type B.a :</h3><em>' + self.repo_c.repo_name
                r_21_21_str += '</em> has already opted into module and indirectly depends on <em>' + project_name
                r_21_21_str += '</em> through a GOPATH project. And project <em>' + project_name
                r_21_21_str += '</em> already opted into module and released a v2+ version with the major branch ' \
                               'strategy. The latest module path of <em>' + project_name
                r_21_21_str += '</em> is <em> "' + p_mode_path + '" </em>. From module-unaware project\'s '
                r_21_21_str += 'perspective, it interprets the import path <em> "' + path_name + '" </em> as '
                r_21_21_str += project_name + '\'s latest version. But from the Go Modules\' point of view, '
                r_21_21_str += 'path <em> "' + path_name + '" </em> equals to version v0/v1 or the latest version ' \
                                                           'that doesn’t use the module. So when you try to get <em>'
                r_21_21_str += project_name + '</em> through the indirect path <em> "' + path_name
                r_21_21_str += '" </em> which comes from module-unaware project, the module pulls the old ' \
                               'version of ' + project_name + ' , ' + v_list[0] + ' . This causes version of '
                r_21_21_str += project_name + ' , which you are dependent on, sticked at the old version '
                r_21_21_str += project_name + ' .<br/>'
                if len(r_list) >= 1:
                    r_21_21_str += 'Same to these indirect dependencies:'
                    for i in range(1, len(r_list)):
                        r_21_21_str += ' <em>' + r_list[i].replace('github.com/', '').replace('@', ' ') + '</em> ,'
                    r_21_21_str = r_21_21_str.strip(',') + '.<br/>'

                s_21_21_str = '<h3>Add a replace directive in your go.mod files with version information to avoid ' \
                              'sticking at the old version.</h3>'
                r_21_21_str = r_a_f + r_21_21_str
                s_21_21_str = r_a_f + s_21_21_str
                if [r_21_21_str, s_21_21_str, order_list.index('2-1=2-1')] not in report_list:
                    report_list.append([r_21_21_str, s_21_21_str, order_list.index('2-1=2-1')])
        report_list = sorted(report_list, key=lambda x: x[2])
        if not report_list:
            report_list.append(['no issue', 'no solution', 10])
        return report_list[0]

    def get_updated_report(self, old_repo_name, d_msg_list):
        order_list = ['3-0=3-1', '3-0=3-3', '2-1=2-1', '2-2=2-2', '1-1', '3-0=3-2']
        if self.repo_c.v_name:
            version_str = self.repo_c.v_name
        else:
            version_str = self.repo_c.v_hash
        r_30_33_str = '<h3>ISSUE Type C.c :</h3>Module path in your go.mod file is inconsistent with ' \
                      'your URL on the hosting site. Module path is <em> "' + self.repo_c.mod_name
        r_30_33_str += '" </em>, but URL on the hosting site is <em> "github.com/' + old_repo_name
        r_30_33_str += '" </em>. Running <em>go get github.com/' + old_repo_name
        r_30_33_str += '</em> with GO111MODULE=on, will get the following errors:<br/><div class="code-div">' \
                       ' > go get: github.com/' + old_repo_name + '@' + version_str
        r_30_33_str += ': parsing go.mod:<br/> > module declares its path as: ' + self.repo_c.mod_name
        r_30_33_str += '<br/> > but was required as: github.com/' + old_repo_name + '</div><br/>'
        s_30_33_str = '<h3>1. Fix configuration items to follow Semantic Import Versioning rules.</h3>' \
                      'Fix your module path: Rename module path to be <em> "github.com/' \
                      + old_repo_name
        s_30_33_str += '" </em>.<h4>2. Suggest downstream module users use a replace directive to ' \
                       'replace the original import path and avoid errors.</h4>Downstream module users ' \
                       'add this replace directive in their go.mod files:<br/><div class="code-div">replace ' \
                       'github.com/' + old_repo_name + ' => ' + self.repo_c.mod_name + version_str
        s_30_33_str += '</div><br/>'
        if d_msg_list[0] > 0:
            if d_msg_list[0] >= 2:
                usr_str = 'users'
            else:
                usr_str = 'user'
            s_30_33_str += '[*] You can see which module-aware downstream projects will be affected here: (<em>'
            s_30_33_str += str(d_msg_list[0]) + ' module</em> ' + usr_str + ', e.g.'
            if d_msg_list[0] >= 3:
                if len(d_msg_list[4]) >= 3:
                    s_30_33_str += ', ' + d_msg_list[4][0] + ', ' + d_msg_list[4][1] + ', ' + d_msg_list[4][2]
                    s_30_33_str += ')<br/>'
                else:
                    for d in d_msg_list[4]:
                        s_30_33_str = s_30_33_str + ', ' + d
                    s_30_33_str += ')<br/>'
            else:
                for d in d_msg_list[4]:
                    s_30_33_str = s_30_33_str + ', ' + d
                s_30_33_str += ')<br/>'
            for u in range(0, len(d_msg_list[1])):
                if len(d_msg_list[1]) == 1:
                    link_str = 'LINK'
                else:
                    link_str = 'LINK-' + str(u + 1)
                s_30_33_str = s_30_33_str + '<a href="' + d_msg_list[1][u] + '">' + link_str + '</a>&nbsp;&nbsp;&nbsp;&nbsp;'
        s_30_33_str += '<br/>'
        return [r_30_33_str, s_30_33_str, order_list.index('3-0=3-3')]

    def insert_repo(self):
        d_sql = self.repo_c.insert_repo()
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
                # 执行sql语句
                insert_cursor.execute(insert_sql)
                db.commit()
                insert_cursor.close()
                print('insert ', insert_db, ' successful', self.repo_name, self.v_name, self.v_hash)
                self.insert_s = self.insert_s + 1
            except Exception as exp:
                print('insert ', insert_db, ' error exception is:', exp)
                print('insert ', insert_db, ' error sql:', insert_sql)
                self.insert_e = self.insert_e + 1
                # 发生错误时回滚
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
                # print(update_sql)
                sql = update_sql
                try:
                    update_cursor = db.cursor()
                    # 执行sql语句
                    update_cursor.execute(update_sql)
                    db.commit()
                    update_cursor.close()
                    # print('update ', insert_db, ' successful', self.repo_name, self.v_name, self.v_hash)
                    self.update_s = self.update_s + 1
                except Exception as exp:
                    print('update ', insert_db, ' error exception is:', exp)
                    print('update ', insert_db, ' error sql:', update_sql)
                    self.update_e = self.update_e + 1
                    # 发生错误时回滚
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

    def get_e_s_param(self):
        return self.search_e, self.insert_e, self.insert_s, self.update_e, self.update_s

