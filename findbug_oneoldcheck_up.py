# 从旧机制检测代码复制至此，修改了插入至need_check_fo这部分的代码
import base64
import json
import re
import time
from concurrent.futures.thread import ThreadPoolExecutor
from urllib.request import Request, urlopen
import pymysql

from findbug_onenewcheck_api import check_bug_new_repo, insert_replace, get_releases_url, get_go_mod_detail
from findbug_onenewcheck_api import check_path_real, check_go_mod_detail, insert_replace
from findbug_oneoldcheck_public import get_source_code,
from findchange_api import judge_repo_type, get_go_mod_detail, get_version
from find_local_use import get_local_use
from find_upstream_api import get_up_repo
# from one_check_api.findbug_onenewcheck_api import check_bug_new_repo
# # from one_check_api.findchange_api import judge_repo_type, get_go_mod_detail
# from one_check_api.find_local_use import get_local_use
# from one_check_api.findchange_api import get_go_mod_detail
# from one_check_api.find_upstream_api import get_up_repo
# from one_check_api.findbug_oneoldcheck_api import get_source_code, search_repo
# from one_check_api.findchange_api import get_version
from find_upstream_api import check_name_change


def get_results(url, headers):
    request = Request(url, headers=headers)
    response = urlopen(request).read()
    result = json.loads(response.decode())
    # time
    return result


