# 通过GitHub的api获取某一repo的上游  【注意k8s.com其他存储库】
import base64
import json
import re
import time
from concurrent.futures.thread import ThreadPoolExecutor
from urllib.request import Request, urlopen
import pymysql
# from findbug_oneoldcheck_api import get_import
# from findbug_oneoldcheck_api import get_import\


# 获取改名过的repo的list
def get_name_change_list(host, user, password, db_name):
    n_name_list = []
    sql = "SELECT old_repo_name FROM repo_name_update WHERE now_repo_name!='0'"
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            for n_name in check_result:
                n_name_list.append(n_name[0])
            return n_name_list
        else:
            return []
    except Exception as exp:
        print("get repo_name_update update-list error:", exp, '************************************************************')
        return []


# 获取删除的repo的list
def get_name_delete_list(host, user, password, db_name):
    n_name_list = []
    sql = "SELECT old_repo_name FROM repo_name_update WHERE now_repo_name='0'"
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            for n_name in check_result:
                n_name_list.append(n_name[0])
            return n_name_list
        else:
            return []
    except Exception as exp:
        print("get repo_name_update delete-list error:", exp, '************************************************************')
        return []


# 检测repo是否改名  repo_name_update
def check_name_change(repo_name, host, user, password, db_name):
    sql = "SELECT now_repo_name FROM repo_name_update WHERE old_repo_name='%s'" % repo_name
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            print('数据库表repo_name_update有：', repo_name)
            print('改名为：', check_result[0][0])
            return check_result[0][0]
        else:
            return ''
    except Exception as exp:
        print("check repo_name_update error:", exp, '******************************************************************')
        return ''


# 【此处解析go源文件file_url中的代码】
# 获取包中的go源文件 【待删】
# def get_pkg_file(url, file_list, headers):
#     pkg_list = []
#     try:
#         page_detail = get_results(url, headers)
#     except Exception as exp:
#         print("When find detail page: get search error 2", exp)
#         page_detail = []
#     for f in page_detail:
#         # 判断是否为.go源文件文件
#         if re.findall(r".go$", f['name']) and f['type'] == 'file' and (f['url'] not in file_list):
#             # 源文件
#             print('get pkg file: ', f['name'])
#             pkg_list.append(f['url'])
#     return pkg_list


# 获取包中每个go源文件中的import语句 【待删】
# def get_pkg_import(file_url, import_list, vendor_list, headers):
#     pkg_import_list = []
#     file_result = get_results(file_url, headers)  # 获取文件内容
#     # 解码后，使用正则表达式，获取module声明的模块路径
#     file_content = base64.b64decode(file_result['content'])
#     file_import = re.findall(r"import\s\(\n(.+?)\n\)", file_content.decode(), re.S)
#     if file_import:
#         imports = file_import[0]  # 所有依赖项
#         imports_list = imports.split('\n')
#         for imp in imports_list:
#             print('第二层，', imp)
#             if re.findall(r"\"(.+?)\"", imp):
#                 import_path = re.findall(r"\"(.+?)\"", imp)[0].replace(' ', '') + ' '
#                 if (import_path not in import_list) and re.findall(r"github\.com/(.+?)\s", import_path):
#                     imp_mod = re.findall(r"(github\.com/[^/]+?/[^/]+?)/.+?", import_path)
#                     imp_repo = re.findall(r"(github\.com/[^/]+?)/.+?", import_path)
#                     if imp_mod:
#                         imp_mod_name = imp_mod[0].replace(' ', '')
#                     else:
#                         imp_mod_name = import_path.replace(' ', '')
#                     if imp_repo:
#                         imp_repo_name = imp_repo[0].replace(' ', '')
#                     else:
#                         imp_repo_name = import_path.replace(' ', '')
#                     if (imp_mod_name not in vendor_list) and (imp_repo_name not in vendor_list) and \
#                             (import_path not in vendor_list) and (imp_mod_name not in import_list):
#                         print('get pkg import: ', import_path)
#                         pkg_import_list.append(import_path.replace(' ', ''))
#     return pkg_import_list


# 获取文件夹中的go源文件
# def get_file(url, file_list, headers):
#     try:
#         page_detail = get_results(url, headers)
#         # print(page_detail)
#     except Exception as exp:
#         print("When find detail page: get search error 2", exp)
#         page_detail = []
#     for f in page_detail:
#         # 判断是否为.go源文件文件
#         if f['type'] == 'file' and re.findall(r".go$", f['name']):
#             if f['url'] not in file_list:
#                 print('get file 直接依赖 file: ', f['name'])
#                 file_list.append(f['url'])
#         elif f['type'] == 'dir' and f['name'] != 'vendor':
#             print('get file 直接依赖 dir: ', f['name'])
#             file_list = get_file(f['url'], file_list, headers)
#             if len(page_detail) > 20:
#                 time.sleep(0.8)
#     return file_list


