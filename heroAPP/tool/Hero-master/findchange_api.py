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


# 获取详情页的：go.mod文件【是否有，module声明】，版本号，子文件夹/vN，module声明的路径是否符合模块机制的要求
# def get_detailpage(fullname, name, semantic, headers):
#     # d_url = 'https://raw.githubusercontent.com/'
#     d_url = 'https://api.github.com/repos/'
#     if semantic:
#         d_url = d_url + fullname + '/contents?ref=' + name
#     else:
#         d_url = d_url + fullname + '/contents'
#     print(d_url)
#     try:
#         page_detail = get_results(d_url, headers)
#     except Exception as exp:
#         print("When find detail page: get search error", exp)
#         d_url = 'https://api.github.com/repos/' + fullname + '/contents'
#         page_detail = get_results(d_url, headers)
#     main_version = name.split('.')[0].replace('v', '')
#     sub_dir = 'v' + main_version
#     # file_num = len(page_detail)
#     go_mod = 0  # 存：是否有go.mod的指标。【0无；1有但为空；2有且非空】
#     version_dir = 0  # 存：是否有主要子目录的指标。【0无；1有但为空；2有且非空】
#     go_mod_url = ''
#     # sub_dir_url = ''
#     for f in page_detail:
#         # 判断有无go.mod文件
#         if f['name'] == 'go.mod':
#             # print('yes')
#             if f['size'] == 0:
#                 go_mod = 1
#             else:
#                 go_mod = 2
#             go_mod_url = f['url']
#         # 判断有无子目录/vN
#         if f['name'] == sub_dir or f['name'] == ('.' + sub_dir) and f['type'] == 'dir':
#             # print('yes')
#             sub_dir_result = get_results(f['url'], headers)
#             if len(sub_dir_result):
#                 print('have sub direct')
#                 version_dir = 2
#                 go_mod = 0
#                 for sub_dir_f in sub_dir_result:
#                     # 判断有无go.mod文件
#                     if sub_dir_f['name'] == 'go.mod':
#                         print('yes')
#                         if sub_dir_f['size'] == 0:
#                             go_mod = 1
#                         else:
#                             go_mod = 2
#                         go_mod_url = sub_dir_f['url']
#             else:
#                 print('nothing in sub direct')
#                 version_dir = 1
#     if main_version.isdigit() and int(main_version) > 1:
#         # 主版本为数字（整数），且>=2
#         version_number = 2
#     elif main_version.isdigit() and int(main_version) < 2:
#         # 主版本为数字（整数），且<2
#         version_number = 1
#     else:
#         # 主版为非数字
#         version_number = 0
#     # version_number：存：主版本分类指标。
#     # print(main_version)
#     path_match = -1  # 无go.mod文件的，不存在匹配问题，默认为-1
#     # path_match：存：go.mod文件中的module声明的模块路径与Go Modules机制要求的模块路径是否一致的指标
#     # 判断所有有go.mod文件的，module声明的模块路径与Go Modules要求的是否一致
#     if go_mod == 2:  # 如果有非空的go.mod文件
#         print(go_mod_url)
#         go_mod_result = get_results(go_mod_url, headers)  # 获取go.mod内容
#         # 解码后，使用正则表达式，获取module声明的模块路径
#         go_mod_content = base64.b64decode(go_mod_result['content'])
#         module = re.findall(r"module\s(.+?)\s", go_mod_content.decode(), re.M)
#         if module:
#             go_mod_module = module[0]  # go.mod中module声明的模块路径
#         else:
#             module = go_mod_content.decode()
#             go_mod_module = module.replace('module ', '')
#         print(go_mod_module)
#         module_path = 'github.com/' + fullname  # 模块机制要求的不带语义版本的路径
#         if version_number == 2:
#             module_version_path = 'github.com/' + fullname + '/' + sub_dir  # 按照module要求的带语义版本的模块路径
#             # print(module_version_path)
#             if go_mod_module == module_version_path:
#                 path_match = 2
#             elif go_mod_module == module_path:
#                 path_match = 1
#             else:
#                 path_match = 0
#         else:
#             if go_mod_module == module_path:
#                 path_match = 2
#             else:
#                 path_match = 0
#     # print(go_mod, version_dir, version_number, path_match, semantic)
#     return go_mod, version_dir, version_number, path_match


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