# 从旧机制检测代码复制至此，修改了插入至need_check_fo这部分的代码
def check_bug_old_repo_fo(fullname, name, semantic, bug_type_num, bug_list, break_type_num, break_list, headers,
                          issue, time_w, host, user, password, db_name, insert_e, search_e, check_e, update_e, insert_s,
                          update_s, check_type, db_id, db_check):
    last_tim = 0
    now_name = check_name_change(fullname, host, user, password, db_name)
    if now_name:
        fullname = now_name
    # 找到vendor文件夹，以及出了vendor文件夹外的所有的文件路径
    (import_list, dir_name_list, vendor_list) = get_source_code(fullname, name, semantic, headers, time_w)
    # 获取上游repos
    (imp_final_siv_list, imp_final_list, insert_e, search_e, check_e, update_e, insert_s, update_s,
     issue) = get_up_repo(import_list, dir_name_list, vendor_list, fullname, host, user, password, db_name,
                          time_w, insert_e, search_e, check_e, update_e, insert_s, update_s, issue)
    for imp_siv in imp_final_siv_list:
        # 问题1-2，A，已经发生
        break_type_num[0] = break_type_num[0] + 1
        break_list[0] = break_list[0] + '$' + '1.2' + ':' + imp_siv
    for imp in imp_final_list:
        imp_mod = re.findall(r"^([^/]+?/[^/]+?)/.+?", imp)
        if imp_mod:  # 说明是子模块的导入路径
            imp_mod_name = imp_mod[0]
        else:
            imp_mod_name = imp
        print('开始正常检测：')
        bu = 0
        # 针对新用户，未来更新时会发生的bug，检测该包的最新版本
        (i_v_name, i_semantic, issue) = get_releases_url(imp_mod_name, headers, issue)
        (imp_mod_name, sub_mod_path, imp_siv, repo_version, v_siv, result, go_mod, go_mod_url, v_dir_url,
         issue) = check_path_real(imp, i_v_name, headers, issue)
        l_1 = [8, 5, -8, -5]  # -8, -5
        if result in l_1:  # siv为实体路径，旧机制可以获取到
            if go_mod == 2:
                path_match = check_go_mod_detail(imp_mod_name, sub_mod_path, imp_siv, v_siv, go_mod_url, headers)
                if path_match != 2:
                    # 问题4-0，D，已经发生
                    bug_type_num[6] = bug_type_num[6] + 1
                    bug_list[6] = bug_list[6] + '$' + imp_mod_name + ' ' + i_v_name
                    bu = 4
                    print('[8,5]问题4-0', imp + ' ' + i_v_name)
        l_2 = [7, 6, 4, -7, -6, -4]  # , -7, -6, -4
        if result in l_2:
            # 问题1-1，A，旧用户升级预警
            bug_type_num[1] = bug_type_num[1] + 1
            bug_list[1] = bug_list[1] + '$' + '1.1' + ':' + imp + ' ' + i_v_name
            print('[7]问题1-1', imp + ' ' + i_v_name)
            if go_mod == 2:
                path_match = check_go_mod_detail(imp_mod_name, sub_mod_path, imp_siv, v_siv, go_mod_url, headers)
                if path_match == 1:
                    # 问题3-0，C，下游新用户升级预警
                    bug_type_num[4] = bug_type_num[4] + 1
                    bug_list[4] = bug_list[4] + '$' + imp_mod_name + ' ' + i_v_name
                    bu = 3
                    print('[7]问题3-0', imp + ' ' + i_v_name)
                elif path_match == 0:
                    # 问题4-0，D，下游新用户升级预警
                    bug_type_num[6] = bug_type_num[6] + 1
                    bug_list[6] = bug_list[6] + '$' + imp_mod_name + ' ' + i_v_name
                    bu = 4
                    print('[7]问题4-0', imp + ' ' + i_v_name)

        l_3 = [3, 2, 1, -3, -2]  # -3, -2, -1
        if result in l_3:
            if result == 2:
                # 问题1-1，A，旧用户升级预警
                bug_type_num[1] = bug_type_num[1] + 1
                bug_list[1] = bug_list[1] + '$' + '1.1' + ':' + imp_mod_name + ' ' + i_v_name
                print('[3]问题1-1', imp + ' ' + i_v_name)
            if go_mod == 2:
                path_match = check_go_mod_detail(imp_mod_name, sub_mod_path, imp_siv, v_siv, go_mod_url, headers)
                if int(v_siv) >= 2 and path_match == 1:
                    # 问题3-0，C，下游新用户升级预警
                    bug_type_num[4] = bug_type_num[4] + 1
                    bug_list[4] = bug_list[4] + '$' + imp_mod_name + ' ' + i_v_name
                    bu = 3
                    print('[3]问题3-0', imp + ' ' + i_v_name)
                elif path_match == 0 and result != 2:
                    # 问题4-0，D，下游新用户升级预警
                    bug_type_num[6] = bug_type_num[6] + 1
                    bug_list[6] = bug_list[6] + '$' + imp_mod_name + ' ' + i_v_name
                    bu = 4
                    print('[3]问题4-0', imp + ' ' + i_v_name)

        # (r_version_number_new, r_path_match_new,
        #  issue) = get_go_mod_detail(imp_mod_name, i_v_name, i_semantic, headers, issue)
        # print('针对新用户的检测：【当前】', r_version_number_new, r_path_match_new)
        # # 判断依赖项是否有go.mod文件，path_match=-1
        # if r_path_match_new != -1:
        #     # 判断版本号是否为>=2的整数且与模块路径的语义版本不一致
        #     if r_path_match_new == 1:
        #         # 问题3-0，C，下游新用户升级预警
        #         bug_type_num[4] = bug_type_num[4] + 1
        #         bug_list[4] = bug_list[4] + '$' + imp_mod_name + ' ' + i_v_name
        #         bu = 3
        #     elif r_path_match_new == 2 and r_version_number_new == 2:
        #         # 问题2-0，B，下游新用户升级预警
        #         bug_type_num[2] = bug_type_num[2] + 1
        #         bug_list[2] = bug_list[2] + '$' + imp_mod_name + ' ' + i_v_name
        #         bu = 2
        #     elif r_path_match_new == 0:
        #         # 问题4-0，D，下游新用户升级预警
        #         bug_type_num[6] = bug_type_num[6] + 1
        #         bug_list[6] = bug_list[6] + '$' + imp_mod_name + ' ' + i_v_name
        #         bu = 4

        if db_check == 0:
            print('检测是否有传递依赖，查询repo_impact库')
            # 0, prob_list, '', '', -1  查询repo_impact库
            (search_r, r_list, r_update, r_vname, r_gomod) = search_repo(imp_mod_name, host, user, password, db_name)
            if search_r == 2:
                for r in r_list:
                    if r == '1-1':
                        # 问题1-1，A，旧用户升级预警
                        bug_type_num[1] = bug_type_num[1] + 1
                        bug_list[1] = bug_list[1] + '$' + '1.1' + ':' + imp_mod_name + ' ' + r_vname
                        print('db get bug 1-1:', imp + ' ' + r_vname)
                    elif r == '2-0':
                        # 问题2-0，B，下游新用户升级预警
                        bug_type_num[2] = bug_type_num[2] + 1
                        if bu != 2:
                            bug_list[2] = bug_list[2] + '$' + imp_mod_name + ' ' + r_vname
                            print('db get bug 2-0:', imp + ' ' + r_vname)
                    elif r == '3-0':
                        # 问题3-0，C，下游新用户升级预警
                        bug_type_num[4] = bug_type_num[4] + 1
                        if bu != 3:
                            bug_list[4] = bug_list[4] + '$' + imp_mod_name + ' ' + r_vname
                            print('db get bug 3-0:', imp + ' ' + r_vname)
                    elif r == '4-0':
                        # 问题4-0，D，下游新用户升级预警
                        bug_type_num[6] = bug_type_num[6] + 1
                        if bu != 4:
                            bug_list[6] = bug_list[6] + '$' + imp_mod_name + ' ' + r_vname
                            print('db get bug 4-0:', imp + ' ' + r_vname)
            elif search_r == 1:
                print('db get 没问题:', imp + ' ' + r_vname)
            else:
                # 存库 need_check_fo  db
                # 解析check_type： check_type = '[o]' + r[3] + '@' + r[4]
                imp_version = '-1'
                get_type = re.findall(r"(.+?)@\d$", check_type)
                get_layer = re.findall(r"@(\d)$", check_type)
                if get_type and get_layer:
                    from_type = get_type[0].replace('[o]', '')
                    layer = get_layer[0]
                else:
                    (from_type, layer) = get_need_check_info(host, user, password, db_name, db_id)

                d_repo = fullname + '@' + name
                now_tim_str = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
                now_tim = int(now_tim_str)
                if last_tim == now_tim:
                    time.sleep(1)
                    last_tim = now_tim
                else:
                    last_tim = now_tim

                (insert_e, check_e) = insert_need_check_fo(imp_mod_name, imp_version, from_type, d_repo, layer, host,
                                                           user, password, db_name, insert_e, check_e, now_tim)
        else:  # check_type == 1
            # 存库 need_check_fo  db
            imp_version = '-1'
            get_type = re.findall(r"^\[o\](.+?)@\d$", check_type)
            get_layer = re.findall(r"@(\d)$", check_type)
            if get_type and get_layer:
                from_type = get_type[0]
                layer = get_layer[0]
            else:
                (from_type, layer) = get_need_check_info(host, user, password, db_name, db_id)

            d_repo = fullname + '@' + name
            now_tim_str = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
            now_tim = int(now_tim_str)
            if last_tim == now_tim:
                time.sleep(1)
                last_tim = now_tim
            else:
                last_tim = now_tim
            (insert_e, check_e) = insert_need_check_fo(imp_mod_name, imp_version, from_type, layer, d_repo, host,
                                                       user, password, db_name, insert_e, check_e, now_tim)
    return (bug_type_num, bug_list, break_type_num, break_list, insert_e, search_e, check_e, update_e, insert_s,
            update_s, issue)


# 通过id号获取上游旧机制信息，依赖关系层数
def get_need_check_info(host, user, password, db_name, db_id):
    from_type = '-1'
    layer = 0
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT from_type,layer FROM need_check_fo WHERE id='%d'" % db_id
    db = pymysql.connect(host, user, password, db_name)
    try:
        # 执行sql语句
        check_cursor = db.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        if check_result:
            from_type = check_result[0][0]
            layer = check_result[0][1]
    except Exception as exp:
        print("check need_check_fo error:【", db_id, '】', exp, '****************************************?????????'
                                                              '???????????********')
        # 发生错误时回滚
        db.rollback()
    db.close()
    return from_type, layer


