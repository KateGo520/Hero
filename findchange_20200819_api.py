import base64
import json
import re
import time
from concurrent.futures.thread import ThreadPoolExecutor
from urllib.request import Request, urlopen
import pymysql


def get_results(url, headers):
    request = Request(url, headers=headers)
    response = urlopen(request).read()
    result = json.loads(response.decode())
    return result


# 获取版本信息
def get_version(releases_url, headers):
    v_url = releases_url.replace('{/id}', '')
    version_result = get_results(v_url, headers)
    # v_id = ''
    v_name = ''
    semantic = True  # 存：是否为语义版本，也是判断是否为伪版本
    # 判断是否为伪版本
    if version_result:
        v_url = releases_url.replace('{/id}', '/latest')
        try:
            result = get_results(v_url, headers)
        except Exception as exp:
            result = version_result[0]
            print("When find version: get search error", exp, '-------------------------------------------------------'
                                                              '-------------------------------------------------------')
        v_name = result['tag_name']
    else:
        semantic = False
        # print('伪版本')
    return v_name, semantic


def deal_require_path(repo_name, repo_version):
    # 检查模块是否为主模块，还是子模块，拆分出存储库名，和子模块的相对路径
    main_mod = re.findall(r"^([^/]+?/[^/]+?)/.+?", repo_name)
    if main_mod:  # 说明是子模块的导入路径
        main_mod_name = main_mod[0]
        sub_mod_path = repo_name.replace(main_mod_name, '')
    else:
        main_mod_name = repo_name
        sub_mod_path = ''

    # 检查子模块的相对路径中是否有siv
    imp_siv = ''
    imp_siv_c = re.findall(r"(/v\d+?)$", repo_name)
    if imp_siv_c:
        imp_siv = imp_siv_c[0]  # 导入路径中存在siv

    # 获取主版本号：
    imp_main_v = re.findall(r"^v(\d+?)\.", repo_version)
    if imp_main_v:
        v_siv = imp_main_v[0]
    else:
        if re.findall(r"^v(\d+?)$", repo_version):
            imp_main_v = re.findall(r"^v(\d+?)$", repo_version)
            v_siv = imp_main_v[0]
        else:
            v_siv = '-1'

    # 判断是否为伪版本,如果是，获取哈希值
    not_semantic = re.findall(r"^v\d+?\.\d+?\.\d+?-*[^-]*?-[0-9.]+?-([A-Za-z0-9]+?)$", repo_version)
    # bug_main_version = ''
    if not_semantic:
        repo_version = not_semantic[0]

    print(repo_version, '的主版本号为：', v_siv)
    return main_mod_name, sub_mod_path, imp_siv, repo_version, v_siv


# 获取该路径下的存储库中是否有go.mod文件,主要子目录（SIV）
def get_go_mod(fullname, name, semantic, headers, issue):
    page_detail = []
    # 先判断有无子模块
    (main_mod_name, sub_mod_path, imp_siv, repo_version, v_siv) = deal_require_path(fullname, name)
    # v_siv_num = int(v_siv)
    if sub_mod_path:
        print('1.拆分出主模块路径和子模块的相对路径：', main_mod_name, sub_mod_path, '**********************************'
                                                                   '**get go.mod*******')
        d_url = 'https://api.github.com/repos/' + main_mod_name + '/contents' + sub_mod_path + '?ref=' + repo_version
        try:
            page_detail = get_results(d_url, headers)
        except Exception as exp:
            print("2.可能是版本获取不到：", exp, '************************************get go.mod*******')
            d_url = 'https://api.github.com/repos/' + main_mod_name + '/contents' + sub_mod_path
            try:
                page_detail = get_results(d_url, headers)
            except Exception as exp:
                sub_mod_path = ''
                print('3.可能不是子模块：', exp, '************************************get go.mod*******')
    if sub_mod_path == '':
        d_url = 'https://api.github.com/repos/'
        if semantic:
            d_url = d_url + fullname + '/contents?ref=' + repo_version
        else:
            d_url = d_url + fullname + '/contents'
        # print(d_url)
        try:
            page_detail = get_results(d_url, headers)
        except Exception as exp:
            print("1.可能是版本获取不到：", exp, '************************************get go.mod*******')
            d_url = 'https://api.github.com/repos/' + fullname + '/contents'
            try:
                page_detail = get_results(d_url, headers)
            except Exception as exp:
                print("2.可能是repo名不准确：", exp, '****************************get go.mod**w********')
                page_detail = []
                issue = issue + '<' + 'get_go_mod:' + fullname + '>'

    go_mod = 0  # 存：是否有go.mod的指标。【0无；1有但为空；2有且非空】
    go_mod_url = ''
    version_dir = 0  # 存：是否有主要子目录的指标。【0无；1有但为空；2有且非空】
    # main_version = ''
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

    return go_mod, v_siv, go_mod_url, version_dir, issue


