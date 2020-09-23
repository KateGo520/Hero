import base64
import json
import re
import time
from concurrent.futures.thread import ThreadPoolExecutor
from urllib.request import Request, urlopen
import pymysql
from find_upstream_api import get_up_repo
from findbug_onenewcheck_api import get_releases_url, get_go_mod_detail
from findbug_onenewcheck_api import check_path_real, check_go_mod_detail
from findchange_api import get_go_mod, get_version
from github_api_checkone_new import check_repo_from_api, one_get_go_mod_detail


def get_results(url, headers):
    request = Request(url, headers=headers)
    response = urlopen(request).read()
    result = json.loads(response.decode())
    # time
    return result


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
def get_import(file_url, all_import_list, vendor_list, headers, record_c):
    import_list = []
    # imp_mod_list = []  【尝试在根源处理导入路径】
    file_imp_list = []  # 作用：
    file_result = get_results(file_url, headers)  # 获取文件内容
    # print(file_result)
    # 解码后，使用正则表达式，获取module声明的模块路径
    file_contents = base64.b64decode(file_result['content'])
    import_part = file_contents.decode()
    file_content = import_part.replace('"', '')
    # 匹配得到所有import语句
    file_imports = re.findall(r"import\s*\(\n*(.+?)\n*\)", file_content, re.S)
    if file_imports:
        import_l_t = re.findall(r"^[^/]*github\.com/(.+?)$", file_imports[0], re.M)
        import_l = []
        for i in import_l_t:
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
            if import_rp and (import_rp not in import_list) and (import_rp not in all_import_list):
                print('[git]上游-m1：', import_rp)
                # 先不检查子模块 【暂时】
                import_list.append(import_rp)
                # if record_c == 1:
                #     file_imp_list.append(import_rp)
                # print('1.依赖项_1:', require_r)

        import_l_t = re.findall(r"^[^/]*k8s\.com/(.+?)$", file_imports[0], re.M)
        import_l = []
        for i in import_l_t:
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
            if import_rp and (import_rp not in import_list) and (import_rp not in all_import_list):
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
        # import_rm = import_rp
        # if re.findall(r"^([^/]+?/[^/]+?)/.+?$", import_rp):
        #     import_rm = re.findall(r"^([^/]+?/[^/]+?)/", import_rp)[0]
        # if import_rm and (import_rm not in imp_mod_list):
        #     imp_mod_list.append(import_rm)
        if import_rp and (import_rp not in import_list) and (import_rp not in all_import_list):
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
        # import_rm = import_rp
        # if re.findall(r"^([^/]+?/[^/]+?)/.+?$", import_rp):
        #     import_rm = re.findall(r"^([^/]+?/[^/]+?)/", import_rp)[0]
        # if import_rm and (import_rm not in imp_mod_list):
        #     imp_mod_list.append(import_rm)
        if import_rp and (import_r not in import_list) and (import_rp not in all_import_list):
            print('[k8s]上游-m2：', import_rp)
            # 先不检查子模块 【暂时】
            import_list.append(import_rp)
            # print('1.依赖项_2:', require_r)

    # print(import_list)
    if record_c == 1:
        return import_list, file_imp_list
    else:
        return import_list


# 获取一个项目的go源文件  【k8s.com其他存储库】
def get_source_code(fullname, name, semantic, headers, time_w):
    print('获取直接依赖的信息')
    file_list = []
    # file_name_list = []
    dir_name_list = []
    import_list = []
    vendor_list = []
    repo = 'github.com/' + fullname
    vendor_list.append(repo)
    d_url = 'https://api.github.com/repos/'
    if semantic:
        d_url = d_url + fullname + '/contents?ref=' + name
    else:
        d_url = d_url + fullname + '/contents'
    print(d_url)
    try:
        page_detail = get_results(d_url, headers)
        # print(page_detail)
    except Exception as exp:
        print("When find detail page: get search error", exp, '******************************************************')
        d_url = 'https://api.github.com/repos/' + fullname + '/contents'
        try:
            page_detail = get_results(d_url, headers)
        except Exception as exp:
            print("When find detail page: get search error 222222", exp, '*********************************************'
                                                                         '***********')
            page_detail = []
    for f in page_detail:
        # 判断是否为.go源文件文件
        if re.findall(r".go$", f['name']) and f['type'] == 'file' and (f['url'] not in file_list):
            # print('直接依赖 file: ', f['name'])
            file_list.append(f['url'])
        # 判断有无子目录，获取所有文件夹中的go源文件
        elif f['type'] == 'dir' and f['name'] != 'vendor':
            # print('直接依赖 dir: ', f['name'])
            dir_name_list.append(f['name'])
        elif f['type'] == 'dir' and f['name'] == 'vendor':
            print('vendor目录')
            try:
                vendor_detail = get_results(f['url'], headers)
                # print(page_detail)
            except Exception as exp:
                print("%1% When find vendor page: get search error ", exp, '****************************************'
                                                                           '***********')
                vendor_detail = []
            for v in vendor_detail:
                # 其他存储库 ， 在这里扩展
                # 解析vendor目录  【github.com】
                if re.findall(r"github\.com", v['name']) and v['type'] == 'dir':
                    if re.findall(r"(github\.com/[^/]+?/.+?)$", v['name']):
                        vendor_repo = re.findall(r"github\.com/([^/]+?/[^/]+?)", v['name'])[0]
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
                                        vendor_repo = re.findall(r"github\.com/([^/]+?/[^/]+?)", dir_name)[0]
                                        if vendor_repo not in vendor_list:
                                            vendor_list.append(vendor_repo)
                                    else:
                                        try:
                                            vendor_page_detail = get_results(vd['url'], headers)
                                            # print(page_detail)
                                            for vdp in vendor_page_detail:
                                                if vdp['type'] == 'dir':
                                                    pkg_name = v['name'] + '/' + vd['name'] + '/' + vdp['name']
                                                    # print('vendor列表：', pkg_name)
                                                    if re.findall(r"(github\.com/[^/]+?/.+?)", pkg_name):
                                                        vendor_repo = re.findall(r"github\.com/([^/]+?/[^/]+?)",
                                                                                 pkg_name)[0]
                                                        if vendor_repo not in vendor_list:
                                                            vendor_list.append(vendor_repo)
                                        except Exception as exp:
                                            print("%3% When find vendor detail page: get search error 3[git]", exp)
                                            # vendor_page_detail = []
                        except Exception as exp:
                            print("%2% When find vendor detail page: get search error 3[git]", exp)
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
                                        vendor_repo = re.findall(r"k8s\.com/([^/]+?)", v['name'])[0]
                                        vendor_repo = 'kubernetes/' + vendor_repo
                                        if vendor_repo not in vendor_list:
                                            vendor_list.append(vendor_repo)
                        except Exception as exp:
                            print("%2% When find vendor detail page: get search error 3[k8s]", exp)
            # if 'github.com' in vendor_list:
            #     vendor_list.remove('github.com')
            # if 'github.com/' in vendor_list:
            #     vendor_list.remove('github.com/')
            # if 'k8s.com' in vendor_list:
            #     vendor_list.remove('k8s.com')
            # if 'k8s.com/' in vendor_list:
            #     vendor_list.remove('k8s.com/')
            print('vendor目录', vendor_list)  # 带有github.com

    for file in file_list:
        import_list = get_import(file, import_list, vendor_list, headers, 0)
        if len(file_list) >= 10:
            time.sleep(time_w)
    # 直接依赖 import_list
    return import_list, dir_name_list, vendor_list