# 存库 need_check_fo  db
def insert_need_check_fo(full_name, imp_version, from_type, d_repo, layer_str, host, user, password, db_name, insert_e,
                         check_e, time_num):
    layer = int(layer_str) + 1
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT id,bug_update FROM need_check_fo WHERE full_name='%s' AND v_name='%s' " \
          "AND from_type='%s'" % (full_name, imp_version, from_type)
    db = pymysql.connect(host, user, password, db_name)
    try:
        # 执行sql语句
        check_cursor = db.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        update_sql = ''
        if check_result:
            # 有该项
            if check_result[0][1] != 0:
                update_sql = "UPDATE need_check_fo SET id='%d',bug_update='%d' " \
                             "WHERE id='%d'" % (time_num, 0, check_result[0][0])
        else:
            update_sql = "INSERT INTO need_check_fo (id,bug_update,full_name,v_name,from_type,d_repo,layer) " \
                         "VALUES ('%d','%d','%s','%s','%s'," \
                         "'%s','%d')" % (time_num, 0, full_name, imp_version, from_type, d_repo, layer)
        if update_sql:
            # time.sleep(0.8)
            db_insert = pymysql.connect(host, user, password, db_name)
            try:
                insert_cursor = db_insert.cursor()
                # 执行sql语句
                insert_cursor.execute(update_sql)
                db_insert.commit()
                insert_cursor.close()
                print('insert or update need_check_fo successful', full_name)
            except Exception as exp:
                print('insert or update need_check_fo error exception is:', exp, '***********************************')
                print('insert or update need_check_fo error sql:', update_sql)
                insert_e = insert_e + 1
                # 发生错误时回滚
                db_insert.rollback()
            db_insert.close()
    except Exception as exp:
        print("check need_check_fo error:【", full_name, '】', exp, '*************************************'
                                                                  '***????????????????????********')
        # 发生错误时回滚
        db.rollback()
        check_e = check_e + 1
    db.close()
    return insert_e, check_e


# 通过github的api在线分析
def check_repo_fo(fullname, r_version, host, user, password, db_name, search_e, insert_e, check_e, update_e, insert_s,
                  update_s, issue, time_w, check_type, db_id, c_method):
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    # d_url = 'https://raw.githubusercontent.com/'
    # d_url = 'https://api.github.com/repos/'
    # v_name = ''
    if r_version:
        semantic = True
        # # 获取主版本号：
        # imp_main_v = re.findall(r"^v(\d+?)\.", r_version)
        # if imp_main_v:
        #     v_siv = imp_main_v[0]
        # else:
        #     if re.findall(r"^v(\d+?)$", r_version):
        #         imp_main_v = re.findall(r"^v(\d+?)$", r_version)
        #         v_siv = imp_main_v[0]
        #     else:
        #         v_siv = '-1'
        # # 判断是否为伪版本,如果是，获取哈希值
        # not_semantic = re.findall(r"^v\d+?\.\d+?\.\d+?-*[^-]*?-[0-9.]+?-([A-Za-z0-9]+?)$", r_version)
        # # bug_main_version = ''
        # if not_semantic:
        #     v_name = not_semantic[0]
        # else:
        #     v_name = r_version
    else:
        semantic = False

    (search_e, insert_e, check_e, update_e, insert_s, update_s,
     issue) = get_detail_page(fullname, semantic, headers, host, user, password, db_name, search_e,
                              insert_e, check_e, update_e, insert_s, update_s, issue, time_w, r_version,
                              check_type, db_id, c_method)
    return search_e, insert_e, check_e, update_e, insert_s, update_s, issue