# 获取每个go源文件中的import语句  【k8s.com其他存储库】
def get_import(file_url, import_list, vendor_list, headers, record_c):
    # imp_mod_list = []  【尝试在根源处理导入路径】
    file_imp_list = []  # 作用：
    file_result = get_results(file_url, headers)  # 获取文件内容
    # https://api.github.com/repos/go-chi/chi/contents/chi.go?ref=v4.1.2
    # https://api.github.com/repos/inconshreveable/ngrok/git/blobs/28459adb62922b713ef2b9dcc20727ee5f5f4cc4
    print(file_url, ' # ', file_result['url'])
    repo_name = ''
    if re.findall(r"https://api\.github\.com/(.+?)/repos/contents", file_result['url']):
        repo_name = re.findall(r"https://api\.github\.com/repos/(.+?)/contents", file_result['url'])[0]
    elif re.findall(r"https://api\.github\.com/repos/(.+?)/git", file_result['url']):
        repo_name = re.findall(r"https://api\.github\.com/repos/(.+?)/git", file_result['url'])[0]

    # 解码后，使用正则表达式，获取module声明的模块路径
    file_contents = base64.b64decode(file_result['content'])
    import_part = file_contents.decode()
    file_content = import_part.replace('"', '')
    # 匹配得到所有import语句
    file_imports = re.findall(r"import\s*\(\n*(.+?)\n*\)", file_content, re.S)
    if file_imports:
        import_l_t = re.findall(r"\s*github\.com/(.+?)$", file_imports[0], re.M)
        import_l = []
        for i in import_l_t:
            j = i.replace(repo_name, '')
            if j == i:
                if re.findall(r"//", i):
                    i = i.split('//')[0].replace(' ', '')
                    import_l.append(i)
                else:
                    i = i.replace(' ', '')
                    import_l.append(i)

        for import_r in import_l:
            import_rp = import_r.strip()  # 无github.com/
            # import_rm = import_rp
            # if re.findall(r"^([^/]+?/[^/]+?)/.+?$", import_rp):
            #     import_rm = re.findall(r"^([^/]+?/[^/]+?)/", import_rp)[0]
            # if import_rm and (import_rm not in imp_mod_list):
            #     imp_mod_list.append(import_rm)

            #  and (import_rm not in vendor_list)  不排除vendor里的
            if import_rp and (import_rp not in import_list) :
                print('[git]上游-m1：', import_rp)
                # 先不检查子模块 【暂时】
                import_list.append(import_rp)
                # if record_c == 1:
                #     file_imp_list.append(import_rp)
                # print('1.依赖项_1:', require_r)

        import_l_t = re.findall(r"\s*k8s\.com/(.+?)$", file_imports[0], re.M)
        import_l = []
        for i in import_l_t:
            j = i.replace(repo_name, '')
            if j == i:
                if re.findall(r"//", i):
                    i = i.split('//')[0].replace(' ', '')
                    import_l.append(i)
                else:
                    i = i.replace(' ', '')
                    import_l.append(i)

        for import_r in import_l:
            import_rp = 'kubernetes/' + import_r.strip()
            # import_rm = import_rp
            # if re.findall(r"^([^/]+?/[^/]+?)/.+?$", import_rp):
            #     import_rm = re.findall(r"^([^/]+?/[^/]+?)/", import_rp)[0]
            # if import_rm and (import_rm not in imp_mod_list):
            #     imp_mod_list.append(import_rm)
            #  and (import_rm not in vendor_list)  不排除vendor里的
            if import_rp and (import_rp not in import_list):
                print('[k8s]上游-m1：', import_rp)
                # 先不检查子模块 【暂时】
                import_list.append(import_rp)
                # if record_c == 1:
                #     file_imp_list.append(import_rp)
            # if import_r and (import_r not in import_list):
            #     name_list = import_r.split('/')
            #     name_path = ''
            #     match = 0
            #     for name in name_list:
            #         name_path = name_path + '/' + name
            #         path = 'k8s.com' + name_path
            #         path_git = 'kubernetes' + name_path
            #         if (path in vendor_list) or (path_git in import_list):
            #             match = match + 1
            #     if match == 0:
            #         import_r_git = 'kubernetes/' + import_r
            #         print('找上游-m1：', import_r_git)
            #         import_list.append(import_r_git)
            #         if record_c == 1:
            #             file_imp_list.append(import_r_git)
                # print('1.依赖项_1:', require_r)

    file_imports = re.findall(r"^import\s+github\.com/(.+?)$", file_content, re.M)
    for import_r in file_imports:
        import_rp = import_r.strip()
        j = import_rp.replace(repo_name, '')
        if j == import_rp:
            # import_rm = import_rp
            # if re.findall(r"^([^/]+?/[^/]+?)/.+?$", import_rp):
            #     import_rm = re.findall(r"^([^/]+?/[^/]+?)/", import_rp)[0]
            # if import_rm and (import_rm not in imp_mod_list):
            #     imp_mod_list.append(import_rm)
            if import_rp and (import_rp not in import_list):
                print('[git]上游-m1：', import_rp)
                # 先不检查子模块 【暂时】
                import_list.append(import_rp)
                # if record_c == 1:
                #     file_imp_list.append(import_rp)
                # print('1.依赖项_1:', require_r)
                # print('1.依赖项_2:', require_r)

    file_imports = re.findall(r"^import\s+k8s\.com/(.+?)$", file_content, re.M)
    for import_r in file_imports:
        import_rp = 'kubernetes/' + import_r.strip()
        import_rp = import_r.strip()
        j = import_rp.replace(repo_name, '')
        if j == import_rp:
            # import_rm = import_rp
            # if re.findall(r"^([^/]+?/[^/]+?)/.+?$", import_rp):
            #     import_rm = re.findall(r"^([^/]+?/[^/]+?)/", import_rp)[0]
            # if import_rm and (import_rm not in imp_mod_list):
            #     imp_mod_list.append(import_rm)
            if import_rp and (import_r not in import_list):
                print('[k8s]上游-m2：', import_rp)
                # 先不检查子模块 【暂时】
                import_list.append(import_rp)
                # print('1.依赖项_2:', require_r)

    # print(import_list)
    if record_c == 1:
        return import_list, file_imp_list
    else:
        return import_list