# 遍历获取所有import语句 【待删】
# def get_all_import(import_path, import_list, file_list, vendor_list, headers, issue):
#     imp_mod_path = re.findall(r"github\.com/([^/]+?/[^/]+?)/.+?", import_path)
#     # imp_pkg_path = ''
#     d_url = 'https://api.github.com/repos/'
#     if imp_mod_path:
#         mod_name = imp_mod_path[0]
#         imp_pkg_path = import_path.replace('github.com/', '').replace(imp_mod_path[0], '').replace(' ', '')
#         (i_v_name, i_semantic, issue) = get_releases_url(mod_name, headers, issue)
#         print('get_all_import:', mod_name, i_v_name, i_semantic)
#
#         if i_semantic:
#             # mod_url = d_url + imp_mod_path[0] + '/contents' + '?ref=' + i_v_name
#             d_url = d_url + imp_mod_path[0] + '/contents' + imp_pkg_path + '?ref=' + i_v_name
#         else:
#             # mod_url = d_url + imp_mod_path[0] + '/contents'
#             d_url = d_url + imp_mod_path[0] + '/contents' + imp_pkg_path
#     else:
#         mod_name = import_path.replace('github.com/', '').replace(' ', '')
#         (i_v_name, i_semantic, issue) = get_releases_url(mod_name, headers, issue)
#         print('get_all_import:', mod_name, i_v_name, i_semantic)
#
#         mod_url = d_url + import_path.replace('github.com/', '').replace(' ', '') + '/contents'
#         d_url = mod_url
#     # print(d_url)
#     (go_mod, main_version, go_mod_url, version_dir, issue)=get_go_mod(mod_name, i_v_name, i_semantic, headers, issue)
#     if go_mod == 2:
#         print('新机制，直接读取go.mod文件，无需继续往下挖掘')
#         go_mod_result = get_results(go_mod_url, headers)  # 获取go.mod内容
#         # 解码后，使用正则表达式，获取module声明的模块路径
#         go_mod_content = base64.b64decode(go_mod_result['content'])
#         mod_requires = re.findall(r"require\s\(\n(.+?)\n\)", go_mod_content.decode(), re.S)
#         if not mod_requires:
#             mod_requires = re.findall(r"require\s\"(.+?\"\s.+?)\s", go_mod_content.decode(), re.S)
#
#         if mod_requires:
#             requires = mod_requires[0]  # 所有依赖项
#             requires_list = requires.split('\n')
#             for require in requires_list:
#                 require = require.replace('"', '').replace('// indirect', '').replace('+incompatible', '')
#                 require_path = require.split(' ')[0] + ' '
#                 # vendor_list.append(require.split(' ')[0])  # 停止往下检查间接依赖
#                 # require_version = require.split(' ')[1].replace(' ', '') + ' '
#                 # require = require_path + require_version
#                 # print(require_path)
#                 # bug_1_0 = re.findall(r"/v\d+?\s", require_path)
#                 # # 判断是否为伪版本,如果是，获取哈希值
#                 # not_semantic = re.findall(r"v\d+?\.\d+?\.\d+?-[^-]+?-(.+?)\s", require_version)
#                 # if not_semantic:
#                 #     require_version = not_semantic[0]
#                 repo_git_name = re.findall(r"github\.com/(.+?)\s", require_path)
#                 # print(repo_git_name, require_version, not_semantic, bug_1_0)
#                 if repo_git_name:  # 若是github上的存储库
#                     if require.split(' ')[0] not in import_list:
#                         import_list.append(require.split(' ')[0])
#                     # vendor_list.append(require.split(' ')[0])  # 停止往下检查间接依赖
#                     # if bug_1_0:
#                     #     import_list.append(require.split(' ')[0])
#     else:
#         pkg_list = get_pkg_file(d_url, file_list, headers)
#         file_list = file_list + pkg_list
#         # pkg_import_list = []
#         for file_url in pkg_list:
#             # print(file_url)
#             pkg_import_list = get_pkg_import(file_url, import_list, vendor_list, headers)
#             import_list = import_list + pkg_import_list
#             # 暂不检测第三层
#             # for pkg_import_path in pkg_import_list:
#             #     if re.findall(r"/v(\d+?)/", pkg_import_path) or re.findall(r"/v(\d+?)$", pkg_import_path):
#             #         print('problem 1-1')
#             #     else:
#             #         print('继续获取间接依赖项，目前获取的对象是：', pkg_import_path)
#             #         (import_list, file_list) = get_all_import(pkg_import_path, import_list, file_list, vendor_list,
#             #                                                   headers)
#
#     return import_list, file_list, issue


