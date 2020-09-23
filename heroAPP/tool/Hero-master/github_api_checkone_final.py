import base64
import json
import re
import time
from concurrent.futures.thread import ThreadPoolExecutor
from urllib.request import Request, urlopen
import pymysql
from findbug_oneoldcheck_api import check_bug_old_repo
from findbug_onenewcheck_api import check_bug_new_repo, insert_replace, get_repo_detail
from findchange_api import judge_repo_type, get_go_mod_detail
from find_local_use import get_local_use

# from check_200.final_file.findbug_oneoldcheck_api import check_bug_old_repo
# from one_check_api.findbug_onenewcheck_api import check_bug_new_repo
# # from one_check_api.findchange_api import judge_repo_type, get_go_mod_detail
# from one_check_api.find_local_use import get_local_use
# from one_check_api.findchange_api import get_go_mod_detail
# from one_check_api.findbug_onenewcheck_api import insert_replace, get_repo_detail
# from one_check_api.findbug_oneoldcheck_api import check_bug_old_repo
# from one_check_api.findbug_oneoldcheck_api import check_up_repo_fo
from findchange_20200529_api import get_version


def get_results(url, headers):
    request = Request(url, headers=headers)
    response = urlopen(request).read()
    result = json.loads(response.decode())
    # time
    return result


# 通过github的api在线分析
def check_repo_from_api(fullname, r_version, r_hash, r_mes_list, host, user, password, db_name, search_e, insert_e,
                        check_e, update_e, insert_s, update_s, issue, time_w, check_type, insert_db):
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    # d_url = 'https://raw.githubusercontent.com/'
    # d_url = 'https://api.github.com/repos/'
    stars = -1
    forks = -1
    updated = ''
    v_name = ''
    if not r_version:
        r_version = ''
    if not r_hash:
        r_hash = ''
    if r_mes_list:
        # stars, forks, updated, semantic
        semantic = r_mes_list[3]
        stars = r_mes_list[0]
        forks = r_mes_list[1]
        updated = r_mes_list[2]
    else:
        semantic = True

    # 获取主版本号：
    imp_main_v = re.findall(r"^v(\d+?)\.", r_version)
    if imp_main_v:
        v_siv = str(imp_main_v[0])
    else:
        if re.findall(r"^v(\d+?)$", r_version):
            imp_main_v = re.findall(r"^v(\d+?)$", r_version)
            v_siv = str(imp_main_v[0])
        else:
            v_siv = '-1'

    if r_hash:
        # d_url = d_url + fullname + '/contents?ref=' + r_hash
        v_name = r_hash

    elif r_hash == '' and r_version:
        # 判断是否为伪版本,如果是，获取哈希值
        not_semantic = re.findall(r"^v\d+?\.\d+?\.\d+?-*[^-]*?-[0-9.]+?-([A-Za-z0-9]+?)$", r_version)
        # bug_main_version = ''
        if not_semantic:
            v_name = not_semantic[0]
        else:
            v_name = r_version
    else:
        semantic = False

    # try:
    #     page_detail = get_results(d_url, headers)
    # except Exception as exp:
    #     print("无法获取该存储库的当前版本" + fullname + '@' + v_name + '：', exp, '***********************************'
    #                                                                 '*get go.mod*******')
    #     issue = issue + '<' + 'get_go_mod:' + fullname + '@' + v_name + '>'
    #     page_detail = ''
    (search_e, insert_e, check_e, update_e, insert_s, update_s,
     issue) = get_detail_page(fullname, v_name, v_siv, semantic, stars, forks, updated, headers, host, user, password,
                              db_name, search_e, insert_e, check_e, update_e, insert_s, update_s, issue, time_w,
                              r_version, r_hash, check_type, insert_db)
    return search_e, insert_e, check_e, update_e, insert_s, update_s, issue