# 获取主页的项目信息
def get_mainpage_info(url, headers, host, user, password, db_name, search_e, insert_e, check_e, update_e, insert_s,
                      update_s, time_w, issue):
    try:
        print(url)
        results = get_results(url, headers)
        items = results['items']
        c = 0  # 计数器
        for i in items:
            item_fullname = i['full_name']  # 存：存储库完整名字
            item_stars = i['stargazers_count']  # 存：标星数量
            item_forks = i['forks_count']  # 存：forks数量
            item_size = i['size']  # 存：存储库大小
            item_created = i['created_at']  # 存：存储创建时间
            item_updated = i['updated_at']  # 存：数据库更新时间
            releases_url = i['releases_url']  # 获取版本信息api
            # item_user = i['owner']['login']
            c = c + 1
            (v_name, semantic) = get_version(releases_url, headers)
            # (go_mod,version_dir,version_number,path_match) = get_detailpage(item_fullname, v_name, semantic, headers)
            (go_mod_module, version_number, path_match, go_mod, main_version, go_mod_url, version_dir,
             issue) = get_go_mod_detail(item_fullname, v_name, semantic, headers, issue)
            time.sleep(time_w)
            print(c, ": ", item_fullname, item_stars, item_forks, item_size, "【V】", v_name, go_mod, version_dir,
                  version_number, path_match)
            (insert_e, check_e, update_e, insert_s,
             update_s) = insert_info(item_fullname, item_stars, item_forks, item_size, item_created, item_updated,
                                     v_name, semantic, go_mod, version_dir, version_number, path_match, host, user,
                                     password, db_name, insert_e, check_e, update_e, insert_s, update_s)
    except Exception as exp:
        print("get search error", exp)
        search_e = search_e + 1
    print('--------------------------------------------------------------')
    return search_e, insert_e, check_e, update_e, insert_s, update_s, issue


def get_onepage_info(name, headers, host, user, password, db_name, search_e, insert_e, check_e, update_e, insert_s,
                     update_s, time_w, issue):
    # headers = {'User-Agent': 'Mozilla/5.0',
    #            'Content-Type': 'application/json',
    #            'Accept': 'application/json',
    #            'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    one_page_url = 'https://api.github.com/repos/' + name
    try:
        one_page_results = get_results(one_page_url, headers)
        item_fullname = one_page_results['full_name']  # 存：存储库完整名字
        item_stars = one_page_results['stargazers_count']  # 存：标星数量
        item_forks = one_page_results['forks_count']  # 存：forks数量
        item_size = one_page_results['size']  # 存：存储库大小
        item_created = one_page_results['created_at']  # 存：存储创建时间
        item_updated = one_page_results['updated_at']  # 存：数据库更新时间
        releases_url = one_page_results['releases_url']  # 获取版本信息api
        (v_name, semantic) = get_version(releases_url, headers)
        # (go_mod,version_dir,version_number,path_match) = get_detailpage(item_fullname, v_name, semantic, headers)
        (go_mod_module, version_number, path_match, go_mod, main_version, go_mod_url, version_dir,
         issue) = get_go_mod_detail(item_fullname, v_name, semantic, headers, issue)
        time.sleep(time_w)
        print(item_fullname, ": ", item_stars, item_forks, item_size, "【V】", v_name, go_mod, go_mod_module,
              version_dir, version_number, path_match)
        (insert_e, check_e, update_e, insert_s,
         update_s) = insert_info(item_fullname, item_stars, item_forks, item_size, item_created, item_updated,
                                 v_name, semantic, go_mod, version_dir, version_number, path_match, host, user,
                                 password, db_name, insert_e, check_e, update_e, insert_s, update_s)
    except Exception as exp:
        print("get search error", name, ':', exp)
        search_e = search_e + 1
    return search_e, insert_e, check_e, update_e, insert_s, update_s, issue