# stars, forks, update,
def get_detail_page(fullname, semantic, headers, host, user, password, db_name, search_e, insert_e,
                    check_e, update_e, insert_s, update_s, issue_l, time_w, r_version, check_type, db_id, c_method):
    v_name = r_version
    v_semantic = semantic
    if not semantic:
        one_repo_url = 'https://api.github.com/repos/' + fullname
        try:
            one_repo = get_results(one_repo_url, headers)
            # item_fullname = one_repo['full_name']  # 存：存储库完整名字
            # item_stars = one_repo['stargazers_count']  # 存：标星数量
            # item_forks = one_repo['forks_count']  # 存：forks数量
            # item_size = one_repo['size']  # 存：存储库大小
            # item_created = one_repo['created_at']  # 存：存储创建时间
            # item_updated = one_repo['updated_at']  # 存：数据库更新时间
            releases_url = one_repo['releases_url']  # 获取版本信息api
            (v_name, v_semantic) = get_version(releases_url, headers)
        except Exception as exp:
            print('获取该旧机制', check_type, '的上游', fullname, '失败:', exp, '-----------+++++++++++++++++++++++++'
                                                                     '+++-----------------------')
            check_e = check_e + 1
    # 未来会发生问题的地方
    bug_type_num = [0, 0, 0, 0, 0, 0, 0, 0]  # 没有问题，默认为0
    bug_list = ['', '', '', '', '', '', '', '']
    # 已经发生问题的地方
    break_type_num = [0, 0, 0, 0]
    break_list = ['', '', '', '']
    issue = ''
    # 获取本项目的go.mod文件的情况
    # (go_mod, main_version, go_mod_url, version_dir, issue) = get_go_mod(fullname, name, semantic, headers,
    #                                                                     issue)
    (go_mod_module, version_number, path_match, go_mod, main_version, go_mod_url, version_dir,
     issue) = get_go_mod_detail(fullname, v_name, v_semantic, headers, issue)
    r_type = judge_repo_type(go_mod, version_number, path_match, version_dir)
    print('旧机制上游-------------------------------------------------------------------------------------')
    show = '<' + fullname + '>' + v_name + '[go_mod:' + str(go_mod) + ']'
    show = show + ' [v_num:' + str(version_number) + ']' + '[v_dir:' + str(version_dir) + ']'
    show = show + '[path_match:' + str(path_match) + ']' + ' [r_type:' + str(r_type) + ']'
    print(show)
    check_local_self = 0
    if r_type == 4:
        # 问题3-0，C，下游新用户升级预警
        bug_type_num[4] = bug_type_num[4] + 1
        bug_list[4] = bug_list[4] + '$' + fullname + ' ' + v_name
    elif r_type == 10:

        # 问题4-0，D，下游新用户升级预警
        bug_type_num[6] = bug_type_num[6] + 1
        bug_list[6] = bug_list[6] + '$' + fullname + ' ' + v_name
        # print(go_mod_module)
        if version_number >= 2:
            module_siv = re.findall(r"/v" + str(version_number) + "$", go_mod_module)
            if not module_siv:
                # 问题3-0，C，下游新用户升级预警
                bug_type_num[4] = bug_type_num[4] + 1
                bug_list[4] = bug_list[4] + '$' + fullname + ' ' + v_name
            else:
                check_local_self = 1
    if r_type == 2 or check_local_self == 1:
        # 检测该项目是否存在自身调用，因为如果本项目是分支法创建的v>=2的，且本地有调用自己的代码则会出现影响下游的情况。
        (r, issue) = get_local_use(fullname, go_mod_module, 'check_self_use:1-0', time_w, issue)
        if r > 0:
            # 问题1-0，A，下游预警
            bug_1_0_type = '1.0'
            bug_type_num[0] = bug_type_num[0] + 1
            bug_list[0] = bug_list[0] + '$' + bug_1_0_type + ':' + fullname + ' ' + v_name
            print('[*]问题1-0', fullname + ' ' + v_name, ' 参数：', r_type, check_local_self)
    replace_num = [0, 0, 0, 0]
    replace_list = ['', '', '', '']
    if go_mod == 2:  # 如果有非空的go.mod文件，说明是新机制
        print('*新机制*')
        # 通过replace替换的地方
        # replaces_list 是go.mod文件中replace语句替换的repos，replace_list是这些替换曾经有问题的bug记录表
        (bug_type_num, bug_list, break_type_num, break_list, replace_num, replace_list,
         issue) = check_bug_new_repo(fullname, go_mod_url, bug_type_num, bug_list, break_type_num, break_list,
                                     replace_num, replace_list, headers, issue, time_w)
    else:
        if go_mod == 1:
            print('go.mod文件为空######################################################################################')

        # 遍历获取import导包语句
        print('本项目为非模块机制，需要从源文件中读取导包路径')
        db_check = 0
        (bug_type_num, bug_list, break_type_num, break_list, insert_e, search_e, check_e, update_e, insert_s, update_s,
         issue) = check_bug_old_repo_fo(fullname, v_name, v_semantic, bug_type_num, bug_list, break_type_num,
                                        break_list, headers, issue, time_w, host, user, password, db_name, insert_e,
                                        search_e, check_e, update_e, insert_s, update_s, check_type, db_id, db_check)

    # 打印检测结果
    impact = [0, 0]
    insert = 0
    replace = 0
    for bug_type in range(0, 8):
        if bug_type_num[bug_type] > 0:
            insert = insert + 1
            print('bug_存在问题', bug_type, ':', bug_list[bug_type])
            if bug_type <= 1:
                impact[0] = 1
            else:
                impact[1] = 1
    for break_type in range(0, 4):
        if break_type_num[break_type] > 0:
            insert = insert + 1
            print('break_存在问题', break_type, ':', break_list[break_type])
            if break_type <= 0:
                impact[0] = 1
            else:
                impact[1] = 1
    for replace_type in range(0, 4):
        if replace_num[replace_type] > 0:
            replace = replace + 1
            print('replace_存在问题', replace_type, ':', replace_list[replace_type])

    time_num = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    time_num = int(time_num)

    # insert_impact(time_num, fullname, update, name, bug_type_num, break_type_num, impact)
    # if insert:
    #     (check_error, insert_error,
    #      insert_success) = insert_info(time_num, fullname, stars, forks, update, name, bug_type_num, bug_list,
    #                                    break_type_num, break_list, impact, host, user, password, db_name,
    #                                    check_date, check_error, insert_error, insert_success)
    if replace:
        (check_e, insert_e, update_e, insert_s,
         update_s) = insert_replace(time_num, fullname, v_name, replace_num, replace_list, host, user, password,
                                    db_name, check_e, insert_e, update_e, insert_s, update_s)
    # (insert_error, update_error, check_error, insert_success,
    #  update_success) = insert_impact(time_num, fullname, update, name, bug_type_num, break_type_num, impact, host,
    #                                  user, password, db_name, insert_error, update_error, check_error,
    #                                  insert_success, update_success)
    # check_type = ''
    r_hash = ''
    time.sleep(0.8)
    (check_e, insert_e, update_e, insert_s,
     update_s) = insert_check_go_repos_db(time_num, fullname, v_name, r_hash, go_mod, version_dir, version_number,
                                          path_match, r_type,  check_type, bug_type_num, bug_list, break_type_num,
                                          break_list, impact, host, user,  password, db_name, check_e, insert_e,
                                          update_e, insert_s, update_s)
    if insert:
        get_type = re.findall(r"^\[o\](.+?)@\d$", check_type)
        if get_type:
            from_type = get_type[0]
        else:
            (from_type, layer) = get_need_check_info(host, user, password, db_name, db_id)
        down_repo_l = from_type.split('@')
        down_repo_name = down_repo_l[0].replace(' ', '')
        down_repo_ver = down_repo_l[1].replace(' ', '')
        if c_method:
            (check_e, update_e,
             update_s) = update_downrepo_s(down_repo_name, down_repo_ver, bug_type_num, bug_list, break_type_num,
                                           break_list, host, user, password, db_name, check_e, update_e, update_s,
                                           c_method)
        else:
            (check_e, update_e,
             update_s) = update_downrepo_l(down_repo_name, down_repo_ver, bug_type_num, bug_list, break_type_num,
                                           break_list, host, user, password, db_name, check_e, update_e, update_s)
    # time.sleep(time_w)
    # 更新待检测表
    (update_s, update_e) = update_need_check_fo(db_id, host, user, password, db_name,  update_s, update_e, v_name,
                                                go_mod)
    if issue:
        issue_l = issue_l + '【' + fullname + ':' + issue + '】'

    return search_e, insert_e, check_e, update_e, insert_s, update_s, issue_l