# k8s  github
def get_go_mod_detail(fullname, name, semantic, headers, issue):
    # k8s = 0
    (go_mod, v_siv, go_mod_url, version_dir, issue) = get_go_mod(fullname, name, semantic, headers, issue)
    go_mod_module = ''
    if v_siv.isdigit() and v_siv != '-1':
        # 主版本为数字（整数），且>=2
        version_number = int(v_siv)
    else:
        # 主版为非数字
        version_number = -1
    path_match = -1  # 无go.mod文件的，不存在匹配问题，默认为-1
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
    # version_number, path_match
    return go_mod_module, version_number, path_match, go_mod, v_siv, go_mod_url, version_dir, issue


def get_onepage_info(repo_name, host, user, password, db_name, search_e, insert_e, check_e, update_e, insert_s,
                     update_s, time_w, issue, insert_db):
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': 'token abdd967d350662632381f130cd62268ed2f961a1'}
    one_page_url = 'https://api.github.com/repos/' + repo_name
    try:
        i = get_results(one_page_url, headers)
        releases_url = i['releases_url']  # 获取版本信息api
        item_commit = i['commits_url'].replace('{/number}', '').replace('{/sha}', '')
        item_issues = i['issues_url'].replace('{/number}', '')
        time.sleep(0.6)
        (item_updated, search_e) = get_commit_time(item_commit, headers, search_e)
        (item_issues_count, search_e) = get_issue_count(item_issues, headers, search_e)
        # 获取依赖管理信息
        time.sleep(0.6)
        (mod_num, tool_num, search_e) = get_dm_msg(repo_name, headers, search_e)
        (v_name, semantic) = get_version(releases_url, headers)
        # (go_mod,version_dir,version_number,path_match) = get_detailpage(item_fullname, v_name,
        # semantic, headers)
        (go_mod_module, version_number, path_match, go_mod, main_version, go_mod_url, version_dir,
         issue) = get_go_mod_detail(repo_name, v_name, semantic, headers, issue)
        time.sleep(time_w)
        print(repo_name, ": ", "【V】", v_name, go_mod, version_dir, version_number, path_match, 'DM：', mod_num, tool_num)
        (insert_e, check_e, update_e, insert_s,
         update_s) = insert_info(repo_name, item_updated, v_name, semantic, go_mod, version_dir,
                                 version_number, path_match, item_issues_count, mod_num, tool_num,
                                 host, user, password, db_name, insert_e, check_e, update_e,
                                 insert_s, update_s, insert_db)

    except Exception as exp:
        print("get search ", insert_db, " error", repo_name, ':', exp)
        search_e = search_e + 1
    return search_e, insert_e, check_e, update_e, insert_s, update_s, issue


# 获取最新的commit更新日期
def get_commit_time(commit_url, headers, search_e):
    c_date_num = -1
    try:
        commit_result = get_results(commit_url, headers)
        if commit_result:
            last_commit_time = commit_result[0]['commit']['committer']
            date_str = last_commit_time['date']
            # 2020-08-18T13:19:33Z

            c_date_re = re.findall(r"(\d+?-\d+?-\d+?)T", date_str)
            if c_date_re:
                c_date = c_date_re[0].replace('-', '')
                c_date_num = int(c_date)
                # print(c_date_num, type(c_date_num))
        else:
            c_date_num = 0
    except Exception as exp:
        print("获取最新的commit更新日期失败", exp, '***********************************************')
        search_e = search_e + 1

    return c_date_num, search_e