# 获取搜索主页，使用API
def get_mainpage(part, host, user, password, db_name, search_e, insert_e, check_e, update_e, insert_s, update_s,
                 time_w, issue):
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    part = 1
    if part == 1:
        # 141..204
        list_1 = ['1420..67200', '800..1419', '430..799', '280..429', '205..279', '155..204', '141..154', '113..140',
                  '92..112', '78..91', '67..77', '58..66', '51..57', '45..50', '41..44', '37..40', '34..36', '31..33',
                  '29..30', '27..28', '25..26', '23..24', '22', '21', '20', '19', '18', '17', '16']
        # 获取star数为16--67200
        # 0,28  14
        for l1_num in range(0, 1):
            # 1,11  100
            # list_e = [3, 10]
            for page_num in range(1, 11):
                url_1 = 'https://api.github.com/search/repositories?q=language:go+stars:%s&' \
                        'sort=stars&page=%s&per_page=100' % (list_1[l1_num], page_num)
                print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
                      '+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                print(list_1[l1_num], page_num)
                # print(list_1[l1_num], page_num)
                try:
                    print(url_1)
                    results = get_results(url_1, headers)
                    items = results['items']
                    if items:
                        c = 0  # 计数器
                        for i in items:
                            item_fullname = i['full_name']  # 存：存储库完整名字
                            item_stars = i['stargazers_count']  # 存：标星数量
                            item_forks = i['forks_count']  # 存：forks数量
                            item_size = i['size']  # 存：存储库大小
                            item_created = i['created_at']  # 存：存储创建时间
                            item_updated = i['updated_at']  # 存：数据库更新时间
                            releases_url = i['releases_url']  # 获取版本信息api
                            # item_user = i['owner']['login']
                            c = c + 1
                            (v_name, semantic) = get_version(releases_url, headers)
                            # (go_mod,version_dir,version_number,path_match) = get_detailpage(item_fullname, v_name,
                            # semantic, headers)
                            (go_mod_module, version_number, path_match, go_mod, main_version, go_mod_url, version_dir,
                             issue) = get_go_mod_detail(item_fullname, v_name, semantic, headers, issue)
                            time.sleep(time_w)
                            print(c, ": ", item_fullname, item_stars, item_forks, item_size, "【V】", v_name, go_mod,
                                  version_dir, version_number, path_match)
                            (insert_e, check_e, update_e, insert_s,
                             update_s) = insert_info(item_fullname, item_stars, item_forks, item_size, item_created,
                                                     item_updated,
                                                     v_name, semantic, go_mod, version_dir, version_number, path_match,
                                                     host, user,
                                                     password, db_name, insert_e, check_e, update_e, insert_s, update_s)
                    else:
                        break
                    if page_num == 10 and len(items) >= 100:
                        print(list_1[l1_num], page_num, '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'
                                                        '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')

                except Exception as exp:
                    print("get search error", exp, url_1)
                    search_e = search_e + 1
                print('--------------------------------------------------------------')
                time.sleep(time_w)
    elif part == 2:
        # 获取star数为0--15,forks数为7--800
        list_2 = ['13..800', '10..12', '8..9', '7']
        # 0,4
        for l2_num in range(0, 1):
            # 1,11       100
            for page_num in range(3, 4):
                url_2 = 'https://api.github.com/search/repositories?q=language:go+stars:0..15+forks:%s&sort=stars&' \
                        'page=%s&per_page=10' % (list_2[l2_num], page_num)
                (search_e, insert_e, check_e, update_e, insert_s, update_s,
                 issue) = get_mainpage_info(url_2, headers, host, user, password, db_name, search_e, insert_e,
                                            check_e, update_e, insert_s, update_s, time_w, issue)
                time.sleep(time_w)
    else:
        # 获取剩余项目  27
        list_3_s = ['3..15', '0..2', '6..15', '3..5', '9..15', '5..8', '1..3', '0', '11..15', '8..10', '6..7', '4..5',
                    '3', '2', '1', '0', '14..15', '11..15', '12..13', '9..10', '10..11', '9..11', '8', '9', '7..8',
                    '7', '7']
        list_3_f = ['6', '5..6', '5', '5', '4', '4', '4', '4', '3', '3', '3', '3', '3', '3', '3', '3', '1..2', '0',
                    '1..2', '0', '1', '2', '0', '1', '2', '0', '1']
        # 0,27
        for l3_num in range(0, 1):
            # 1,11     100
            for page_num in range(1, 10):
                url_3 = 'https://api.github.com/search/repositories?q=language:go+stars:%s+forks:%s&sort=stars&' \
                        'page=%s&per_page=10' % (list_3_s[l3_num], list_3_f[l3_num], page_num)
                (search_e, insert_e, check_e, update_e, insert_s, update_s,
                 issue) = get_mainpage_info(url_3, headers, host, user, password, db_name, search_e, insert_e,
                                            check_e, update_e, insert_s, update_s, time_w, issue)
                time.sleep(time_w)
    return search_e, insert_e, check_e, update_e, insert_s, update_s, issue


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
def insert_info(name, stars, forks, size, c_time, up_time, v_name, semantic, go_mod, v_dir, v_num, path_match, host,
                user, password, db_name, insert_e, check_e, update_e, insert_s, update_s):
    r_type = judge_repo_type(go_mod, v_num, path_match, v_dir)
    if semantic:
        v_semantic = 1
    else:
        v_semantic = 0
    (check_result, result_list) = check_name(name, up_time, v_name, v_num, r_type, host, user, password, db_name)
    if check_result == 0:
        # check_result == 0 , 未插入
        insert_sql = "INSERT INTO github_go_repos (full_name,stars,forks,r_size,created_time,updated_time,v_name," \
                     "semantic,go_mod,version_dir,version_number,path_match,r_type) VALUES ('%s','%d','%d','%d','%s'," \
                     "'%s','%s','%d','%d','%d','%d','%d','%d')" % (name, stars, forks, size, c_time, up_time, v_name,
                                                                   v_semantic, go_mod, v_dir, v_num, path_match, r_type)
        db = pymysql.connect(host, user, password, db_name)
        try:
            insert_cursor = db.cursor()
            # 执行sql语句
            insert_cursor.execute(insert_sql)
            db.commit()
            insert_cursor.close()
            print('insert successful', name)
            insert_s = insert_s + 1
        except Exception as exp:
            print('insert error exception is:', exp)
            print('insert error sql:', insert_sql)
            insert_e = insert_e + 1
            # 发生错误时回滚
            db.rollback()
        db.close()
    elif check_result == 1:
        # 已经有了该信息
        print('already insert')
    elif check_result > 1:
        # 有该存储库但信息不同
        if check_result == 3:
            # result_list
            time_num = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
            time_num = int(time_num)
            change_list = [time_num, name, result_list[0], result_list[1], up_time, v_name, result_list[3], r_type]
            (insert_e, insert_s) = insert_repo_change(change_list, insert_e, insert_s, host, user, password, db_name)

        update_sql = "UPDATE github_go_repos SET stars='%d',forks='%d',r_size='%d',created_time='%s'," \
                     "updated_time='%s',v_name='%s',semantic='%d',go_mod='%d',version_dir='%d',version_number='%d'," \
                     "path_match='%d',r_type='%d' WHERE full_name='%s'" % (stars, forks, size, c_time, up_time, v_name,
                                                                           v_semantic, go_mod, v_dir, v_num, path_match,
                                                                           r_type, name)
        db = pymysql.connect(host, user, password, db_name)
        try:
            update_cursor = db.cursor()
            # 执行sql语句
            update_cursor.execute(update_sql)
            db.commit()
            update_cursor.close()
            print('update successful', name)
            update_s = update_s + 1
        except Exception as exp:
            print('update error exception is:', exp)
            print('update error sql:', update_sql)
            update_e = update_e + 1
            # 发生错误时回滚
            db.rollback()
        db.close()
    else:
        print('check error', name)
        check_e = check_e + 1
    return insert_e, check_e, update_e, insert_s, update_s