# def get_import(file_url, import_list, vendor_list, headers, record_c):
#     file_imp_list = []
#     file_result = get_results(file_url, headers)  # 获取文件内容
#     # print(file_result)
#     # 解码后，使用正则表达式，获取module声明的模块路径
#     file_contents = base64.b64decode(file_result['content'])
#     import_part = file_contents.decode()
#     file_content = import_part.replace('"', '')
#     # 匹配得到所有import语句
#     file_imports = re.findall(r"import\s*\(\n*(.+?)\n*\)", file_content, re.S)
#     if file_imports:
#         import_l_t = re.findall(r"^[^/]*github\.com/(.+?)$", file_imports[0], re.M)
#         import_l = []
#         for i in import_l_t:
#             if re.findall(r"//", i):
#                 i = i.split('//')[0].replace(' ', '')
#                 import_l.append(i)
#             else:
#                 i = i.replace(' ', '')
#                 import_l.append(i)
#         for import_r in import_l:
#             import_r = import_r.strip()  # 无github.com/
#             if import_r and (import_r not in import_list):
#                 name_list = import_r.split('/')
#                 name_path = ''
#                 match = 0
#                 for name in name_list:
#                     name_path = name_path + '/' + name
#                     path = 'github.com' + name_path
#                     i_path = path.replace('github.com/', '')
#                     if (path in vendor_list) or (i_path in import_list):
#                         match = match + 1
#                 if match == 0:
#                     print('找上游-m1：', import_r)
#                     import_list.append(import_r)
#                     if record_c == 1:
#                         file_imp_list.append(import_r)
#                 # print('1.依赖项_1:', require_r)
#
#         import_l_t = re.findall(r"^[^/]*k8s\.com/(.+?)$", file_imports[0], re.M)
#         import_l = []
#         for i in import_l_t:
#             if re.findall(r"//", i):
#                 i = i.split('//')[0].replace(' ', '')
#                 import_l.append(i)
#             else:
#                 i = i.replace(' ', '')
#                 import_l.append(i)
#         for import_r in import_l:
#             import_r = import_r.strip()
#             if import_r and (import_r not in import_list):
#                 name_list = import_r.split('/')
#                 name_path = ''
#                 match = 0
#                 for name in name_list:
#                     name_path = name_path + '/' + name
#                     path = 'k8s.com' + name_path
#                     path_git = 'kubernetes' + name_path
#                     if (path in vendor_list) or (path_git in import_list):
#                         match = match + 1
#                 if match == 0:
#                     import_r_git = 'kubernetes/' + import_r
#                     print('找上游-m1：', import_r_git)
#                     import_list.append(import_r_git)
#                     if record_c == 1:
#                         file_imp_list.append(import_r_git)
#                 # print('1.依赖项_1:', require_r)
#
#     file_imports = re.findall(r"^import\s+github\.com/(.+?)$", file_content, re.M)
#     for import_r in file_imports:
#         import_r = import_r.strip()
#         if import_r and (import_r not in import_list):
#             name_list = import_r.split('/')
#             name_path = ''
#             match = 0
#             for name in name_list:
#                 name_path = name_path + '/' + name
#                 path = 'github.com' + name_path
#                 if (path in vendor_list) or (path in import_list):
#                     match = match + 1
#             if match == 0:
#                 print('找上游-m2：', import_r)
#                 import_list.append(import_r)
#                 if record_c == 1:
#                     file_imp_list.append(import_r)
#             # print('1.依赖项_2:', require_r)
#
#     file_imports = re.findall(r"^import\s+k8s\.com/(.+?)$", file_content, re.M)
#     for import_r in file_imports:
#         import_r = import_r.strip()
#         if import_r and (import_r not in import_list):
#             name_list = import_r.split('/')
#             name_path = ''
#             match = 0
#             for name in name_list:
#                 name_path = name_path + '/' + name
#                 path = 'k8s.com' + name_path
#                 path_git = 'kubernetes' + name_path
#                 if (path in vendor_list) or (path_git in import_list):
#                     match = match + 1
#             if match == 0:
#                 import_r_git = 'kubernetes/' + import_r
#                 print('找上游-m2：', import_r_git)
#                 import_list.append(import_r_git)
#                 if record_c == 1:
#                     file_imp_list.append(import_r_git)
#             # print('1.依赖项_2:', require_r)
#     # print(import_list)
#     if record_c == 1:
#         return import_list, file_imp_list
#     else:
#         return import_list


def get_results(url, headers):
    request = Request(url, headers=headers)
    response = urlopen(request).read()
    result = json.loads(response.decode())
    return result


# 需要改成 get_file_detail 解析文件中的import语句，获取import列表
def get_file_detail(import_list, vendor_list, repo_name, file_path, i_file_url, headers, issue):
    file_imp_list = []
    try:
        (import_list, file_imp_list) = get_import(i_file_url, import_list, vendor_list, headers, 1)
        # 检查import语句中是否有该repo
        # file_import = re.findall(r"import\s\(\n(.+?)\n\)", go_mod_content.decode(), re.S)
        # if file_import:
        #     imports = file_import[0]  # 所有依赖项
        #     imports_l = imports.split('\n')
        #     for imp in imports_l:
        #         # print('1.粗分: ', imp)
        #         if re.findall(r"\"(.+?)\"", imp):
        #             imp = re.findall(r"\"(.+?)\"", imp)[0].replace(' ', '') + ' '
        #             # print('2.去引号: ', imp)
        #             if re.findall(r"github\.com/(.+?)\s", imp):
        #
        #                 imp_path = re.findall(r"github\.com/(.+?)\s", imp)[0]  # 无github.com
        #                 name_list = imp_path.split('/')
        #                 name_path = ''
        #                 match = 0
        #                 for name in name_list:
        #                     name_path = name_path + '/' + name
        #                     path = 'github.com' + name_path
        #                     if (path in vendor_list) or (path in import_list):
        #                         match = match + 1
        #                 if match == 0:
        #                     file_imp_list.append(imp_path)
        #                     import_list.append(imp_path)
        #                     print('找上游-读取文件：', imp, '--', imp_path)
        #         else:
        #             # print('没有引号引起来的依赖项')
        #             # print('没有引号？', imp)
        #             imp = imp + ' '
        #             if re.findall(r"github\.com/(.+?)\s", imp):
        #                 imp_path = re.findall(r"github\.com/(.+?)\s", imp)[0]  # 无github.com
        #                 if imp_path not in import_list:
        #                     import_list.append(imp_path)
        # file_import = re.findall(r"import\s\"github\.com/(.+?)\"", go_mod_content.decode(), re.S)
        # for imp_r in file_import:
        #     if imp_r:
        #         imp = imp_r[0]
        #         name_list = imp.split('/')
        #         name_path = ''
        #         match = 0
        #         for name in name_list:
        #             name_path = name_path + '/' + name
        #             path = 'github.com' + name_path
        #             if (path in vendor_list) or (path in import_list):
        #                 match = match + 1
        #         if match == 0:
        #             file_imp_list.append(imp)
        #             import_list.append(imp)
        #             print('找上游-读取文件：', 'import引号 --', imp)
    except Exception as exp:
        print("When find detail page: get search error", exp, '******************************************************'
                                                              '*****************************************************')
        issue = issue + '<' + 'get_file_detail:' + repo_name + '-' + file_path + '>'
    return file_imp_list, import_list, issue


# imp_mod, headers, search_e, time_w
def get_sub_mod_list(up_repo_name, headers, search_e, time_w):
    # 查看依赖的该项，检查是否有子模块
    imp_sub_mod_list = []
    for page_num in range(1, 11):
        # https://api.github.com/search/code?q=repo:%s+extension:mod&page=1&per_page=100
        url = 'https://api.github.com/search/code?q=module+repo:%s' \
              '+extension:mod&page=%s&per_page=100' % (up_repo_name, page_num)
        print('***get_sub_mod_list', url)
        try:
            time.sleep(time_w)
            results = get_results(url, headers)
            items = results['items']
            if items:
                # c = 0  # 计数器
                for i in items:
                    # i_filename = i['name']  # 存：文件名字
                    i_path = i['path']  # 存：文件相对路径
                    if not re.findall(r"vendor/.+?", i_path):
                        if i_path != 'go.mod':
                            sub_mod = up_repo_name + '/' + i_path.replace('/go.mod', '')
                            if sub_mod not in imp_sub_mod_list:
                                imp_sub_mod_list.append(sub_mod)
                                print(up_repo_name, '的子模块：', sub_mod)
                        # else:
                        #     sub_mod = up_repo_name
            else:
                break
            time.sleep(time_w)
        except Exception as exp:
            print("get search 子模块路径 error", exp, '************************************************')
            search_e = search_e + 1
    print('筛选得到的子模块列表为：', imp_sub_mod_list)
    return imp_sub_mod_list, search_e