# 获取依赖信息
def get_dm_msg(repo_name, headers, search_e):
    mod_count = -1
    tool_count = -1
    # 检测获取go.mod数
    url_mod = 'https://api.github.com/search/code?q=repo:' + repo_name + '+filename:go.mod'
    try:
        results_mod = get_results(url_mod, headers)
        mod_count = results_mod['total_count']
        if mod_count > 30:
            for page in range(1, 11):
                url_mod = url_mod + '&page=' + str(page) + '&per_page=100'
                results_mod = get_results(url_mod, headers)
                items = results_mod['items']
                if items:
                    vendor = 0  # 查vendor的计数器
                    not_g0_mod = 0
                    for i in items:
                        mod_path = i['path']
                        file_name = i['name']
                        mod_path = mod_path.replace(file_name, '')
                        if file_name != 'go.mod':
                            not_g0_mod = not_g0_mod + 1
                        elif re.findall(r"vendor/", mod_path) or re.findall(r"/vendor/", mod_path):
                            vendor = vendor + 1
                    mod_count = mod_count - vendor - not_g0_mod
                else:
                    break
        else:
            items = results_mod['items']
            if items:
                vendor = 0  # 查vendor的计数器
                not_g0_mod = 0
                for i in items:
                    mod_path = i['path']
                    file_name = i['name']
                    mod_path = mod_path.replace(file_name, '')
                    if file_name != 'go.mod':
                        not_g0_mod = not_g0_mod + 1
                    elif re.findall(r"vendor/", mod_path) or re.findall(r"/vendor/", mod_path):
                        vendor = vendor + 1
                mod_count = mod_count - vendor - not_g0_mod
                # print('no vendor go.mod count:', mod_count, ' vendor go.mod count:', vendor)
            else:
                mod_count = 0

    except Exception as exp:
        print("获取go.mod数失败", exp, '***********************************************')
        search_e = search_e + 1

    # 获取第三方工具数
    tool_list = ['Godeps.json', 'vendor.conf', 'vendor.json', 'glide.toml', 'Gopkg.toml', 'Godep.json']
    url_tool = 'https://api.github.com/search/code?q=repo:'
    url_tool = url_tool + repo_name + '+filename:Godeps.json+filename:vendor.conf+filename:vendor.json+' \
                                      'filename:glide.toml+filename:Gopkg.toml+filename:Godep.json'
    try:
        results_tool = get_results(url_tool, headers)
        tool_count = results_tool['total_count']
        if tool_count > 30:
            for page in range(1, 11):
                url_tool = url_tool + '&page=' + str(page) + '&per_page=100'
                results_tool = get_results(url_tool, headers)
                items = results_tool['items']
                if items:
                    vendor = 0  # 查vendor的计数器
                    not_tool = 0
                    for i in items:
                        tool_path = i['path']
                        file_name = i['name']
                        tool_path = tool_path.replace(file_name, '')
                        if file_name not in tool_list:
                            not_tool = not_tool + 1
                        elif re.findall(r"vendor/", tool_path) or re.findall(r"/vendor/", tool_path):
                            vendor = vendor + 1
                    tool_count = tool_count - vendor - not_tool
                else:
                    break
        else:
            items = results_tool['items']
            if items:
                vendor = 0  # 查vendor的计数器
                not_tool = 0
                for i in items:
                    tool_path = i['path']
                    file_name = i['name']
                    tool_path = tool_path.replace(file_name, '')
                    if file_name not in tool_list:
                        not_tool = not_tool + 1
                    elif re.findall(r"vendor/", tool_path) or re.findall(r"/vendor/", tool_path):
                        vendor = vendor + 1
                tool_count = tool_count - vendor - not_tool
                # print('no vendor tool count:', tool_count, ' vendor tool count:', vendor)
            else:
                tool_count = 0
    except Exception as exp:
        print("获取tool数失败", exp, '***********************************************')
        search_e = search_e + 1
    return mod_count, tool_count, search_e


# 获取issues总数
def get_issue_count(issue_url, headers, search_e):
    count = -1
    try:
        issue_result = get_results(issue_url, headers)
        if issue_result:
            issues_count = issue_result[0]
            count = issues_count['number']
            # print(count, type(count))
        else:
            count = 0

    except Exception as exp:
        print("获取issues总数失败", exp, '***********************************************')
        search_e = search_e + 1
    return count, search_e