# 获取详情页的：go.mod文件【是否有，module声明】，版本号，子文件夹/vN，module声明的路径是否符合模块机制的要求


def check_bug_old_repo(modname, name, semantic, bug_type_num, bug_list, break_type_num, break_list, headers,
                       issue, time_w, host, user, password, db_name, insert_e, search_e, check_e, update_e, insert_s,
                       update_s, check_type):
    if re.findall(r"^[^/]+?/[^/]+?(/.+?)$", modname):
        fullname = re.findall(r"^([^/]+?/[^/]+?)/.+?$", modname)[0]
        # sub_mod = re.findall(r"^[^/]+?/[^/]+?(/.+?)$", modname)[0]
    else:
        fullname = modname
        # sub_mod = ''
    nc_ur = 0  # need check up repos
    imp_version = '-1'
    # from_type = '[1]' + fullname + '@' + name
    from_type = fullname + '@' + name
    d_repo = fullname + '@' + name
    # 找到vendor文件夹，以及出了vendor文件夹外的所有的文件路径
    (import_list, dir_name_list, vendor_list) = get_source_code(fullname, name, semantic, headers, time_w)
    # 获取上游repos
    (imp_final_siv_list, imp_final_list, insert_e, search_e, check_e, update_e, insert_s, update_s,
     issue) = get_up_repo(import_list, dir_name_list, vendor_list, fullname, host, user, password, db_name,
                          time_w, insert_e, search_e, check_e, update_e, insert_s, update_s, issue)

    # 旧检测方法，先注释
    # for imp_siv in imp_final_siv_list:
    #     # 问题1-2，A，已经发生
    #     break_type_num[0] = break_type_num[0] + 1
    #     break_list[0] = break_list[0] + '$' + '1.2' + ':' + imp_siv
    for imp in imp_final_list:
        imp_mod = re.findall(r"^([^/]+?/[^/]+?)/.+?", imp)
        if imp_mod:  # 说明是子模块的导入路径
            imp_mod_name = imp_mod[0]
        else:
            imp_mod_name = imp
        print('开始正常检测：')
        bu = 0
        # 针对新用户，未来更新时会发生的bug，检测该包的最新版本
        (stars, forks, updated, r_v_name, r_semantic, issue) = get_repo_detail(imp_mod_name, headers, issue)
        r_hash = ''
        # [r[0], v_name, stars, forks, updated, semantic]
        repo_mes_list = [stars, forks, updated, r_semantic]
        # 获取主版本号：
        imp_main_v = re.findall(r"^v(\d+?)\.", r_v_name)
        if imp_main_v:
            r_v_siv = str(imp_main_v[0])
        else:
            if re.findall(r"^v(\d+?)$", r_v_name):
                imp_main_v = re.findall(r"^v(\d+?)$", r_v_name)
                r_v_siv = str(imp_main_v[0])
            else:
                r_v_siv = '-1'
        (go_mod_module, version_number, path_match, go_mod, go_mod_url, version_dir,
         issue) = one_get_go_mod_detail(imp, r_v_name, r_v_siv, headers, issue)
        # (imp_mod_name, sub_mod_path, imp_siv, repo_version, v_siv, result, go_mod, go_mod_url, v_dir_url,
        #  issue) = check_path_real(imp, i_v_name, headers, issue)
        # l_1 = [8, 5, -8, -5]  # -8, -5
        # if result in l_1:  # siv为实体路径，旧机制可以获取到
        #     if go_mod == 2:
        #         path_match = check_go_mod_detail(imp_mod_name, sub_mod_path, imp_siv, v_siv, go_mod_url, headers)
        #         if path_match != 2:
        #             # 问题4-0，D，已经发生
        #             bug_type_num[6] = bug_type_num[6] + 1
        #             bug_list[6] = bug_list[6] + '$' + imp_mod_name + ' ' + i_v_name
        #             bu = 4
        #             print('[8,5]问题4-0', imp + ' ' + i_v_name)
        # l_2 = [7, 6, 4, -7, -6, -4]  # , -7, -6, -4
        # if result in l_2:
        #     # 问题1-1，A，旧用户升级预警
        #     bug_type_num[1] = bug_type_num[1] + 1
        #     bug_list[1] = bug_list[1] + '$' + '1.1' + ':' + imp + ' ' + i_v_name
        #     print('[7]问题1-1', imp + ' ' + i_v_name)
        #     if go_mod == 2:
        #         path_match = check_go_mod_detail(imp_mod_name, sub_mod_path, imp_siv, v_siv, go_mod_url, headers)
        #         if path_match == 1:
        #             # 问题3-0，C，下游新用户升级预警
        #             bug_type_num[4] = bug_type_num[4] + 1
        #             bug_list[4] = bug_list[4] + '$' + imp_mod_name + ' ' + i_v_name
        #             bu = 3
        #             print('[7]问题3-0', imp + ' ' + i_v_name)
        #         elif path_match == 0:
        #             # 问题4-0，D，下游新用户升级预警
        #             bug_type_num[6] = bug_type_num[6] + 1
        #             bug_list[6] = bug_list[6] + '$' + imp_mod_name + ' ' + i_v_name
        #             bu = 4
        #             print('[7]问题4-0', imp + ' ' + i_v_name)
        #
        # l_3 = [3, 2, 1, -3, -2]  # -3, -2, -1
        # if result in l_3:
        #     if result == 2:
        #         # 问题1-1，A，旧用户升级预警
        #         bug_type_num[1] = bug_type_num[1] + 1
        #         bug_list[1] = bug_list[1] + '$' + '1.1' + ':' + imp_mod_name + ' ' + i_v_name
        #         print('[3]问题1-1', imp + ' ' + i_v_name)
        #     if go_mod == 2:
        #         path_match = check_go_mod_detail(imp_mod_name, sub_mod_path, imp_siv, v_siv, go_mod_url, headers)
        #         if int(v_siv) >= 2 and path_match == 1:
        #             # 问题3-0，C，下游新用户升级预警
        #             bug_type_num[4] = bug_type_num[4] + 1
        #             bug_list[4] = bug_list[4] + '$' + imp_mod_name + ' ' + i_v_name
        #             bu = 3
        #             print('[3]问题3-0', imp + ' ' + i_v_name)
        #         elif path_match == 0 and result != 2:
        #             # 问题4-0，D，下游新用户升级预警
        #             bug_type_num[6] = bug_type_num[6] + 1
        #             bug_list[6] = bug_list[6] + '$' + imp_mod_name + ' ' + i_v_name
        #             bu = 4
        #             print('[3]问题4-0', imp + ' ' + i_v_name)

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

        if check_type == 0:
            print('检测是否有传递依赖，查询repo_impact库')
            # 0, prob_list, '', '', -1  查询repo_impact库
            (search_r, r_list, r_vname) = search_check_go_repos(imp_mod_name, host, user, password, db_name)
            if search_r < 1:
                # 存库 need_check_fo  db
                # from_type = fullname + '@' + name
                # d_repo = fullname + '@' + name
                if go_mod == 2:
                    time.sleep(0.8)
                    insert_db = 'check_go_repos'
                    (search_e, insert_e, check_e, update_e, insert_s, update_s,
                     issue_l) = check_repo_from_api(imp, r_v_name, r_hash, repo_mes_list, host, user,
                                                    password, db_name, search_e, insert_e, check_e, update_e, insert_s,
                                                    update_s, issue, time_w, check_type, insert_db)
                    (search_r, r_list, r_vname) = search_check_go_repos(imp_mod_name, host, user, password, db_name)
                else:
                    (insert_e, check_e) = insert_need_check_fo(imp_mod_name, imp_version, from_type, d_repo, host,
                                                               user, password, db_name, insert_e, check_e)
                    nc_ur = nc_ur + 1

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
        else:  # check_type == 1
            # 存库 need_check_fo  db
            # from_type = '[1]' + fullname + '@' + name
            # d_repo = fullname + '@' + name
            if go_mod == 2:
                time.sleep(0.8)
                insert_db = 'check_go_repos'
                (search_e, insert_e, check_e, update_e, insert_s, update_s,
                 issue_l) = check_repo_from_api(imp, r_v_name, r_hash, repo_mes_list, host, user,
                                                password, db_name, search_e, insert_e, check_e, update_e, insert_s,
                                                update_s, issue, time_w, check_type, insert_db)
                (search_r, r_list, r_vname) = search_check_go_repos(imp_mod_name, host, user, password, db_name)
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
                (insert_e, check_e) = insert_need_check_fo(imp_mod_name, imp_version, from_type, d_repo, host,
                                                           user, password, db_name, insert_e, check_e)
                nc_ur = nc_ur + 1
    return (bug_type_num, bug_list, break_type_num, break_list, insert_e, search_e, check_e, update_e, insert_s,
            update_s, issue, nc_ur, from_type)