# 大表中的，非特定小表，更新；；小表不同之处在于版本号是哈希值，查的表不同
def update_downrepo_s(fullname, r_version, bug_type_num, bug_list, break_type_num, break_list, host, user,
                      password, db_name, check_e, update_e, update_s, c_method):
    r_id = 0
    sql = "SELECT id FROM " + c_method + " WHERE (full_name='%s' AND v_hash='%s')" % (fullname, r_version)
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            # print(check_result[0], ' type is: ', type(check_result[0]))
            r_id = int(check_result[0][0])
        else:
            sql = "SELECT id FROM " + c_method + " WHERE (full_name='%s' AND v_name='%s')" % (fullname, r_version)
            try:
                # 执行sql语句
                db_check = pymysql.connect(host, user, password, db_name)
                check_cursor = db_check.cursor()
                check_cursor.execute(sql)
                check_result = check_cursor.fetchall()
                check_cursor.close()
                db_check.close()
                if check_result:
                    # print(check_result[0], ' type is: ', type(check_result[0]))
                    r_id = int(check_result[0][0])
                else:
                    # REGEXP "孙$";
                    sql = 'SELECT id FROM ' + c_method + ' WHERE (full_name=' + fullname
                    sql = sql + ' AND v_name REGEXP "' + r_version + '$")'
                    try:
                        # 执行sql语句
                        db_check = pymysql.connect(host, user, password, db_name)
                        check_cursor = db_check.cursor()
                        check_cursor.execute(sql)
                        check_result = check_cursor.fetchall()
                        check_cursor.close()
                        db_check.close()
                        if check_result:
                            # print(check_result[0], ' type is: ', type(check_result[0]))
                            r_id = int(check_result[0][0])
                    except Exception as exp3:
                        print("find id to update the old repo from " + c_method + " error", fullname, '@', r_version,
                              exp3, '-------------------------------------------------%%%%%%%%%%%%%%%%'
                                    '%%%%%%%%%%%%%----------------')
                        check_e = check_e + 1
            except Exception as exp2:
                print("find id to update the old repo from " + c_method + " error", fullname, '@', r_version, exp2,
                      '-------------------------------------------------%%%%%%%%%%%%%%%%%%%%%%%%%%%%%----------------')
                check_e = check_e + 1

    except Exception as exp1:
        print("find id to update the old repo from " + c_method + " error", fullname, '@', r_version,
              exp1, '-------------------------------------------------%%%%%%%%%%%%%%%%%%%%%%%%%%%%%-1-----------------')
        check_e = check_e + 1
    # 查到了id号，开始更新数据
    if r_id:
        # 获取到github_go_repos_findbug数据库中的数据
        sql = "SELECT num1_1,list1_1,num2_0,list2_0,num3_0,list3_0,num4_0,list4_0,old_impact,new_impact " \
              "FROM " + c_method + " WHERE id='%d'" % r_id
        try:
            num_l = [0, 0, 0, 0]
            list_l = ['', '', '', '']
            impact = [0, 0]

            # 执行sql语句
            db_check = pymysql.connect(host, user, password, db_name)
            check_cursor = db_check.cursor()
            check_cursor.execute(sql)
            check_result = check_cursor.fetchall()
            check_cursor.close()
            db_check.close()
            if check_result:
                # num_l[0] = check_result[0][0]
                # list_l[0] = check_result[0][1]
                # num_l[1] = check_result[0][2]
                # list_l[1] = check_result[0][3]
                # num_l[2] = check_result[0][4]
                # list_l[2] = check_result[0][5]
                # num_l[3] = check_result[0][6]
                # list_l[3] = check_result[0][7]
                # 将结果更新至下游
                j = 0
                for i in range(0, 4):
                    num_l[i] = check_result[0][j]
                    j = j + 1
                    list_l[i] = check_result[0][j]
                    j = j + 1
                impact[0] = check_result[0][8]
                impact[1] = check_result[0][9]
                j = 0
                for i in range(0, 4):
                    if bug_type_num[0]:
                        num_l[i] = num_l[i] + bug_type_num[j]
                        list_l[i] = list_l[i] + bug_list[j]
                    j = j + 1
                    if bug_type_num[1]:
                        num_l[i] = num_l[i] + bug_type_num[j]
                        list_l[i] = list_l[i] + bug_list[j]
                    if break_type_num[i]:
                        num_l[i] = num_l[i] + break_type_num[i]
                        list_l[i] = list_l[i] + break_list[i]
                    j = j + 1
                # # bug1_0
                # if bug_type_num[0]:
                #     num_l[0] = num_l[0] + bug_type_num[0]
                #     list_l[0] = list_l[0] + bug_list[0]
                # # bug1_1
                # if bug_type_num[1]:
                #     num_l[0] = num_l[0] + bug_type_num[1]
                #     list_l[0] = list_l[0] + bug_list[1]
                # # break_1
                # if break_type_num[0]:
                #     num_l[0] = num_l[0] + break_type_num[0]
                #     list_l[0] = list_l[0] + break_list[0]
                # # bug2_0
                # if bug_type_num[2]:
                #     num_l[1] = num_l[1] + bug_type_num[2]
                #     list_l[1] = list_l[1] + bug_list[2]
                # # bug2_1
                # if bug_type_num[3]:
                #     num_l[1] = num_l[1] + bug_type_num[3]
                #     list_l[1] = list_l[1] + bug_list[3]
                # # break_2
                # if break_type_num[1]:
                #     num_l[1] = num_l[1] + break_type_num[1]
                #     list_l[1] = list_l[1] + break_list[1]
                # # bug3_0
                # if bug_type_num[4]:
                #     num_l[2] = num_l[2] + bug_type_num[4]
                #     list_l[2] = list_l[2] + bug_list[4]
                # # bug3_1
                # if bug_type_num[5]:
                #     num_l[2] = num_l[2] + bug_type_num[5]
                #     list_l[2] = list_l[2] + bug_list[5]
                # # break_3
                # if break_type_num[2]:
                #     num_l[2] = num_l[2] + break_type_num[2]
                #     list_l[2] = list_l[2] + break_list[2]
                # # bug4_0
                # if bug_type_num[6]:
                #     num_l[3] = num_l[3] + bug_type_num[6]
                #     list_l[3] = list_l[3] + bug_list[6]
                # # bug4_1
                # if bug_type_num[7]:
                #     num_l[3] = num_l[3] + bug_type_num[7]
                #     list_l[3] = list_l[3] + bug_list[7]
                # # break_4
                # if break_type_num[3]:
                #     num_l[3] = num_l[3] + break_type_num[3]
                #     list_l[3] = list_l[3] + break_list[3]

                if num_l[0]:
                    impact[0] = 1
                if num_l[1] or num_l[2] or num_l[3]:
                    impact[0] = 1
                # 更新数据库
                (update_s, update_e) = update_down_repo_db_s(fullname, r_version, num_l, list_l, impact, r_id, host,
                                                             user, password, db_name, update_s, update_e, c_method)
        except Exception as exp:
            print("find id to update the old repo from " + c_method + " error", fullname, '@', r_version, exp,
                  '-------------------------------------------------%%%%%%%%%%%%%%%%%%%%%%%%%%%%%-2-----------------')
            check_e = check_e + 1
    return check_e, update_e, update_s