# 输入repo名，以获得下游信息, 【1】
def get_up_repo(import_list, dir_name_list, vendor_list, repo_name, host, user, password, db_name, time_w, insert_e,
                search_e, check_e, update_e, insert_s, update_s, issue):
    vendor_dir_list = []
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    # 查询数据库是否有
    check_result = 0
    imp_mod_list = []
    imp_final_list = []
    imp_final_siv_list = []
    imp_siv_ok_list = []
    sub_mod_list = []
    size_check = 0
    url = 'https://api.github.com/search/code?q=github.com+repo:' + repo_name
    url = url + '+extension:go&page=1&per_page=100'
    try:
        results = get_results(url, headers)
        file_count = results['total_count']
        print('文件总数', file_count)
        if file_count > 1000:
            size_check = 1
        else:
            for page_num in range(1, 11):
                url = 'https://api.github.com/search/code?q=github.com+repo:' + repo_name
                url = url + '+extension:go&page=%d&per_page=100' % page_num
                print(url)
                print('page-num: ', page_num)  # size_list[l_num]
                try:
                    time.sleep(time_w)
                    results = get_results(url, headers)
                    items = results['items']
                    if page_num == 10 and len(items) >= 100:
                        print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@-------------超过了1000个本页---------------@@@@@@@',
                              '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@-------------超过了1000个本页---------------@@@@@@@@',
                              '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@-------------超过了1000个本页---------------@@@@@@@@',
                              '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
                    if items:
                        c = 0  # 计数器
                        for i in items:
                            # i_filename = i['name']  # 存：文件名字
                            i_path = i['path']
                            i_repo = i['repository']
                            i_reponame = i_repo['full_name']
                            i_fileurl = i['git_url']
                            c = c + 1
                            # print('-----------------------------------------------------------------------------')
                            print('【file:', c, '】: ', i_reponame, i_path)
                            if re.findall(r"^(.*/vendor)/", i_path):
                                # 有vendor目录
                                vendor_path = re.findall(r"^(.*/vendor)/", i_path)[0]
                                fr_path = i_path.replace(vendor_path, '')
                                if vendor_path not in vendor_dir_list:
                                    vendor_dir_list.append(vendor_path)
                                    vendor_url = i_fileurl.replace(fr_path, '')
                                    try:
                                        vendor_detail = get_results(vendor_url, headers)
                                        # print(page_detail)
                                    except Exception as exp:
                                        print("**%1% When find vendor page: get search error ", exp,
                                              '***************************************************')
                                        vendor_detail = []
                                    for v in vendor_detail:
                                        # 其他存储库 ， 在这里扩展
                                        # 解析vendor目录  【github.com】
                                        if re.findall(r"github\.com", v['name']) and v['type'] == 'dir':
                                            if re.findall(r"(github\.com/[^/]+?/.+?)$", v['name']):
                                                vendor_repo = re.findall(r"github\.com/([^/]+?/[^/]+?)",
                                                                         v['name'])[0]
                                                if vendor_repo not in vendor_list:
                                                    vendor_list.append(vendor_repo)
                                            else:
                                                try:
                                                    vendor_page_detail = get_results(v['url'], headers)
                                                    # print(page_detail)
                                                    for vd in vendor_page_detail:
                                                        if vd['type'] == 'dir':
                                                            dir_name = v['name'] + '/' + vd['name']
                                                            # print('vendor列表：', pkg_name)
                                                            if re.findall(r"(github\.com/[^/]+?/.+?)", dir_name):
                                                                vendor_repo = \
                                                                    re.findall(r"github\.com/([^/]+?/[^/]+?)",
                                                                               dir_name)[0]
                                                                if vendor_repo not in vendor_list:
                                                                    vendor_list.append(vendor_repo)
                                                            else:
                                                                try:
                                                                    vendor_page_detail = get_results(vd['url'],
                                                                                                     headers)
                                                                    # print(page_detail)
                                                                    for vdp in vendor_page_detail:
                                                                        if vdp['type'] == 'dir':
                                                                            pkg_name = v['name'] + '/' \
                                                                                       + vd['name'] + '/' \
                                                                                       + vdp['name']
                                                                            # print('vendor列表：', pkg_name)
                                                                            if re.findall(
                                                                                    r"(github\.com/[^/]+?/.+?)",
                                                                                    pkg_name):
                                                                                vendor_repo = re.findall(
                                                                                    r"github\.com/([^/]+?/[^/]+?)",
                                                                                    pkg_name)[0]
                                                                                if vendor_repo not in vendor_list:
                                                                                    vendor_list.append(vendor_repo)
                                                                except Exception as exp:
                                                                    print("**%3% When find vendor detail page: "
                                                                          "get search error 3[git]", exp)
                                                                    # vendor_page_detail = []
                                                except Exception as exp:
                                                    print("**%2% When find vendor detail page: get search "
                                                          "error 3[git]", exp)
                                                    # vendor_page_detail = []

                                        # 解析vendor目录  【k8s.com】
                                        if re.findall(r"k8s\.com", v['name']) and v['type'] == 'dir':
                                            if re.findall(r"(k8s\.com/.+?)$", v['name']):
                                                vendor_repo = re.findall(r"k8s\.com/([^/]+?)", v['name'])[0]
                                                vendor_repo = 'kubernetes/' + vendor_repo
                                                if vendor_repo not in vendor_list:
                                                    vendor_list.append(vendor_repo)
                                            else:
                                                try:
                                                    vendor_page_detail = get_results(v['url'], headers)
                                                    # print(page_detail)
                                                    for vd in vendor_page_detail:
                                                        if vd['type'] == 'dir':
                                                            dir_name = v['name'] + '/' + vd['name']
                                                            # print('vendor列表：', pkg_name)
                                                            if re.findall(r"(k8s\.com/[^/]+?)", dir_name):
                                                                vendor_repo = \
                                                                    re.findall(r"k8s\.com/([^/]+?)", v['name'])[0]
                                                                vendor_repo = 'kubernetes/' + vendor_repo
                                                                if vendor_repo not in vendor_list:
                                                                    vendor_list.append(vendor_repo)
                                                except Exception as exp:
                                                    print("**%2% When find vendor detail page: get search "
                                                          "error 3[k8s]", exp)
                                    # if 'github.com' in vendor_list:
                                    #     vendor_list.remove('github.com')
                                    # if 'github.com/' in vendor_list:
                                    #     vendor_list.remove('github.com/')
                                    # if 'k8s.com' in vendor_list:
                                    #     vendor_list.remove('k8s.com')
                                    # if 'k8s.com/' in vendor_list:
                                    #     vendor_list.remove('k8s.com/')
                                    print('vendor目录', vendor_list)  # 带有github.com

                            else:
                                (file_imp_list, import_list,
                                 issue) = get_file_detail(import_list, vendor_list, i_reponame, i_path, i_fileurl,
                                                          headers, issue)
                                time.sleep(time_w + 0.5)
                            # print('-----------------------------------------------------------------------------')

                            # for imp in file_imp_list:
                            # if up_repo_name != repo_name:  # (up_repo_name not in imp_mod_list) and
                            #     imp_mod_list.append(up_repo_name)
                            #     i_count = i_count + 1
                            #     print('【import:', i_count, '】: ', up_repo_name)
                            #     time.sleep(0.8)
                            #     (check_e, insert_e, update_e, insert_s,
                            #      update_s) = insert_repo_depend(check_time, up_repo_name, repo_name, i_path,
                            #                                     i_fileurl, host, user, password, db_name, check_e,
                            #                                     insert_e, update_e, insert_s, update_s)
                    else:
                        break
                except Exception as exp:
                    print("get search code main page error", exp,
                          '***********************************************')
                    search_e = search_e + 1
                print(
                    '-------------------------------------------------------------------------------------------')

    except Exception as exp:
        print("get search code main page error", exp, '***********************************************')
        search_e = search_e + 1
        size_check = 2

    if size_check > 0:
        # i_count = 0
        # check_time = int(time.strftime('%Y%m%d', time.localtime(time.time())))
        # (check_result, down_list) = check_down_repo(repo_name, check_date, host, user, password, db_name)
        size_list = ['0..800', '801..1200', '1201..4600', '4601..18000', '18001..38000', '38001..68000',
                     '68001..108000', '108001..180000', '180001..350000', '350001..385000']
        dir_path_list = []
        d_c = 0
        dir_name_list_copy = dir_name_list
        dir_path = ''
        # for d in dir_name_list:
        #     d_c = d_c + 1
        #     if d_c < 6 and len(dir_name_list_copy) >= 4:
        #         dir_path = dir_path + '+path:/' + d
        #         if len(dir_path) <= 75:
        #             dir_name_list_copy.remove(d)
        #         else:
        #             break
        #     elif d_c < 6 and len(dir_name_list_copy) < 4:
        #         for d_rest in dir_name_list_copy:
        #             dir_path = dir_path + '+path:/' + d_rest
        #         break
        #     else:
        #         dir_path_list.append(dir_path)
        #         dir_path = '+path:/' + d
        #         dir_name_list_copy.remove(d)
        #         d_c = 1
        for d in dir_name_list:
            dir_path_1 = dir_path + '+path:/' + d
            if len(dir_path_1) <= 70:
                dir_path = dir_path + '+path:/' + d

            else:
                dir_path_list.append(dir_path)
                dir_path = '+path:/' + d
        dir_path_list.append(dir_path)

        if check_result == 0 or check_result == 1:
            for dir_path in dir_path_list:
                # for l_num in range(2, 3)
                for size in size_list:
                    # 41,101
                    for page_num in range(1, 11):
                        url = 'https://api.github.com/search/code?q=github.com+repo:' + repo_name
                        url = url + dir_path + '+size:%s+extension:go&page=%s&per_page=100' % (size, page_num)
                        print(url)
                        print('size: ', size, page_num)  # size_list[l_num]
                        try:
                            time.sleep(time_w)
                            results = get_results(url, headers)
                            items = results['items']
                            if page_num == 10 and len(items) >= 100:
                                print(
                                    '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@-------------超过了1000个本页---------------@@@@@@@'
                                    '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@-------------超过了1000个本页---------------@@@@@@@@'
                                    '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@-------------超过了1000个本页---------------@@@@@@@@'
                                    '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
                            if items:
                                c = 0  # 计数器
                                for i in items:
                                    # i_filename = i['name']  # 存：文件名字
                                    i_path = i['path']
                                    i_repo = i['repository']
                                    i_reponame = i_repo['full_name']
                                    i_fileurl = i['git_url']
                                    c = c + 1
                                    # print('-----------------------------------------------------------------------------')
                                    print('【file:', c, '】: ', i_reponame, i_path)
                                    if re.findall(r"^(.*/vendor)/", i_path):
                                        # 有vendor目录
                                        vendor_path = re.findall(r"^(.*/vendor)/", i_path)[0]
                                        fr_path = i_path.replace(vendor_path, '')
                                        if vendor_path not in vendor_dir_list:
                                            vendor_dir_list.append(vendor_path)
                                            vendor_url = i_fileurl.replace(fr_path, '')
                                            try:
                                                vendor_detail = get_results(vendor_url, headers)
                                                # print(page_detail)
                                            except Exception as exp:
                                                print("**%1% When find vendor page: get search error ", exp,
                                                      '***************************************************')
                                                vendor_detail = []
                                            for v in vendor_detail:
                                                # 其他存储库 ， 在这里扩展
                                                # 解析vendor目录  【github.com】
                                                if re.findall(r"github\.com", v['name']) and v['type'] == 'dir':
                                                    if re.findall(r"(github\.com/[^/]+?/.+?)$", v['name']):
                                                        vendor_repo = re.findall(r"github\.com/([^/]+?/[^/]+?)",
                                                                                 v['name'])[0]
                                                        if vendor_repo not in vendor_list:
                                                            vendor_list.append(vendor_repo)
                                                    else:
                                                        try:
                                                            vendor_page_detail = get_results(v['url'], headers)
                                                            # print(page_detail)
                                                            for vd in vendor_page_detail:
                                                                if vd['type'] == 'dir':
                                                                    dir_name = v['name'] + '/' + vd['name']
                                                                    # print('vendor列表：', pkg_name)
                                                                    if re.findall(r"(github\.com/[^/]+?/.+?)",
                                                                                  dir_name):
                                                                        vendor_repo = \
                                                                            re.findall(r"github\.com/([^/]+?/[^/]+?)",
                                                                                       dir_name)[0]
                                                                        if vendor_repo not in vendor_list:
                                                                            vendor_list.append(vendor_repo)
                                                                    else:
                                                                        try:
                                                                            vendor_page_detail = get_results(vd['url'],
                                                                                                             headers)
                                                                            # print(page_detail)
                                                                            for vdp in vendor_page_detail:
                                                                                if vdp['type'] == 'dir':
                                                                                    pkg_name = v['name'] + '/' \
                                                                                               + vd['name'] + '/' \
                                                                                               + vdp['name']
                                                                                    # print('vendor列表：', pkg_name)
                                                                                    if re.findall(
                                                                                            r"(github\.com/[^/]+?/.+?)",
                                                                                            pkg_name):
                                                                                        vendor_repo = re.findall(
                                                                                            r"github\.com/([^/]+?/[^/]+?)",
                                                                                            pkg_name)[0]
                                                                                        if vendor_repo not in vendor_list:
                                                                                            vendor_list.append(
                                                                                                vendor_repo)
                                                                        except Exception as exp:
                                                                            print("**%3% When find vendor detail page: "
                                                                                  "get search error 3[git]", exp)
                                                                            # vendor_page_detail = []
                                                        except Exception as exp:
                                                            print("**%2% When find vendor detail page: get search "
                                                                  "error 3[git]", exp)
                                                            # vendor_page_detail = []

                                                # 解析vendor目录  【k8s.com】
                                                if re.findall(r"k8s\.com", v['name']) and v['type'] == 'dir':
                                                    if re.findall(r"(k8s\.com/.+?)$", v['name']):
                                                        vendor_repo = re.findall(r"k8s\.com/([^/]+?)", v['name'])[0]
                                                        vendor_repo = 'kubernetes/' + vendor_repo
                                                        if vendor_repo not in vendor_list:
                                                            vendor_list.append(vendor_repo)
                                                    else:
                                                        try:
                                                            vendor_page_detail = get_results(v['url'], headers)
                                                            # print(page_detail)
                                                            for vd in vendor_page_detail:
                                                                if vd['type'] == 'dir':
                                                                    dir_name = v['name'] + '/' + vd['name']
                                                                    # print('vendor列表：', pkg_name)
                                                                    if re.findall(r"(k8s\.com/[^/]+?)", dir_name):
                                                                        vendor_repo = \
                                                                            re.findall(r"k8s\.com/([^/]+?)", v['name'])[
                                                                                0]
                                                                        vendor_repo = 'kubernetes/' + vendor_repo
                                                                        if vendor_repo not in vendor_list:
                                                                            vendor_list.append(vendor_repo)
                                                        except Exception as exp:
                                                            print("**%2% When find vendor detail page: get search "
                                                                  "error 3[k8s]", exp)
                                            # if 'github.com' in vendor_list:
                                            #     vendor_list.remove('github.com')
                                            # if 'github.com/' in vendor_list:
                                            #     vendor_list.remove('github.com/')
                                            # if 'k8s.com' in vendor_list:
                                            #     vendor_list.remove('k8s.com')
                                            # if 'k8s.com/' in vendor_list:
                                            #     vendor_list.remove('k8s.com/')
                                            print('vendor目录', vendor_list)  # 带有github.com

                                    else:
                                        (file_imp_list, import_list,
                                         issue) = get_file_detail(import_list, vendor_list, i_reponame, i_path,
                                                                  i_fileurl,
                                                                  headers, issue)
                                        time.sleep(time_w + 0.5)
                                    # print('-----------------------------------------------------------------------------')

                                    # for imp in file_imp_list:
                                    # if up_repo_name != repo_name:  # (up_repo_name not in imp_mod_list) and
                                    #     imp_mod_list.append(up_repo_name)
                                    #     i_count = i_count + 1
                                    #     print('【import:', i_count, '】: ', up_repo_name)
                                    #     time.sleep(0.8)
                                    #     (check_e, insert_e, update_e, insert_s,
                                    #      update_s) = insert_repo_depend(check_time, up_repo_name, repo_name, i_path,
                                    #                                     i_fileurl, host, user, password, db_name, check_e,
                                    #                                     insert_e, update_e, insert_s, update_s)
                            else:
                                break
                        except Exception as exp:
                            print("get search code main page error", exp,
                                  '***********************************************')
                            search_e = search_e + 1
                        print(
                            '-------------------------------------------------------------------------------------------')
        else:
            print('please check the problem！')
            print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
            # return []
    print('导入路径获取完毕，开始检测')
    # 导入路径改名问题
    b_name_l = []
    a_name_l = []
    imp_remove_list = []
    n_name_list = get_name_change_list(host, user, password, db_name)
    delete_name_list = get_name_delete_list(host, user, password, db_name)

    for imp in import_list:
        # repo_name 下游，找上游  imp 上游
        # 找imp中的repo_name
        main_mod = re.findall(r"^([^/]+?/[^/]+?)/.+?", imp)
        if main_mod:  # 说明是子模块的导入路径
            main_mod_name = main_mod[0]
            # sub_mod_path = imp.replace(main_mod_name, '')
        else:
            main_mod_name = imp
            # sub_mod_path = ''
        if main_mod_name in delete_name_list:
            imp_remove_list.append(imp)
            break
        if main_mod_name in n_name_list:
            now_name = check_name_change(main_mod_name, host, user, password, db_name)
            n_imp = imp.replace(main_mod_name, now_name)
            if imp not in b_name_l:
                b_name_l.append(imp)
            if n_imp not in a_name_l:
                a_name_l.append(n_imp)
            main_mod_name = now_name

        # # 检测是否改过名 【注意！！！】
        # now_name = check_name_change(main_mod_name, host, user, password, db_name)
        # if now_name:
        #     n_imp = imp.replace(main_mod_name, now_name)
        #     if imp not in b_name_l:
        #         b_name_l.append(imp)
        #     if n_imp not in a_name_l:
        #         a_name_l.append(n_imp)
        #     main_mod_name = now_name

        if (main_mod_name not in imp_mod_list) and main_mod_name != repo_name:
            print(imp, '拆分出repo name：', main_mod_name)
            imp_mod_list.append(main_mod_name)
        elif main_mod_name == repo_name:
            imp_remove_list.append(imp)

    for imp in b_name_l:
        if imp in import_list:
            import_list.remove(imp)
    for n_imp in a_name_l:
        import_list.append(n_imp)
    for imp in imp_remove_list:
        if imp in import_list:
            import_list.remove(imp)
    imp_remove_list = []

    for imp in import_list:
        if re.findall(r"/v(\d+?)/", imp):
            # print('存在siv', imp)
            imp_mod_name = re.findall(r"^(.+?/v\d+?)/", imp)[0]
            if imp_mod_name not in imp_final_siv_list:
                imp_final_siv_list.append(imp_mod_name)
            imp_remove_list.append(imp)
        elif re.findall(r"^(.+?/v\d+?)$", imp):
            # print('存在siv', imp)
            imp_mod_name = re.findall(r"^(.+?/v\d+?)$", imp)[0]
            if imp_mod_name not in imp_final_siv_list:
                imp_final_siv_list.append(imp_mod_name)
            imp_remove_list.append(imp)

    for imp in imp_remove_list:
        if imp in import_list:
            import_list.remove(imp)

    for imp_mod in imp_mod_list:
        print('寻找子模块->', imp_mod)
        time.sleep(2)
        (imp_sub_mod_list, search_e) = get_sub_mod_list(imp_mod, headers, search_e, time_w)
        if imp_sub_mod_list:
            sub_mod_list.extend(imp_sub_mod_list)
    sub_mod_list.sort(key=str, reverse=True)
    # print('子模块列表为：', sub_mod_list)
    # imp_remove_list = []
    # for imp in imp_final_siv_list:
    #     print('有siv的路径，进行检测', imp)
    #     if imp in sub_mod_list:
    #         print('1')
    #         imp_siv_ok_list.append(imp)
    #         imp_remove_list.append(imp)
    #         import_list.append(imp)
    #     else:
    #         print('2')
    #         imp_mod = re.findall(r"^([^/]+?/[^/]+?)/.+?", imp)
    #         if imp_mod:
    #             siv_repo_name = imp_mod[0]
    #             b_path = imp.replace(siv_repo_name, '')
    #             (result_c, issue) = get_local_go_file(siv_repo_name, b_path, time_w, issue)
    #             if result_c > 0:
    #                 print('3')
    #                 imp_siv_ok_list.append(imp)
    #                 imp_remove_list.append(imp)
    #                 import_list.append(imp)
    #         else:
    #             print('4')
    #             imp_siv_ok_list.append(imp)
    #             imp_remove_list.append(imp)
    #             import_list.append(imp)
    # for imp in imp_remove_list:
    #     import_list.remove(imp)
    for imp in import_list:
        match = 0
        for sub_mod in sub_mod_list:
            if imp != imp.replace(sub_mod, '') and (sub_mod not in imp_final_list):
                imp_final_list.append(sub_mod)
                # import_list.remove(imp)
                match = match + 1
                break
        if match == 0:
            main_mod = re.findall(r"^([^/]+?/[^/]+?)/.+?", imp)
            if main_mod:  # 说明是子模块的导入路径
                main_mod_name = main_mod[0]
                # sub_mod_path = imp.replace(main_mod_name, '')
            else:
                main_mod_name = imp
                # sub_mod_path = ''
            if main_mod_name not in imp_final_list:
                imp_final_list.append(main_mod_name)
    for imp in imp_final_siv_list:
        match = 0
        for sub_mod in sub_mod_list:
            if imp != imp.replace(sub_mod, '') and (sub_mod not in imp_final_list):
                imp_final_list.append(sub_mod)
                # import_list.remove(imp)
                match = match + 1
                break
        if match == 0:
            main_mod = re.findall(r"^([^/]+?/[^/]+?)/.+?", imp)
            if main_mod:  # 说明是子模块的导入路径
                main_mod_name = main_mod[0]
                # sub_mod_path = imp.replace(main_mod_name, '')
            else:
                main_mod_name = imp
                # sub_mod_path = ''
            if main_mod_name not in imp_final_list:
                imp_final_list.append(main_mod_name)

    print('包含siv的导包路径：', imp_final_siv_list)
    print('不含siv的导包路径：', imp_final_list)
    # print('包含siv但不影响旧机制使用', imp_siv_ok_list)

    print(
        '*******************************************************************************************************'
        '***********************************************************************************************')
    # return down_list
    # elif check_result == 2:
    #     print('********************************************')
    #     return down_list

    return imp_final_siv_list, imp_final_list, insert_e, search_e, check_e, update_e, insert_s, update_s, issue, vendor_list


# 输入repo名，以获得下游信息
def get_local_go_file(repo_name, path, time_w, issue):
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    # 查询数据库是否有
    # (check_result, down_list) = check_down_repo(repo_name, check_time)
    # url = 'https://api.github.com/' + reponame + '/search/code?q=' + downname + \
    #       '+extension:go&page=1&per_page=10'
    url = 'https://api.github.com/search/code?q=repo:' + repo_name \
          + '+path:' + path + '+extension:go&page=1&per_page=10'
    print(url)
    try:
        results = get_results(url, headers)
        # print(results)
        items = results['items']
        if items:
            return 1, issue
        else:
            return 0, issue
    except Exception as exp:
        print("get search repo local go file error", exp)
        issue = issue + '<' + 'get_local_go_file:' + repo_name + '~' + path + '>'
        return -1, issue


# 输入repo名查重，数据库repo_depend
def check_up_repo(repo_name, check_time, host, user, password, db_name):
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql_1 = "SELECT distinct d_repo FROM repo_depend WHERE u_repo='%s'" % repo_name
    sql_2 = "SELECT distinct checkdate FROM repo_depend WHERE u_repo='%s' order by checkdate DESC" % repo_name
    result_list = []
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql_1)
        check_result = check_cursor.fetchall()
        check_cursor.execute(sql_2)
        check_date = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            for r in check_result:
                result_list.append(r[0])
            print('数据库表repo_depend有：', result_list)
            print(check_date[0][0])
            if check_time >= check_date[0][0] + 6:
                return 1, result_list
            else:
                return 2, result_list
        else:
            return 0, []
    except Exception as exp:
        print("check repo_depend error:", exp, '******************************************************************')
        return -1, []