# 这里与新旧机制检测不同，有哈希值干扰
def one_get_go_mod_detail(fullname, name, v_siv, headers, issue):
    go_mod = 0  # 存：是否有go.mod的指标。【0无；1有但为空；2有且非空】
    go_mod_url = ''
    version_dir = 0  # 存：是否有主要子目录的指标。【0无；1有但为空；2有且非空】
    # main_version = ''
    go_mod_module = ''
    version_number = -1
    path_match = -1  # 无go.mod文件的，不存在匹配问题，默认为-1
    sub_mod = ''
    repo_name = ''
    if re.findall(r"^[^/]+?/[^/]+?(/.+?)$", fullname):
        repo_name = re.findall(r"^([^/]+?/[^/]+?)/.+?$", fullname)[0]
        sub_mod = re.findall(r"^[^/]+?/[^/]+?(/.+?)$", fullname)[0]

    d_url = 'https://api.github.com/repos/'
    if name:
        if sub_mod:
            d_url = d_url + repo_name + '/contents' + sub_mod + '?ref=' + name
        else:
            d_url = d_url + fullname + '/contents?ref=' + name

    else:
        if sub_mod:
            d_url = d_url + repo_name + '/contents' + sub_mod
        else:
            d_url = d_url + fullname + '/contents'
    # print(d_url)
    try:
        page_detail = get_results(d_url, headers)
        # get go.mod
        if v_siv != '-1':
            sub_dir = 'v' + v_siv
        else:
            sub_dir = name
        for f in page_detail:
            # 判断有无go.mod文件
            if f['name'] == 'go.mod':
                # print('yes')
                if f['size'] == 0:
                    go_mod = 1
                else:
                    go_mod = 2
                go_mod_url = f['url']
            # 判断有无子目录/vN
            if (f['name'] == sub_dir or f['name'] == ('.' + sub_dir)) and f['type'] == 'dir':
                # print('yes')
                sub_dir_result = get_results(f['url'], headers)
                if sub_dir_result:
                    # print('have sub direct')
                    version_dir = 1
                    go_mod = 0
                    for sub_dir_f in sub_dir_result:
                        # 判断有无go.mod文件
                        if sub_dir_f['name'] == 'go.mod':
                            # print('yes')
                            if sub_dir_f['size'] == 0:
                                go_mod = 1
                            else:
                                go_mod = 2
                            go_mod_url = sub_dir_f['url']
                            version_dir = 2
        # get go.mod detail
        if v_siv.isdigit() and v_siv != '-1':
            # 主版本为数字（整数），且>=2
            version_number = int(v_siv)

        # path_match：存：go.mod文件中的module声明的模块路径与Go Modules机制要求的模块路径是否一致的指标
        # 判断所有有go.mod文件的，module声明的模块路径与Go Modules要求的是否一致
        if go_mod >= 2:  # 如果有非空的go.mod文件
            # print(go_mod_url)
            go_mod_result = get_results(go_mod_url, headers)  # 获取go.mod内容
            # 解码后，使用正则表达式，获取module声明的模块路径
            go_mod_content = base64.b64decode(go_mod_result['content'])
            module = re.findall(r"^module\s*(.+?)$", go_mod_content.decode(), re.M)

            if module:
                go_mod_module = module[0].replace('"', '').strip()  # go.mod中module声明的模块路径
            else:
                go_mod_module = ''
            # print(go_mod_module)
            # k8s.com=github.com/kubernetes
            if re.findall(r"^k8s.com", go_mod_module):
                go_mod_module = go_mod_module.replace('k8s.com', 'github.com/kubernetes')

            module_path = 'github.com/' + fullname  # 模块机制要求的不带语义版本的路径
            if version_number >= 2:
                # 按照module要求的带语义版本的模块路径
                module_version_path = 'github.com/' + fullname + '/' + 'v' + v_siv
                # print(module_version_path)
                if go_mod_module == module_version_path:
                    path_match = 2  # 完全一致
                elif go_mod_module == module_path:
                    path_match = 1  # 没有导入语义版本，问题3（C）
                else:
                    path_match = 0  # 路径完全不一致，问题4
            else:
                if go_mod_module == module_path:
                    path_match = 2  # 完全一致
                else:
                    path_match = 0  # 路径完全不一致，问题4

    except Exception as exp:
        print("版本获取不到：", exp, '************************************请检查版本是否还存在*******')
        # version_number, path_match

    return go_mod_module, version_number, path_match, go_mod, go_mod_url, version_dir, issue