# 查重
def check_name(r_name, up_time, v_name, v_number, r_type, host, user, password, db_name):
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT updated_time,v_name,version_number,r_type FROM github_go_repos WHERE full_name = '%s'" % r_name
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            check_up_time = check_result[0][0]
            check_v_name = check_result[0][1]
            check_v_number = check_result[0][2]
            check_r_type = check_result[0][3]
        else:
            check_up_time = ''
            check_v_name = ''
            check_v_number = ''
            check_r_type = ''

        if check_up_time:
            if check_up_time != up_time or check_v_name != v_name or check_v_number != v_number \
                    or check_r_type != r_type:
                if check_up_time != up_time and check_r_type != r_type:
                    check_num = 3, check_result[0]
                else:
                    check_num = 2, []
            else:
                check_num = 1, []
        else:
            check_num = 0, []
        print("check result:", check_num, check_up_time, check_v_name, check_v_number, check_r_type)
        return check_num
    except Exception as exp:
        print("check repos name error:", exp)
        return -1, []


# 插入repo_change数据库
def insert_repo_change(change, insert_e, insert_s, host, user, password, db_name):
    # change_list
    c_type = str(change[6]) + '-' + str(change[7])
    insert_sql = "INSERT INTO repo_change (id,full_name,b_update,b_v_name,n_update,n_v_name,b_type," \
                 "n_type,change_type) VALUES ('%d','%s','%s','%s','%s','%s','%d','%d'," \
                 "'%s')" % (change[0], change[1], change[2], change[3], change[4], change[5],
                            change[6], change[7], c_type)
    db = pymysql.connect(host, user, password, db_name)
    try:
        insert_cursor = db.cursor()
        # 执行sql语句
        insert_cursor.execute(insert_sql)
        db.commit()
        insert_cursor.close()
        print('insert repo_change successful', change[1])
        insert_s = insert_s + 1
    except Exception as exp:
        print('insert repo_change error exception is:', exp)
        print('insert repo_change error sql:', insert_sql)
        insert_e = insert_e + 1
        # 发生错误时回滚
        db.rollback()
    db.close()
    return insert_e, insert_s


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
    (search_e, insert_e, check_e, update_e, insert_s, update_s,
     issue_l) = get_mainpage(part, host, user, password, db_name, search_e, insert_e, check_e, update_e, insert_s,
                             update_s, time_w, issue_l)
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