# 从数据库读取某一repo的下游列表，输入：d_repo
def get_up_list(repo_name, host, user, password, db_name):
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT distinct u_repo FROM repo_depend WHERE d_repo='%s'" % repo_name
    result_list = []
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            for r in check_result:
                result_list.append(r[0])
            print(len(check_result), '@', repo_name, '的上游有[直接依赖项]：', result_list)
            return 1, result_list
        else:
            return 0, []
    except Exception as exp:
        print("read repo_depend error:", exp, '*********************************************************************')
        return -1, []


# 检查是否有记录
def check_record(u_repo, d_repo, i_path, host, user, password, db_name):
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT id FROM repo_depend WHERE (u_repo='%s' AND d_repo='%s' AND d_fileurl='%s' " \
          "AND u_version=NULL AND u_update=NULL AND d_version=NULL AND d_update=NULL) " \
          "order by id DESC" % (u_repo, d_repo, i_path)

    result_id = 0
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchone()
        check_cursor.close()
        db_check.close()
        if check_result:
            return 1, check_result[0]
        else:
            return 0, result_id
    except Exception as exp:
        print("check repo_impact error:", exp, '**********************************************************************')
        return -1, result_id


# 插入数据库repo_depend的方法
def insert_repo_depend(check_time, u_repo, d_repo, i_path, i_fileurl, host, user, password, db_name, check_e, insert_e,
                       update_e, insert_s, update_s):
    # 查重
    (check_result, old_id) = check_record(u_repo, d_repo, i_path, host, user, password, db_name)
    time_num = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    time_num = int(time_num)
    if check_result == 0:
        insert_sql = "INSERT INTO repo_depend (id, checkdate, u_repo, d_repo, d_file, d_fileurl) VALUES ('%d','%d'," \
                     "'%s', '%s','%s', '%s')" % (time_num, check_time, u_repo, d_repo, i_path, i_fileurl)
        db = pymysql.connect(host, user, password, db_name)
        try:
            insert_cursor = db.cursor()
            # 执行sql语句
            insert_cursor.execute(insert_sql)
            db.commit()
            insert_cursor.close()
            print('insert github_go_repos_findbug successful', u_repo, '->', d_repo, '@', i_path)
            insert_s = insert_s + 1
        except Exception as exp:
            print('insert repo_depend error exception is:', exp, '****************************************************')
            print('insert repo_depend error sql:', insert_sql)
            insert_e = insert_e + 1
            # 发生错误时回滚
            db.rollback()
        db.close()
    elif check_result == 1:
        print('already insert, so update')
        update_sql = "UPDATE repo_depend SET id='%d',checkdate='%d',u_repo='%s',d_repo='%s',d_file='%s'," \
                     "d_fileurl='%s' WHERE id='%s'" % (time_num, check_time, u_repo, d_repo, i_path, i_fileurl, old_id)
        db = pymysql.connect(host, user, password, db_name)
        try:
            update_cursor = db.cursor()
            # 执行sql语句
            update_cursor.execute(update_sql)
            db.commit()
            update_cursor.close()
            print('update repo_impact successful', u_repo)
            update_s = update_s + 1
        except Exception as exp:
            print('update repo_impact error exception is:', exp, '****************************************************')
            print('update repo_impact error sql:', update_sql)
            update_e = update_e + 1
            # 发生错误时回滚
            db.rollback()
        db.close()
    else:
        print('check repo_depend error', u_repo, '->', d_repo, '@', i_path, '&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
        check_e = check_e + 1
    return check_e, insert_e, update_e, insert_s, update_s


# 输入repo名以及版本名以获得


# 输入repo名，和下游repo名，检查是否有该依赖关系
def check_requre(u_repo, d_repo, host, user, password, db_name):
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT distinct d_file FROM repo_depend WHERE (u_repo='%s' AND d_repo='%s')" % (u_repo, d_repo)
    result_list = []
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            for r in check_result:
                result_list.append(r[0])
            # print('数据库表repo_depend中读取结果：', result_list)
            return 1, result_list
        else:
            return 0, result_list
    except Exception as exp:
        print("check repo_impact error:", exp, '**********************************************************************')
        return -1, result_list


def main():
    user = 'root'
    host = '47.254.86.255'
    password = 'Ella1996'
    db_name = 'githubspider'
    insert_error = 0
    search_error = 0
    check_error = 0
    update_error = 0
    insert_success = 0
    update_success = 0
    issue_l = ''
    time_w = 1
    time_s = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    # headers = {'User-Agent': 'Mozilla/5.0',
    #            'Content-Type': 'application/json',
    #            'Accept': 'application/json',
    #            'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    fullname = 'prometheus/prometheus'
    # 调用的时候可以先从数据库中获取import_list
    import_list = []
    dir_name_list = []
    vendor_list = []
    (imp_final_siv_list, imp_final_list, insert_error, search_error, check_error, update_error, insert_success,
     update_success, issue) = get_up_repo(import_list, dir_name_list, vendor_list, fullname, host, user, password,
                                          db_name, time_w, insert_error, search_error, check_error, update_error,
                                          insert_success, update_success, issue_l)
    # (r_down, down_list) = get_up_list(fullname, host, user, password, db_name)
    # if r_down == 0:
    #     print('暂时没有找到下游repos')
    # elif r_down == -1:
    #     print('读取repo_depend失败')
    # else:
    #     print(down_list)

    # 已读取完毕，开始检测某一项是否在该repo的下游
    # d_repo = 'nicksnyder/go-i18n'
    # (r_check, check_list) = check_requre(fullname, d_repo, host, user, password, db_name)
    # print(d_repo, '【', r_check, '】 ', check_list)
    # d_repo = 'tales36/hugo3'
    # (r_check, check_list) = check_requre(fullname, d_repo, host, user, password, db_name)
    # print(d_repo, '【', r_check, '】 ', check_list)
    # (stars, forks, update, v_name, semantic) = get_repo_detail(fullname, headers)
    # get_detail_page(fullname, v_name, semantic, headers, stars, forks, update)
    print('searchError', search_error, 'insertError', insert_error, 'checkError', check_error,
          'updateError', update_error)
    print('insert successfully:', insert_success)
    print('update successfully:', update_success)
    print('other problem: ', issue_l)
    time_e = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    print(time_s, '->', time_e)


if __name__ == '__main__':
    # 声明线程池
    executor = ThreadPoolExecutor(6)
    main()