def get_detail_page(fullname, name, semantic, headers, stars, forks, update, host, user, password, db_name,
                    check_date, search_e, insert_e, check_e, update_e, insert_s,
                    update_s, issue_l, time_w):
    # 未来会发生问题的地方
    bug_type_num = [0, 0, 0, 0, 0, 0, 0, 0]  # 没有问题，默认为0
    bug_list = ['', '', '', '', '', '', '', '']
    # 已经发生问题的地方
    break_type_num = [0, 0, 0, 0]
    break_list = ['', '', '', '']
    issue = ''
    # 获取本项目的go.mod文件的情况
    (go_mod, main_version, go_mod_url, version_dir, issue) = get_go_mod(fullname, name, semantic, headers, issue)
    if go_mod == 2:  # 如果有非空的go.mod文件，说明是新机制
        print('如果有非空的go.mod文件，说明是新机制')
    else:
        if go_mod == 1:
            print('go.mod文件为空######################################################################################')

        # 遍历获取import导包语句
        print('本项目为非模块机制，需要从源文件中读取导包路径')
        check_type = 0  # 是否要在检测上游依赖项时，检测大库中repo的检测结果，0是检测；其他是不检测，实现单个项目的完全自检测
        (bug_type_num, bug_list, break_type_num, break_list, insert_e, search_e,
         check_e, update_e, insert_s, update_s, issue, nc_ur,
         from_type) = check_bug_old_repo(fullname, name, semantic, bug_type_num, bug_list, break_type_num, break_list,
                                         headers, issue, time_w, host, user, password, db_name, insert_e, search_e,
                                         check_e, update_e, insert_s, update_s, check_type)
        # 打印检测结果
        impact = [0, 0]
        insert = 0
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
        time.sleep(0.6)
        time_str = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        time_num = int(time_str)
        # if insert:
        #     insert_info(time_num, fullname, stars, forks, update, name, bug_type_num, bug_list, break_type_num,
        #                 break_list, impact)
        # insert_impact(time_num, fullname, update, name, bug_type_num, break_type_num, impact)
        if insert > 0:
            # time_num, fullname, stars, forks, update, name, bug_type, bug_list, break_type, break_list, impact,
            #                 check_date, host, user, password, db_name, check_error, insert_error, insert_success
            (check_e, insert_e,
             insert_s) = insert_info(time_num, fullname, stars, forks, update, name, bug_type_num, bug_list,
                                     break_type_num, break_list, impact, check_date, host, user, password,
                                     db_name, check_e, insert_e, insert_s)
        # time_num, fullname, update, name, bug_type, break_type, impact, host, user, password, db_name,
        #                   check_error, insert_error, update_error, insert_success, update_success
        time.sleep(time_w + 0.4)
        (insert_e, update_e, check_e, insert_s,
         update_s) = insert_impact(time_num, fullname, update, name, bug_type_num, break_type_num, impact, host,
                                   user, password, db_name, check_e, insert_e, update_e, insert_s, update_s)
        # 检测上游的项目
        # if nc_ur > 0:
        #     c_method = ''  # 空，不是特定表，有表名，是特定表，在后续检测结果返回时查表不同，需要额外标注
        #     (search_e, insert_e, check_e, update_e, insert_s, update_s,
        #      issue_l) = check_up_repo_fo(from_type, host, user, password, db_name, search_e, insert_e, check_e,
        #                                  update_e, insert_s, update_s, issue_l, time_w, c_method)
    if issue:
        issue_l = issue_l + '【' + fullname + ':' + issue + '】'
    return insert_e, check_e, update_e, insert_s, update_s, issue_l