# stars, forks, update,
def get_detail_page(fullname, v_name, v_siv, semantic, stars, forks, updated, headers, host, user, password, db_name,
                    search_e, insert_e, check_e, update_e, insert_s, update_s, issue_l, time_w, r_version, r_hash,
                    check_type, insert_db):
    if re.findall(r"^[^/]+?/[^/]+?(/.+?)$", fullname):
        repo_fullname = re.findall(r"^([^/]+?/[^/]+?)/.+?$", fullname)[0]
        # sub_mod = re.findall(r"^[^/]+?/[^/]+?(/.+?)$", fullname)[0]
    else:
        repo_fullname = fullname
        # sub_mod = ''

    # 未来会发生问题的地方
    bug_type_num = [0, 0, 0, 0, 0, 0, 0, 0]  # 没有问题，默认为0
    bug_list = ['', '', '', '', '', '', '', '']
    # 已经发生问题的地方
    break_type_num = [0, 0, 0, 0]
    break_list = ['', '', '', '']
    issue = ''
    nc_ur = 0
    from_type = ''
    # 获取本项目的go.mod文件的情况
    # (go_mod, main_version, go_mod_url, version_dir, issue) = get_go_mod(fullname, name, semantic, headers,
    #                                                                     issue)
    (go_mod_module, version_number, path_match, go_mod, go_mod_url, version_dir,
     issue) = one_get_go_mod_detail(fullname, v_name, v_siv, headers, issue)
    r_type = judge_repo_type(go_mod, version_number, path_match, version_dir)
    print('*********************************************************************************************************')
    show = '【' + fullname + '】' + r_version + '&' + r_hash + '[go_mod:' + str(go_mod) + ']'
    show = show + ' [v_num:' + str(version_number) + ']' + '[v_dir:' + str(version_dir) + ']'
    show = show + '[path_match:' + str(path_match) + ']' + ' [r_type:' + str(r_type) + ']'
    print(show)
    if go_mod < 2:
        # 非模块机制，以防万一，再次检查master分支上的最新commit，以及是否有最新版本
        # https://api.github.com/repos/knative/serving/releases
        v_url = "https://api.github.com/repos/" + repo_fullname + "/releases{/id}"
        (v_name_rc, semantic) = get_version(v_url, headers)
        if v_name_rc != v_name:
            # 获取主版本号：
            imp_main_v = re.findall(r"^v(\d+?)\.", r_version)
            if imp_main_v:
                v_siv_rc = str(imp_main_v[0])
            else:
                if re.findall(r"^v(\d+?)$", r_version):
                    imp_main_v = re.findall(r"^v(\d+?)$", r_version)
                    v_siv_rc = str(imp_main_v[0])
                else:
                    v_siv_rc = '-1'
            v_hash_rc = ''
            (go_mod_module, version_number, path_match, go_mod, go_mod_url, version_dir,
             issue) = one_get_go_mod_detail(fullname, v_name_rc, v_siv_rc, headers, issue)
            r_type = judge_repo_type(go_mod, version_number, path_match, version_dir)
            print('*****************************************************************************************')
            show = '【' + fullname + '】' + v_name_rc + '&' + v_hash_rc + '[go_mod:' + str(go_mod) + ']'
            show = show + ' [v_num:' + str(version_number) + ']' + '[v_dir:' + str(version_dir) + ']'
            show = show + '[path_match:' + str(path_match) + ']' + ' [r_type:' + str(r_type) + ']'
            print(show)
        if go_mod < 2:
            v_name_rc = ''
            v_hash_rc = ''
            v_siv_rc = '-1'
            (go_mod_module, version_number, path_match, go_mod, go_mod_url, version_dir,
             issue) = one_get_go_mod_detail(fullname, v_name_rc, v_siv_rc, headers, issue)
            r_type = judge_repo_type(go_mod, version_number, path_match, version_dir)
            print('*****************************************************************************************')
            show = '【' + fullname + '】' + v_name_rc + '&' + v_hash_rc + '[go_mod:' + str(go_mod) + ']'
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
        (r, issue) = get_local_use(repo_fullname, go_mod_module, 'check_self_use:1-0', time_w, issue)
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
        check_type = 0  # 是否要在检测上游依赖项时，检测大库中repo的检测结果，0是检测；其他是不检测，实现单个项目的完全自检测
        (bug_type_num, bug_list, break_type_num, break_list, insert_e, search_e,
         check_e, update_e, insert_s, update_s, issue, nc_ur,
         from_type) = check_bug_old_repo(fullname, v_name, semantic, bug_type_num, bug_list, break_type_num, break_list,
                                         headers, issue, time_w, host, user, password, db_name, insert_e, search_e,
                                         check_e, update_e, insert_s, update_s, check_type)

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

    time.sleep(0.8)
    time_num = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    time_num = int(time_num)
    # if insert:
    #     insert_info(time_num, fullname, stars, forks, update, name, bug_type_num, bug_list, break_type_num,
    #                 break_list, impact)
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
    (check_e, insert_e, update_e, insert_s,
     update_s) = insert_check_go_repos_db(time_num, fullname, r_version, r_hash, stars, forks, updated, go_mod,
                                          version_dir, version_number, path_match, r_type,  check_type, bug_type_num,
                                          bug_list, break_type_num, break_list, impact, host, user,  password, db_name,
                                          check_e, insert_e, update_e, insert_s, update_s, insert_db)
    # 检测上游的项目
    # if nc_ur > 0:
    #     # time.sleep(0.8)
    #     # c_method = insert_db  # 空，不是特定表，有表名，是特定表，在后续检测结果返回时查表不同，需要额外标注
    #     (search_e, insert_e, check_e, update_e, insert_s, update_s,
    #      issue_l) = check_up_repo_fo(from_type, host, user, password, db_name, search_e, insert_e, check_e,
    #                                  update_e, insert_s, update_s, issue_l, time_w, insert_db)

    # time.sleep(time_w)
    if issue:
        issue_l = issue_l + '【' + fullname + ':' + issue + '】'

    # # 更新待检测表
    # (update_s, update_e) = update_need_check_db(fullname, r_version, r_hash, check_type, host, user, password,
    #                                             db_name, update_s, update_e, go_mod)
    return search_e, insert_e, check_e, update_e, insert_s, update_s, issue_l