def update_down_repo_db_s(fullname, r_version, num_l, list_l, impact, r_id, host, user, password, db_name,
                          update_s, update_e, c_method):
    update_sql = "UPDATE " + c_method + " SET num1_1='%d',list1_1='%s',num2_0='%d',list2_0='%s',num3_0='%d'," \
                 "list3_0='%s',num4_0='%d',list4_0='%s',old_impact='%d',new_impact='%d' " \
                 "WHERE id='%d'" % (num_l[0], list_l[0], num_l[1], list_l[1], num_l[2], list_l[2], num_l[3],
                                    list_l[3], impact[0], impact[1], r_id)
    db = pymysql.connect(host, user, password, db_name)
    try:
        update_cursor = db.cursor()
        # 执行sql语句
        update_cursor.execute(update_sql)
        db.commit()
        update_cursor.close()
        print('update ' + c_method + ' successful:', fullname, '@', r_version)
        update_s = update_s + 1
    except Exception as exp:
        print('update ' + c_method + ' error exception is:', exp, '*FROM*', fullname, '@', r_version)
        print('update ' + c_method + ' error sql:', update_sql)
        update_e = update_e + 1
        # 发生错误时回滚
        db.rollback()
    db.close()
    return update_s, update_e


# 大表中的，非特定小表，更新；；小表不同之处在于版本号是哈希值，查的表不同
def update_downrepo_l(fullname, r_version, bug_type_num, bug_list, break_type_num, break_list, host, user,
                      password, db_name, check_e, update_e, update_s):
    r_id = 0
    sql = "SELECT id FROM repo_impact WHERE (full_name='%s' AND v_name='%s')" % (fullname, r_version)
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            # print(check_result[0], ' type is: ', type(check_result[0]))
            r_id = int(check_result[0][0])
        else:
            sql = "SELECT id FROM repo_impact WHERE full_name='%s'" % fullname
            try:
                # 执行sql语句
                db_check = pymysql.connect(host, user, password, db_name)
                check_cursor = db_check.cursor()
                check_cursor.execute(sql)
                check_result = check_cursor.fetchall()
                check_cursor.close()
                db_check.close()
                if check_result:
                    # print(check_result[0], ' type is: ', type(check_result[0]))
                    r_id = int(check_result[0][0])
            except Exception as exp:
                print("find id to update the old repo from repo_impact error", fullname, '@', r_version, exp,
                      '-------------------------------------------------%%%%%%%%%%%%%%%%%%%%%%%%%%%%%----------------')
                check_e = check_e + 1

    except Exception as exp:
        print("find id to update the old repo from repo_impact error", fullname, '@', r_version,
              exp, '-------------------------------------------------%%%%%%%%%%%%%%%%%%%%%%%%%%%%%-1-----------------')
        check_e = check_e + 1
    # 查到了id号，开始更新数据
    if r_id:
        # 获取到github_go_repos_findbug数据库中的数据
        sql = "SELECT num1_1,list1_1,num2_0,list2_0,num3_0,list3_0,num4_0,list4_0,old_impact,new_impact " \
              "FROM github_go_repos_findbug WHERE id='%d'" % r_id
        try:
            num_l = [0, 0, 0, 0]
            list_l = ['', '', '', '']
            impact = [0, 0]

            # 执行sql语句
            db_check = pymysql.connect(host, user, password, db_name)
            check_cursor = db_check.cursor()
            check_cursor.execute(sql)
            check_result = check_cursor.fetchall()
            check_cursor.close()
            db_check.close()
            if check_result:
                # num_l[0] = check_result[0][0]
                # list_l[0] = check_result[0][1]
                # num_l[1] = check_result[0][2]
                # list_l[1] = check_result[0][3]
                # num_l[2] = check_result[0][4]
                # list_l[2] = check_result[0][5]
                # num_l[3] = check_result[0][6]
                # list_l[3] = check_result[0][7]
                # 将结果更新至下游
                j = 0
                for i in range(0, 4):
                    num_l[i] = check_result[0][j]
                    j = j + 1
                    list_l[i] = check_result[0][j]
                    j = j + 1
                impact[0] = check_result[0][8]
                impact[1] = check_result[0][9]
                j = 0
                for i in range(0, 4):
                    if bug_type_num[0]:
                        num_l[i] = num_l[i] + bug_type_num[j]
                        list_l[i] = list_l[i] + bug_list[j]
                    j = j + 1
                    if bug_type_num[1]:
                        num_l[i] = num_l[i] + bug_type_num[j]
                        list_l[i] = list_l[i] + bug_list[j]
                    if break_type_num[i]:
                        num_l[i] = num_l[i] + break_type_num[i]
                        list_l[i] = list_l[i] + break_list[i]
                    j = j + 1
                # # bug1_0
                # if bug_type_num[0]:
                #     num_l[0] = num_l[0] + bug_type_num[0]
                #     list_l[0] = list_l[0] + bug_list[0]
                # # bug1_1
                # if bug_type_num[1]:
                #     num_l[0] = num_l[0] + bug_type_num[1]
                #     list_l[0] = list_l[0] + bug_list[1]
                # # break_1
                # if break_type_num[0]:
                #     num_l[0] = num_l[0] + break_type_num[0]
                #     list_l[0] = list_l[0] + break_list[0]
                # # bug2_0
                # if bug_type_num[2]:
                #     num_l[1] = num_l[1] + bug_type_num[2]
                #     list_l[1] = list_l[1] + bug_list[2]
                # # bug2_1
                # if bug_type_num[3]:
                #     num_l[1] = num_l[1] + bug_type_num[3]
                #     list_l[1] = list_l[1] + bug_list[3]
                # # break_2
                # if break_type_num[1]:
                #     num_l[1] = num_l[1] + break_type_num[1]
                #     list_l[1] = list_l[1] + break_list[1]
                # # bug3_0
                # if bug_type_num[4]:
                #     num_l[2] = num_l[2] + bug_type_num[4]
                #     list_l[2] = list_l[2] + bug_list[4]
                # # bug3_1
                # if bug_type_num[5]:
                #     num_l[2] = num_l[2] + bug_type_num[5]
                #     list_l[2] = list_l[2] + bug_list[5]
                # # break_3
                # if break_type_num[2]:
                #     num_l[2] = num_l[2] + break_type_num[2]
                #     list_l[2] = list_l[2] + break_list[2]
                # # bug4_0
                # if bug_type_num[6]:
                #     num_l[3] = num_l[3] + bug_type_num[6]
                #     list_l[3] = list_l[3] + bug_list[6]
                # # bug4_1
                # if bug_type_num[7]:
                #     num_l[3] = num_l[3] + bug_type_num[7]
                #     list_l[3] = list_l[3] + bug_list[7]
                # # break_4
                # if break_type_num[3]:
                #     num_l[3] = num_l[3] + break_type_num[3]
                #     list_l[3] = list_l[3] + break_list[3]

                if num_l[0]:
                    impact[0] = 1
                if num_l[1] or num_l[2] or num_l[3]:
                    impact[0] = 1
                # 更新数据库
                (update_s, update_e,
                 check_e) = update_down_repo_db_l(fullname, r_version, num_l, list_l, impact, r_id, host, user,
                                                  password, db_name, update_s, update_e, check_e)
        except Exception as exp:
            print("find id to update the old repo from github_go_repos_findbug error", fullname, '@', r_version, exp,
                  '-------------------------------------------------%%%%%%%%%%%%%%%%%%%%%%%%%%%%%-2-----------------')
            check_e = check_e + 1
    return check_e, update_e, update_s