# def check_up_repo_fo(from_type, host, user, password, db_name, search_e, insert_e, check_e, update_e, insert_s,
#                      update_s, issue_l, time_w, c_method):
#
#     (need_check_list, check_e) = get_need_check_repo_list(from_type, host, user, password, db_name, check_e)
#     if need_check_list:
#         for repo_check in need_check_list:
#             repo_fullname = repo_check[1]
#             repo_version = repo_check[2]
#             db_id = repo_check[0]
#             check_type = repo_check[3]
#             if repo_fullname:
#                 (search_e, insert_e, check_e, update_e, insert_s, update_s,
#                  issue_l) = check_repo_fo(repo_fullname, repo_version, host, user, password, db_name, search_e,
#                                           insert_e, check_e, update_e, insert_s, update_s, issue_l, time_w, check_type,
#                                           db_id, c_method)
#             else:
#                 print('repo_name 不正确')
#         (search_e, insert_e, check_e, update_e, insert_s, update_s,
#          issue_l) = check_up_repo_fo(from_type, host, user, password, db_name, search_e, insert_e, check_e, update_e,
#                                      insert_s, update_s, issue_l, time_w, c_method)
#     else:
#         print('循环获取检测上游完毕，已无该存储库的上游')
#     return search_e, insert_e, check_e, update_e, insert_s, update_s, issue_l
#