# 更新数据库表repo_impact
def insert_check_go_repos_db(time_num, fullname, v_name, v_hash, stars, forks, updated, go_mod, v_dir, v_num,
                             path_match, r_type, check_type, bug_type, bug_list, break_type, break_list, impact, host,
                             user, password, db_name, check_e, insert_e, update_e, insert_s, update_s, insert_db):
    # 查重
    result_id = check_check_go_repos_db(fullname, v_name, v_hash, check_type, host, user, password, db_name, insert_db)

    if result_id <= 0:
        insert_sql = "INSERT INTO " + insert_db + " (id,full_name,v_name,v_hash,stars,forks,updated,go_mod,v_dir,"\
                     + "v_num,path_match,r_type,num1_0,list1_0,num1_1,list1_1,break1,break_list1,num2_0,list2_0," \
                       "num2_1,list2_1,break2,break_list2,num3_0,list3_0,num3_1,list3_1,break3,break_list3,num4_0," \
                       "list4_0,num4_1,list4_1,break4,break_list4,old_impact,new_impact,check_type) VALUES ('%d'," \
                       "'%s','%s','%s','%d','%d','%s','%d','%d','%d','%d','%d','%d','%s','%d','%s','%d','%s','%d'," \
                       "'%s','%d','%s','%d','%s','%d','%s','%d','%s','%d','%s','%d','%s','%d','%s','%d','%s'," \
                       "'%d','%d','%s')" % (time_num, fullname, v_name, v_hash, stars, forks, updated, go_mod, v_dir,
                                            v_num, path_match, r_type, bug_type[0], bug_list[0], bug_type[1],
                                            bug_list[1], break_type[0], break_list[0], bug_type[2], bug_list[2],
                                            bug_type[3], bug_list[3],  break_type[1], break_list[1], bug_type[4],
                                            bug_list[4], bug_type[5], bug_list[5], break_type[2], break_list[2],
                                            bug_type[6], bug_list[6], bug_type[7], bug_list[7], break_type[3],
                                            break_list[3], impact[0], impact[1], check_type)
        db = pymysql.connect(host, user, password, db_name)
        try:
            insert_cursor = db.cursor()
            # 执行sql语句
            insert_cursor.execute(insert_sql)
            db.commit()
            insert_cursor.close()
            print('insert ', insert_db, ' successful:', fullname, '@', v_name, '@@', v_hash)
            insert_s = insert_s + 1
        except Exception as exp:
            print('insert ', insert_db, ' error exception is:', exp, '-----------------------------------------------'
                                        '---------------------------------------------')
            print('insert ', insert_db, ' error sql:', insert_sql)
            insert_e = insert_e + 1
            # 发生错误时回滚
            db.rollback()
        db.close()
    elif result_id > 0:
        # repo_impact (id,full_name,update_time,old_impact,new_impact)new_impact
        update_sql = "UPDATE " + insert_db\
                     + " SET id='%d',updated='%s',go_mod='%d',v_dir='%d',v_num='%d',"\
                       "path_match='%d',r_type='%d',num1_0='%d',list1_0='%s',num1_1='%d',list1_1='%s',break1='%d'," \
                       "break_list1='%s',num2_0='%d',list2_0='%s',num2_1='%d',list2_1='%s',break2='%d'," \
                       "break_list2='%s',num3_0='%d',list3_0='%s',num3_1='%d',list3_1='%s',break3='%d'," \
                       "break_list3='%s',num4_0='%d',list4_0='%s',num4_1='%d',list4_1='%s',break4='%d'," \
                       "break_list4='%s',old_impact='%d',new_impact='%d' " \
                       "WHERE id='%d'" % (time_num, updated, go_mod, v_dir, v_num, path_match, r_type, bug_type[0],
                                          bug_list[0], bug_type[1], bug_list[1], break_type[0], break_list[0],
                                          bug_type[2], bug_list[2], bug_type[3], bug_list[3], break_type[1],
                                          break_list[1], bug_type[4], bug_list[4], bug_type[5], bug_list[5],
                                          break_type[2], break_list[2], bug_type[6], bug_list[6], bug_type[7],
                                          bug_list[7], break_type[3], break_list[3], impact[0], impact[1], result_id)
        db = pymysql.connect(host, user, password, db_name)
        try:
            update_cursor = db.cursor()
            # 执行sql语句
            update_cursor.execute(update_sql)
            db.commit()
            update_cursor.close()
            print('update ', insert_db, ' successful:', fullname, '@', v_name, '@@', v_hash)
            update_s = update_s + 1
        except Exception as exp:
            print('update ', insert_db, ' error exception is:', exp)
            print('update ', insert_db, ' error sql:', update_sql)
            update_e = update_e + 1
            # 发生错误时回滚
            db.rollback()
        db.close()
    else:
        print('check ', insert_db, ' error:', fullname, '@', v_name, '@@', v_hash, '---------------------------------'
                                   '----------------------------------------------------------------')
        check_e = check_e + 1
    return check_e, insert_e, update_e, insert_s, update_s