def update_down_repo_db_l(fullname, r_version, num_l, list_l, impact, r_id, host, user, password, db_name,
                          update_s, update_e, check_e):
    update_sql = "UPDATE github_go_repos_findbug SET num1_1='%d',list1_1='%s',num2_0='%d',list2_0='%s',num3_0='%d'," \
                 "list3_0='%s',num4_0='%d',list4_0='%s',old_impact='%d',new_impact='%d' " \
                 "WHERE id='%d'" % (num_l[0], list_l[0], num_l[1], list_l[1], num_l[2], list_l[2], num_l[3],
                                    list_l[3], impact[0], impact[1], r_id)
    db = pymysql.connect(host, user, password, db_name)
    try:
        update_cursor = db.cursor()
        # 执行sql语句
        update_cursor.execute(update_sql)
        db.commit()
        update_cursor.close()
        print('update github_go_repos_findbug successful:', fullname, '@', r_version)
        update_s = update_s + 1
    except Exception as exp:
        print('update github_go_repos_findbug error exception is:', exp, '*FROM*', fullname, '@', r_version)
        print('update github_go_repos_findbug error sql:', update_sql)
        update_e = update_e + 1
        # 发生错误时回滚
        db.rollback()
    db.close()

    # 更新repo_impact表
    # 获取到github_go_repos_findbug数据库中的数据
    sql = "SELECT o_bug,n_bug,old_impact,new_impact FROM repo_impact WHERE id='%d'" % r_id
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            need_update = 0
            o_bug_s = '0'
            if num_l[0] != 0:
                o_bug_s = '1'
            o_bug = check_result[0][0][0:1] + o_bug_s + check_result[0][0][2:3]
            if o_bug != check_result[0][0]:
                need_update = need_update + 1
            n_bug_s_l = ['0', '0', '0']
            for i in range(1, 4):
                if num_l[i] != 0:
                    j = i - 1
                    n_bug_s_l[j] = '1'
            n_bug = n_bug_s_l[0] + check_result[0][1][1:3] + n_bug_s_l[1] + check_result[0][1][4:6]
            n_bug = n_bug + n_bug_s_l[2] + check_result[0][1][7:9]
            if n_bug != check_result[0][1]:
                need_update = need_update + 1
            if need_update > 0:
                # 更新repo_impact数据库
                sql = "UPDATE repo_impact SET o_bug='%s',n_bug='%s',old_impact='%d',new_impact='%d' " \
                      "WHERE id='%d'" % (o_bug, n_bug, impact[0], impact[1], r_id)
                db = pymysql.connect(host, user, password, db_name)
                try:
                    update_cursor = db.cursor()
                    # 执行sql语句
                    update_cursor.execute(sql)
                    db.commit()
                    update_cursor.close()
                    print('update repo_impact successful:', fullname, '@', r_version)
                    update_s = update_s + 1
                except Exception as exp:
                    print('update repo_impact error exception is:', exp, '*FROM*', fullname, '@', r_version)
                    print('update repo_impact error sql:', update_sql)
                    update_e = update_e + 1
                    # 发生错误时回滚
                    db.rollback()
                db.close()
    except Exception as exp:
        print("use id to update the old repo from repo_impact error", fullname, '@', r_version,
              exp, '-------------------------------------------------%%%%%%%%%%%%%%%%%%%%%%%%%%%%%-3-----------------')
        check_e = check_e + 1
    return update_s, update_e, check_e