# 获取指定repo的依赖列表
def get_need_check_repo_list(from_type, host, user, password, db_name, check_e):
    need_check_list = []
    sql = "SELECT id,full_name,v_name,layer FROM need_check_fo WHERE bug_update=0 AND from_type='%s' " % from_type
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            print(check_result)
            # num = len(check_result)
            for r in check_result:
                check_type = '[o]' + from_type + '@' + str(r[3])
                need_check_list.append([r[0], r[1], r[2], check_type])
    except Exception as exp:
        print("get need_check_fo error",
              exp, '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
        print(sql)
    return need_check_list, check_e


# 存库 need_check_fo  db
def insert_need_check_fo(full_name, imp_version, from_type, d_repo, host, user, password, db_name, insert_e, check_e):
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
        time_str = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        time_num = int(time_str)
        update_sql = ''
        if check_result:
            # 有该项
            if check_result[0][1] != 0:
                update_sql = "UPDATE need_check_fo SET id='%d',bug_update='%d' " \
                             "WHERE id='%d'" % (time_num, 0, check_result[0][0])
        else:
            update_sql = "INSERT INTO need_check_fo (id,bug_update,full_name,v_name,from_type,d_repo) VALUES ('%d'," \
                         "'%d','%s','%s','%s','%s')" % (time_num, 0, full_name, imp_version, from_type, d_repo)
        if update_sql:
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


# 查询数据库check_go_repos_20200529， check_go_repos
def search_check_go_repos(fullname, host, user, password, db_name):
    # 查询该存储库是否存在于数据库中，返回查询数量
    # num1_0,num1_1,break1,num2_0,num2_1,break2,num3_0,num3_1,break3,num4_0,num4_1,break4
    sql = "SELECT v_name,num1_0,num1_1,break1,num2_0,num2_1,break2,num3_0,num3_1,break3,num4_0,num4_1,break4 " \
          "FROM check_go_repos_20200529 WHERE full_name ='%s'" % fullname
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        prob_list = []
        if check_result:
            # 有该项
            if check_result[0][1] > 0 or check_result[0][2] > 0 or check_result[0][3] > 0:
                # 有影响,问题一
                prob_list.append('1-1')
            if check_result[0][4] > 0 or check_result[0][5] > 0 or check_result[0][6] > 0:
                # 有影响,问题二
                prob_list.append('2-0')
            if check_result[0][7] > 0 or check_result[0][8] > 0 or check_result[0][9] > 0:
                # 有影响,问题三
                prob_list.append('3-0')
            if check_result[0][7] > 0 or check_result[0][8] > 0 or check_result[0][9] > 0:
                # 有影响,问题四
                prob_list.append('4-0')

                return 2, prob_list, check_result[0][0]
            else:
                print('check_go_repos_20200529 有该项，无影响')
                return 1, prob_list, check_result[0][1]
        else:
            # 无该项
            print('check_go_repos_20200529 无该项')
            sql = "SELECT v_name,num1_0,num1_1,break1,num2_0,num2_1,break2,num3_0,num3_1,break3,num4_0,num4_1,break4 " \
                  "FROM check_go_repos WHERE full_name ='%s'" % fullname
            try:
                # 执行sql语句
                db_check = pymysql.connect(host, user, password, db_name)
                check_cursor = db_check.cursor()
                check_cursor.execute(sql)
                check_result = check_cursor.fetchall()
                check_cursor.close()
                db_check.close()
                prob_list = []
                if check_result:
                    # 有该项
                    if check_result[0][1] > 0 or check_result[0][2] > 0 or check_result[0][3] > 0:
                        # 有影响,问题一
                        prob_list.append('1-1')
                    if check_result[0][4] > 0 or check_result[0][5] > 0 or check_result[0][6] > 0:
                        # 有影响,问题二
                        prob_list.append('2-0')
                    if check_result[0][7] > 0 or check_result[0][8] > 0 or check_result[0][9] > 0:
                        # 有影响,问题三
                        prob_list.append('3-0')
                    if check_result[0][7] > 0 or check_result[0][8] > 0 or check_result[0][9] > 0:
                        # 有影响,问题四
                        prob_list.append('4-0')

                        return 2, prob_list, check_result[0][0]
                    else:
                        print('check_go_repos 有该项，无影响')
                        return 1, prob_list, check_result[0][1]
                else:
                    # 无该项
                    print('check_go_repos 无该项')
                    return 0, prob_list, ''
            except Exception as exp:
                print("check check_go_repos name error:", exp, '************************************************')
                return -1, [], ''
    except Exception as exp:
        print("check check_go_repos_20200529 name error:", exp, '************************************************')
        return -1, [], ''


# 查询repo_impact数据库，通过fullname查询
def search_repo(fullname, host, user, password, db_name):
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT update_time,v_name,o_bug,n_bug,old_impact,new_impact,gomod " \
          "FROM repo_impact WHERE full_name = '%s'" % fullname
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        prob_list = []
        if check_result:
            # 有该项
            if check_result[0][4] == 1 or check_result[0][5] == 1:
                # 有影响
                print('repo_impact 有该项，且有影响')
                if check_result[0][2] != '000':
                    prob_list.append('1-1')
                if check_result[0][3][0:3] != '000':
                    prob_list.append('2-0')
                if check_result[0][3][3:6] != '000':
                    prob_list.append('3-0')
                if check_result[0][3][6:9] != '000':
                    prob_list.append('4-0')
                return 2, prob_list, check_result[0][0], check_result[0][1], check_result[0][6]
            else:
                print('repo_impact 有该项，无影响')
                return 1, prob_list, check_result[0][0], check_result[0][1], check_result[0][6]
        else:
            # 无该项
            print('repo_impact 无该项')
            return 0, prob_list, '', '', -1
    except Exception as exp:
        print("check repos name error:", exp, '************************************************')
        return -1, [], '', '', -1


# 插入数据库的方法
def insert_info(time_num, fullname, stars, forks, update, name, bug_type, bug_list, break_type, break_list, impact,
                check_date, host, user, password, db_name, check_error, insert_error, insert_success):
    # 查重
    check_bug_list = [bug_type[1], bug_list[1], break_type[0], break_list[0], bug_type[2], bug_list[2], bug_type[4],
                      bug_list[4], bug_type[6], bug_list[6]]
    check_result = check_record(fullname, update, impact, check_date, host, user, password, db_name, check_bug_list)
    if check_result == 0:
        insert_sql = "INSERT INTO github_go_repos_findbug (id,checkdate,full_name,star,fork,update_time, v_name, " \
                     "num1_1,list1_1,break1,break_list1,num2_0,list2_0,num3_0,list3_0,num4_0,list4_0,old_impact," \
                     "new_impact,repo_type) VALUES ('%d','%d','%s','%d','%d','%s','%s','%d','%s','%d','%s','%d'," \
                     "'%s','%d','%s','%d','%s','%d','%d'," \
                     "'%d')" % (time_num, check_date, fullname, stars, forks, update, name, bug_type[1], bug_list[1],
                                break_type[0], break_list[0], bug_type[2], bug_list[2],  bug_type[4], bug_list[4],
                                bug_type[6], bug_list[6], impact[0], impact[1], 0)
        db = pymysql.connect(host, user, password, db_name)
        try:
            insert_cursor = db.cursor()
            # 执行sql语句
            insert_cursor.execute(insert_sql)
            db.commit()
            insert_cursor.close()
            print('insert github_go_repos_findbug successful', fullname)
            insert_success = insert_success + 1
        except Exception as exp:
            print('insert github_go_repos_findbug error exception is:', exp, '***********************************')
            print('insert github_go_repos_findbug error sql:', insert_sql)
            insert_error = insert_error + 1
            # 发生错误时回滚
            db.rollback()
        db.close()
    elif check_result == 1:
        print('already insert')
    else:
        print('check github_go_repos_findbug error', fullname, '**********************************')
        check_error = check_error + 1
    return check_error, insert_error, insert_success


# 查重
def check_record(fullname, update, impact, check_date, host, user, password, db_name, check_bug_list):
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT id FROM github_go_repos_findbug WHERE (checkdate='%d' AND full_name='%s' AND update_time='%s' AND " \
          "old_impact='%d' AND new_impact='%d' AND num1_1='%d' AND list1_1='%s' AND break1='%d' AND " \
          "break_list1='%s' AND num2_0='%d' AND list2_0='%s' AND num3_0='%d' AND list3_0='%s' AND num4_0='%d' AND " \
          "list4_0='%s')" % (check_date, fullname, update, impact[0], impact[1], check_bug_list[0], check_bug_list[1],
                             check_bug_list[2], check_bug_list[3], check_bug_list[4], check_bug_list[5],
                             check_bug_list[6], check_bug_list[7], check_bug_list[8], check_bug_list[9])
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            # print('查重结果，有：', check_result)
            print('查重结果，有')
            return 1
        else:
            return 0
    except Exception as exp:
        print("check github_go_repos_findbug error:", exp, '********************************************************')
        return -1