# 查重
def check_check_go_repos_db(fullname, v_name, v_hash, check_type, host, user, password, db_name, insert_db):
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT id FROM " + insert_db + " WHERE (full_name='%s' AND v_name='%s' AND v_hash='%s' AND " \
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
        print("check ", insert_db, " error", fullname, '@', v_name, '@@', v_hash, ':',
              exp, '--------------------------------------------------------------------------------------------------')
        return -1


# def update_need_check_db(full_name, v_name, v_hash, check_repo_issue, host, user, password, db_name, update_s,
#                          update_e, go_mod):
#     update_sql = "UPDATE need_check_go_repos_gt SET need_check=1,go_mod='%d' WHERE full_name='%s' AND v_name='%s' " \
#                  "AND v_hash='%s' AND check_repo_issue='%s'" % (go_mod, full_name, v_name, v_hash, check_repo_issue)
#
#     db = pymysql.connect(host, user, password, db_name)
#     try:
#         update_cursor = db.cursor()
#         # 执行sql语句
#         update_cursor.execute(update_sql)
#         db.commit()
#         update_cursor.close()
#         print('update need_check_go_repos_gt successful:', full_name, '@', v_name, '@@', v_hash)
#         update_s = update_s + 1
#     except Exception as exp:
#         print('update need_check_go_repos_gt error exception is:', exp)
#         print('update need_check_go_repos_gt error sql:', update_sql)
#         update_e = update_e + 1
#         # 发生错误时回滚
#         db.rollback()
#     db.close()
#     return update_s, update_e


def get_ignore_nc_list(host, user, password, db_name, headers, issue):
    check_db_name = 'ignore_repo'
    top_num = 1400
    # check_type = check_db_name + '@top' + str(top_num) + '--old'
    check_type = 'new2-2'
    need_check_list = []
    i_sql = "SELECT i_repo_name,v_name,v_hash,sub_mod FROM ignore_repo WHERE reason='wait-check-old'"
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(i_sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            # num = len(check_result)
            for r in check_result:
                (stars, forks, updated, v_name, semantic, issue) = get_repo_detail(r[0], headers, issue)
                if r[1]:
                    v_name = r[1]
                # else:
                #     v_name = ''
                if r[2]:
                    v_hash = r[2]
                else:
                    v_hash = ''
                if r[3]:
                    mod_name = r[0] + '/' + r[3]
                else:
                    mod_name = r[0]
                need_check_list.append([mod_name, v_name, v_hash, stars, forks, updated, semantic])
    except Exception as exp:
        print("get_ignore_nc_list from ", check_db_name, " error",
              exp, '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
    return need_check_list, check_type, issue


# 降序，排序，双参照
def get_need_check_list(host, user, password, db_name, headers, issue):
    check_db_name = 'github_go_repos_20200529'
    top_num = 200
    check_type = check_db_name + '@top' + str(top_num) + '--new'
    need_check_list = []
    # sql = "SELECT full_name,v_name,v_hash,check_repo_issue " \
    #       "FROM need_check_go_repos_gt WHERE need_check=0 AND go_mod=-1"
    # sql = "SELECT full_name,v_name FROM github_go_repos_20200529 ORDER BY stars desc,forks desc LIMIT 10"
    # sql = "SELECT full_name,v_name FROM " + check_db_name + " ORDER BY stars desc,forks desc LIMIT 200"
    #
    sql = "SELECT full_name,v_name FROM " + check_db_name \
          + " WHERE full_name NOT IN (SELECT full_name FROM check_go_repos_20200529) " \
            "AND full_name NOT IN (SELECT i_repo_name FROM ignore_repo) " \
            "AND go_mod<2 AND stars>60 ORDER BY stars desc,forks desc LIMIT 800"
    # sql = "SELECT full_name,v_name FROM " + check_db_name \
    #       + " WHERE full_name IN (SELECT sc.full_name " \
    #         "FROM (SELECT full_name FROM " + check_db_name \
    #       + " ORDER BY stars desc,forks desc LIMIT 200)AS sc ) " \
    #         "AND full_name NOT IN (SELECT i_repo_name FROM ignore_repo) AND go_mod<2 ORDER BY stars desc,forks desc"
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
                (stars, forks, updated, v_name, semantic, issue) = get_repo_detail(r[0], headers, issue)
                need_check_list.append([r[0], v_name, stars, forks, updated, semantic])
    except Exception as exp:
        print("get_need_check_list from ", check_db_name, " error",
              exp, '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
    return need_check_list, check_type, issue


def main():
    insert_e = 0
    search_e = 0
    check_e = 0
    update_e = 0
    insert_s = 0
    update_s = 0
    issue_l = ''
    time_w = 1.4
    user = 'root'
    host = '47.254.86.255'
    password = 'Ella1996'
    db_name = 'githubspider'
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    time_s = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    counter = 0
    insert_db = 'check_go_repos_20200529'
    print('star:', time_s)

    # (ignore_nc_list, check_type, issue) = get_ignore_nc_list(host, user, password, db_name, headers, issue_l)
    # print(check_type, '######################################################################################'
    #                   '#############################################################################################')
    # for repo_check in ignore_nc_list:
    #     # [mod_name, r[1], r[2], stars, forks, updated, semantic]
    #     mod_name = repo_check[0]
    #     repo_version = repo_check[1]
    #     repo_mes_list = [repo_check[3], repo_check[4], repo_check[5], repo_check[6]]
    #     repo_hash = repo_check[2]
    #     counter = counter + 1
    #     if mod_name:
    #         print(counter, '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    #         (search_e, insert_e, check_e, update_e, insert_s, update_s,
    #          issue_l) = check_repo_from_api(mod_name, repo_version, repo_hash, repo_mes_list, host, user,
    #                                         password, db_name, search_e, insert_e, check_e, update_e, insert_s,
    #                                         update_s, issue_l, time_w, check_type, insert_db)
    #     else:
    #         print('repo_name 不正确')
    #
    # time_now = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    # print('time now: ', time_now)

    (need_check_list, check_type, issue) = get_need_check_list(host, user, password, db_name, headers, issue_l)
    print(check_type, '######################################################################################'
          '#############################################################################################')

    counter = 0
    for repo_check in need_check_list:
        # count = count + 1
        # [r[0], v_name, stars, forks, updated, semantic]
        repo_fullname = repo_check[0]
        repo_version = repo_check[1]
        repo_mes_list = [repo_check[2], repo_check[3], repo_check[4], repo_check[5]]
        repo_hash = ''
        counter = counter + 1
        if repo_fullname:
            print(counter, '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
            (search_e, insert_e, check_e, update_e, insert_s, update_s,
             issue_l) = check_repo_from_api(repo_fullname, repo_version, repo_hash, repo_mes_list, host, user,
                                            password, db_name, search_e, insert_e, check_e, update_e, insert_s,
                                            update_s, issue_l, time_w, check_type, insert_db)
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