# 更新数据库表repo_impact
def insert_check_go_repos_db(time_num, fullname, v_name, v_hash, go_mod, v_dir, v_num, path_match, r_type, check_type,
                             bug_type, bug_list, break_type, break_list, impact, host, user, password, db_name, check_e,
                             insert_e, update_e, insert_s, update_s):
    # 查重
    result_id = check_check_go_repos_db(fullname, v_name, v_hash, check_type, host, user, password, db_name)

    if result_id <= 0:
        insert_sql = "INSERT INTO check_go_repos (id,full_name,v_name,v_hash,go_mod,v_dir,v_num,path_match,r_type," \
                     "num1_0,list1_0,num1_1,list1_1,break1,break_list1,num2_0,list2_0,num2_1,list2_1,break2," \
                     "break_list2,num3_0,list3_0,num3_1,list3_1,break3,break_list3,num4_0,list4_0,num4_1,list4_1," \
                     "break4,break_list4,old_impact,new_impact,check_type) VALUES ('%d','%s','%s','%s','%d','%d'," \
                     "'%d','%d','%d','%d','%s','%d','%s','%d','%s','%d','%s','%d','%s','%d','%s'," \
                     "'%d','%s','%d','%s','%d','%s','%d','%s','%d','%s','%d','%s'," \
                     "'%d','%d','%s')" % (time_num, fullname, v_name, v_hash, go_mod, v_dir, v_num, path_match, r_type,
                                          bug_type[0], bug_list[0], bug_type[1], bug_list[1], break_type[0],
                                          break_list[0], bug_type[2], bug_list[2], bug_type[3], bug_list[3],
                                          break_type[1], break_list[1], bug_type[4], bug_list[4], bug_type[5],
                                          bug_list[5], break_type[2], break_list[2], bug_type[6], bug_list[6],
                                          bug_type[7], bug_list[7], break_type[3], break_list[3], impact[0],
                                          impact[1], check_type)
        db = pymysql.connect(host, user, password, db_name)
        try:
            insert_cursor = db.cursor()
            # 执行sql语句
            insert_cursor.execute(insert_sql)
            db.commit()
            insert_cursor.close()
            print('insert check_go_repos successful:', fullname, '@', v_name, '@@', v_hash)
            insert_s = insert_s + 1
        except Exception as exp:
            print('insert check_go_repos error exception is:', exp, '-----------------------------------------------'
                                                                    '---------------------------------------------')
            print('insert check_go_repos error sql:', insert_sql)
            insert_e = insert_e + 1
            # 发生错误时回滚
            db.rollback()
        db.close()
    elif result_id > 0:
        # repo_impact (id,full_name,update_time,old_impact,new_impact)new_impact
        update_sql = "UPDATE check_go_repos SET id='%d',go_mod='%d',v_dir='%d',v_num='%d',path_match='%d'," \
                     "r_type='%d',num1_0='%d',list1_0='%s',num1_1='%d',list1_1='%s',break1='%d',break_list1='%s'," \
                     "num2_0='%d',list2_0='%s',num2_1='%d',list2_1='%s',break2='%d',break_list2='%s',num3_0='%d'," \
                     "list3_0='%s',num3_1='%d',list3_1='%s',break3='%d',break_list3='%s',num4_0='%d',list4_0='%s'," \
                     "num4_1='%d',list4_1='%s',break4='%d',break_list4='%s',old_impact='%d',new_impact='%d' " \
                     "WHERE id='%d'" % (time_num, go_mod, v_dir, v_num, path_match, r_type, bug_type[0], bug_list[0],
                                        bug_type[1], bug_list[1], break_type[0], break_list[0], bug_type[2],
                                        bug_list[2], bug_type[3], bug_list[3], break_type[1], break_list[1],
                                        bug_type[4], bug_list[4], bug_type[5], bug_list[5], break_type[2],
                                        break_list[2], bug_type[6], bug_list[6], bug_type[7], bug_list[7],
                                        break_type[3], break_list[3], impact[0], impact[1], result_id)
        db = pymysql.connect(host, user, password, db_name)
        try:
            update_cursor = db.cursor()
            # 执行sql语句
            update_cursor.execute(update_sql)
            db.commit()
            update_cursor.close()
            print('update check_go_repos successful:', fullname, '@', v_name, '@@', v_hash)
            update_s = update_s + 1
        except Exception as exp:
            print('update check_go_repos error exception is:', exp)
            print('update check_go_repos error sql:', update_sql)
            update_e = update_e + 1
            # 发生错误时回滚
            db.rollback()
        db.close()
    else:
        print('check check_go_repos error:', fullname, '@', v_name, '@@', v_hash, '---------------------------------'
                                                                                  '---------------------------------'
                                                                                  '-------------------------------')
        check_e = check_e + 1
    return check_e, insert_e, update_e, insert_s, update_s


# 查重
def check_check_go_repos_db(fullname, v_name, v_hash, check_type, host, user, password, db_name):
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT id FROM check_go_repos WHERE (full_name='%s' AND v_name='%s' AND v_hash='%s' AND " \
          "check_type='%s')" % (fullname, v_name, v_hash, check_type)
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            # print(check_result[0], ' type is: ', type(check_result[0]))
            r_id = int(check_result[0][0])
            return r_id
        else:
            return 0
    except Exception as exp:
        print("check check_go_repos_gt error", fullname, '@', v_name, '@@', v_hash, ':',
              exp, '--------------------------------------------------------------------------------------------------')
        return -1


def update_need_check_fo(db_id, host, user, password, db_name,  update_s, update_e, v_name, go_mod):
    update_sql = "UPDATE need_check_fo SET bug_update=1,v_name='%s',go_mod='%d' WHERE id='%d'" % (v_name, go_mod, db_id)

    db = pymysql.connect(host, user, password, db_name)
    try:
        update_cursor = db.cursor()
        # 执行sql语句
        update_cursor.execute(update_sql)
        db.commit()
        update_cursor.close()
        print('update need_check_fo successful:', db_id)
        update_s = update_s + 1
    except Exception as exp:
        print('update need_check_fo error exception is:', exp)
        print('update need_check_fo error sql:', update_sql)
        update_e = update_e + 1
        # 发生错误时回滚
        db.rollback()
    db.close()
    return update_s, update_e


def get_need_check_list(host, user, password, db_name):
    need_check_list = []
    sql = "SELECT id,full_name,v_name,from_type,layer FROM need_check_fo WHERE bug_update=0"
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            # num = len(check_result)
            for r in check_result:
                check_type = '[o]' + r[3] + '@' + r[4]
                need_check_list.append([r[0], r[1], r[2], check_type])
    except Exception as exp:
        print("get need_check_fo error",
              exp, '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
    return need_check_list


def main():
    insert_e = 0
    search_e = 0
    check_e = 0
    update_e = 0
    insert_s = 0
    update_s = 0
    issue_l = ''
    time_w = 1.6
    user = 'root'
    host = '47.254.86.255'
    password = 'Ella1996'
    db_name = 'githubspider'
    time_s = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    # repo_fullname = 'go-ldap/ldap'
    # repo_version = 'v3.1.7'
    # repo_hash = 'ec72334'
    # check_type = 'issues'
    # list_2 = []
    # list_repo_check = [['prometheus/prometheus', 'v2.17.1', '']]  # v2.17.1
    c_method = ''  # 空，不是特定表，有表名，是特定表，在后续检测结果返回时查表不同，需要额外标注
    need_check_list = get_need_check_list(host, user, password, db_name)
    for repo_check in need_check_list:
        repo_fullname = repo_check[1]
        repo_version = repo_check[2]
        db_id = repo_check[0]
        check_type = repo_check[3]
        if repo_fullname:
            (search_e, insert_e, check_e, update_e, insert_s, update_s,
             issue_l) = check_repo_fo(repo_fullname, repo_version, host, user, password, db_name, search_e, insert_e,
                                      check_e, update_e, insert_s, update_s, issue_l, time_w, check_type, db_id,
                                      c_method)
        else:
            print('repo_name 不正确')

    print('searchError', search_e, 'insertError', insert_e, 'checkError', check_e, 'updateError', update_e)
    print('insert successfully:', insert_s)
    print('update successfully:', update_s)
    print('other issues:', issue_l)
    time_e = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    print(time_s, '->', time_e)


if __name__ == '__main__':
    # 声明线程池
    executor = ThreadPoolExecutor(6)
    main()