# 更新数据库表repo_impact
def insert_impact(time_num, fullname, update, name, bug_type, break_type, impact, host, user, password, db_name,
                  check_error, insert_error, update_error, insert_success, update_success):
    # 查重
    (check_result, result_list) = check_impact(fullname, host, user, password, db_name)
    bu = ['0', '0', '0', '0', '0', '0', '0', '0']
    bre = ['0', '0', '0', '0']
    for i in range(0, 8):
        if bug_type[i]:
            bu[i] = '1'
        else:
            bu[i] = '0'
    for i in range(0, 4):
        if break_type[i]:
            bre[i] = '1'
        else:
            bre[i] = '0'
    o_bug = bu[0] + bu[1] + bre[0]
    n_bug = bu[2] + bu[3] + bre[1] + bu[4] + bu[5]
    n_bug = n_bug + bre[2] + bu[6] + bu[7] + bre[3]
    if check_result == 0:
        insert_sql = "INSERT INTO repo_impact (id,full_name,update_time,v_name,o_bug,n_bug,old_impact,new_impact," \
                     "gomod) VALUES ('%d','%s','%s','%s','%s','%s','%d','%d','%d')" % (time_num, fullname, update,
                                                                                       name, o_bug, n_bug, impact[0],
                                                                                       impact[1], 0)
        db = pymysql.connect(host, user, password, db_name)
        try:
            insert_cursor = db.cursor()
            # 执行sql语句
            insert_cursor.execute(insert_sql)
            db.commit()
            insert_cursor.close()
            print('insert repo_impact successful', fullname)
            insert_success = insert_success + 1
        except Exception as exp:
            print('insert repo_impact error exception is:', exp, '**************************************')
            print('insert repo_impact error sql:', insert_sql)
            insert_error = insert_error + 1
            # 发生错误时回滚
            db.rollback()
        db.close()
    elif check_result == 1:
        print('already insert at repo_impact')
        # update_time,v_name,o_bug,n_bug,old_impact,new_impact,gomod
        print(type(result_list[2]), type(result_list[4]))
        if result_list[2] != o_bug or result_list[3] != n_bug or result_list[4] != impact[0] \
                or result_list[5] != impact[1] or result_list[6] != 0:
            before_bug = result_list[2] + '&' + result_list[3]
            now_bug = o_bug + '&' + n_bug
            impact_change = [time_num, fullname, result_list[0], result_list[1], update, name, before_bug, now_bug,
                             result_list[4], result_list[5], impact[0], impact[1], result_list[6], 0]
            (insert_error, insert_success) = insert_impact_change(impact_change, host, user, password, db_name,
                                                                  insert_error, insert_success)
        # repo_impact (id,full_name,update_time,old_impact,new_impact)new_impact
        update_sql = "UPDATE repo_impact SET id='%d',update_time='%s',v_name='%s',o_bug='%s',n_bug='%s'," \
                     "old_impact='%d',new_impact='%d',gomod='%d' WHERE full_name='%s'" % (time_num, update, name,
                                                                                          o_bug, n_bug, impact[0],
                                                                                          impact[1], 0, fullname)
        db = pymysql.connect(host, user, password, db_name)
        try:
            update_cursor = db.cursor()
            # 执行sql语句
            update_cursor.execute(update_sql)
            db.commit()
            update_cursor.close()
            print('update repo_impact successful', fullname)
            update_success = update_success + 1
        except Exception as exp:
            print('update repo_impact error exception is:', exp, '**********************************')
            print('update repo_impact error sql:', update_sql)
            update_error = update_error + 1
            # 发生错误时回滚
            db.rollback()
        db.close()
    else:
        print('check repo_impact error', fullname, '*************************************************')
        check_error = check_error + 1
    return check_error, insert_error, update_error, insert_success, update_success