def get_need_check_list(host, user, password, db_name, issue):
    check_db_name = 'github_go_repos_20200819'
    need_check_list = []
    sql = "SELECT full_name FROM " + check_db_name + " WHERE r_type=0 OR issue_num=-1 OR updated_time=-1 OR " \
                                                     "mod_num=-1 OR tool_num=-1 " \
                                                     "ORDER BY stars desc,forks desc LIMIT 5000"
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
                need_check_list.append(r[0])
    except Exception as exp:
        print("get_need_check_list from ", check_db_name, " error",
              exp, '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
    return need_check_list, issue


def judge_repo_type(go_mod, version_number, path_match, version_dir):
    r_type = 0
    if go_mod >= 2:
        if 2 > version_number >= 0:
            if path_match == 2:
                r_type = 1
        if version_number >= 2:
            if version_dir == 0:
                if path_match == 2:
                    r_type = 2
                if path_match == 1:
                    r_type = 4
            elif version_dir == 2:
                if path_match == 2:
                    r_type = 3
                if path_match == 1:
                    r_type = 10
            else:  # version_dir == 1
                r_type = 8

    elif go_mod < 2:
        if 2 > version_number >= 0:
            r_type = 7
        if version_number >= 2:
            if version_dir == 2:
                r_type = 8  # 空go.mod文件全当不存在
            elif version_dir == 1:
                r_type = 8
            else:  # version_dir == 0
                r_type = 9

    if version_number < 0:
        if go_mod < 2:
            r_type = 6
        else:
            r_type = 5
    if path_match == 0:
        r_type = 10
    # print(r_type)
    return r_type


# 插入数据库的方法
def insert_info(name, up_time, v_name, semantic, go_mod, v_dir, v_num, path_match, issue_num, mod_num, tool_num,
                host, user, password, db_name, insert_e, check_e, update_e, insert_s, update_s, insert_db):
    r_type = judge_repo_type(go_mod, v_num, path_match, v_dir)
    if semantic:
        v_semantic = 1
    else:
        v_semantic = 0
    check_result = check_name(name, host, user, password, db_name, insert_db)
    if check_result == 1:
        # 有该存储库但信息不同
        # if check_result == 3:
        #     result_list
        #     time_num = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        #     time_num = int(time_num)
        #     change_list = [time_num, name, result_list[0], result_list[1], up_time, v_name, result_list[3], r_type]
        #     (insert_e, insert_s) = insert_repo_change(change_list, insert_e, insert_s, host, user, password, db_name)

        update_sql = "UPDATE " + insert_db + " SET issue_num='%d',updated_time='%s',v_name='%s',semantic='%d'," \
                                             "go_mod='%d',mod_num='%d',tool_num='%d',version_dir='%d'," \
                                             "version_number='%d',path_match='%d',r_type='%d' " \
                                             "WHERE full_name='%s'" % (issue_num, up_time, v_name, v_semantic, go_mod,
                                                                       mod_num, tool_num, v_dir, v_num, path_match,
                                                                       r_type, name)
        db = pymysql.connect(host, user, password, db_name)
        try:
            update_cursor = db.cursor()
            # 执行sql语句
            update_cursor.execute(update_sql)
            db.commit()
            update_cursor.close()
            print('update ', insert_db, ' successful', name)
            update_s = update_s + 1
        except Exception as exp:
            print('update ', insert_db, ' error exception is:', exp)
            print('update ', insert_db, ' error sql:', update_sql)
            update_e = update_e + 1
            # 发生错误时回滚
            db.rollback()
        db.close()
    else:
        print('check ', insert_db, ' error', name, 'db already has ', check_result)
        check_e = check_e + 1
    return insert_e, check_e, update_e, insert_s, update_s


# 查重
def check_name(r_name, host, user, password, db_name, insert_db):
    check_num = -1
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT count(*) FROM " + insert_db + " WHERE full_name='%s'" % r_name
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            check_num = check_result[0][0]
        print("check " + insert_db + " result:", check_num)
        return check_num
    except Exception as exp:
        print("check repos name from ", insert_db, " error:", exp)
        return check_num


def main():
    search_e = 0
    insert_e = 0
    check_e = 0
    update_e = 0
    insert_s = 0
    update_s = 0
    issue_l = ''
    host = '47.254.86.255'
    user = 'root'
    password = 'Ella1996'
    db_name = 'githubspider'
    time_w = 1.4
    time_s = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    part = 1
    insert_db = 'github_go_repos_20200819'

    # name_l = ['xtaci/kcptun', 'txthinking/brook']
    # for name in name_l:
    #     (search_e, insert_e, check_e, update_e, insert_s, update_s,
    #      issue_l) = get_onepage_info(name, host, user, password, db_name, search_e, insert_e, check_e, update_e,
    #                                  insert_s, update_s, time_w, issue_l, insert_db)

    (need_check_list, issue_l) = get_need_check_list(host, user, password, db_name, issue_l)
    c = 0
    for repo_name in need_check_list:
        c = c + 1
        print('REPO ', c, repo_name)
        (search_e, insert_e, check_e, update_e, insert_s, update_s,
         issue_l) = get_onepage_info(repo_name, host, user, password, db_name, search_e, insert_e, check_e, update_e,
                                     insert_s, update_s, time_w, issue_l, insert_db)

    print('searchError', search_e, 'insertError', insert_e, 'checkError', check_e, 'updateError', update_e)
    print('insert successfully:', insert_s)
    print('update successfully:', update_s)
    print('other issues:', issue_l)
    time_e = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    print(time_s, '->', time_e)


if __name__ == '__main__':
    # 47.254.86.255
    # host = '47.254.86.255'
    # user = 'root'
    # password = 'Ella1996'
    # db_name = 'githubspider'
    # 声明线程池
    executor = ThreadPoolExecutor(6)
    main()