# 查重: 数据库表repo_impact
def check_impact(fullname, host, user, password, db_name):
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT update_time,v_name,o_bug,n_bug,old_impact,new_impact,gomod " \
          "FROM repo_impact WHERE full_name='%s'" % fullname
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            print('数据库表repo_impact有：', check_result)
            return 1, check_result[0]
        else:
            return 0, []
    except Exception as exp:
        print("check repo_impact error:", exp, '***********************************************')
        return -1, []


# 更新repo_impact_change数据库，记录库的更新对下游的影响
def insert_impact_change(change, host, user, password, db_name, insert_error, insert_success):
    # impact_change = [time_num, fullname, result_list[0], result_list[1], update, name, before_bug, now_bug,
    #                              result_list[4], result_list[5], impact[0], impact[1], result_list[6], 1]
    ic_type = str(change[8]) + str(change[9]) + '-' + str(change[10]) + str(change[11])
    gc_type = str(change[12]) + '-' + str(change[13])
    insert_sql = "INSERT INTO repo_impact_change (id,full_name,b_update,b_v_name,n_update,n_v_name,before_bug," \
                 "now_bug,bo_impact,bn_impact,no_impact,nn_impact,ic_type,b_gomod," \
                 "n_gomod,gc_type) VALUES ('%d','%s','%s','%s','%s','%s','%s','%s','%d','%d','%d'," \
                 "'%d','%s','%d','%d','%s')" % (change[0], change[1], change[2], change[3], change[4], change[5],
                                                change[6], change[7], change[8], change[9], change[10], change[11],
                                                ic_type, change[12], change[13], gc_type)
    db = pymysql.connect(host, user, password, db_name)
    try:
        insert_cursor = db.cursor()
        # 执行sql语句
        insert_cursor.execute(insert_sql)
        db.commit()
        insert_cursor.close()
        print('insert repo_impact_change successful', change[1])
        insert_success = insert_success + 1
    except Exception as exp:
        print('insert repo_impact_change error exception is:', exp, '*****************************')
        print('insert repo_impact_change error sql:', insert_sql)
        insert_error = insert_error + 1
        # 发生错误时回滚
        db.rollback()
    db.close()
    return insert_error, insert_success


# 这里与新机制检测的一样，可以考虑合并
def get_repo_detail(fullname, headers, issue):
    one_page_url = 'https://api.github.com/repos/' + fullname
    # one_page_url = 'https://api.github.com/repos/gohugoio/hugo'
    # print(one_page_url)
    try:
        one_page_results = get_results(one_page_url, headers)
        one_stars = one_page_results['stargazers_count']  # 存：标星数量
        one_forks = one_page_results['forks_count']  # 存：forks数量
        one_updated = one_page_results['updated_at']  # 存：数据库更新时间
        releases_url = one_page_results['releases_url']  # 获取版本信息api
        (v_name, semantic) = get_version(releases_url, headers)
    except Exception as exp:
        print("************** get search repo_detail error", exp, '**************')
        v_name = 'master'
        semantic = False
        one_stars = 0
        one_forks = 0
        one_updated = ''
        issue = issue + '<get_repo_detail:' + fullname + '>'
    return one_stars, one_forks, one_updated, v_name, semantic, issue


def update_old_bug(new_fullname, check_date, host, user, password, db_name, insert_error, search_error, check_error,
                   update_error, insert_success, update_success, issue, time_w):
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    (stars, forks, update, v_name, semantic, issue) = get_repo_detail(new_fullname, headers, issue)
    (insert_error, check_error, update_error, insert_success, update_success,
     issue) = get_detail_page(new_fullname, v_name, semantic, headers, stars, forks, update, host, user, password,
                              db_name, check_date, search_error, insert_error, check_error, update_error,
                              insert_success, update_success, issue, time_w)
    return insert_error, search_error, check_error, update_error, insert_success, update_success, issue


def get_repo_name_list(host, user, password, db_name):
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT full_name FROM repo_impact WHERE gomod=0"
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            name_list = []
            for result in check_result:
                name_list.append(result[0])
            print('数据库表repo_impact有：', name_list)
            return 1, name_list
        else:
            return 0, []
    except Exception as exp:
        print("try get repo from repo_impact error:", exp, '***********************************************')
        return -1, []
