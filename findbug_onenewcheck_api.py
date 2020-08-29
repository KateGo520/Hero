# 注意是否存在repo名称修改的问题，有的话，引用find_upstream_api里的方法now_name=check_name_change(repo_name,
# host, user, password, db_name)
import base64
import json
import re
import time
from concurrent.futures.thread import ThreadPoolExecutor
from urllib.request import Request, urlopen
import pymysql
from findchange_20200529_api import get_version, get_go_mod_detail, judge_repo_type
from find_local_use import get_local_use
# from one_check_api.findchange_api import get_version, get_go_mod_detail, judge_repo_type
# from one_check_api.find_local_use import get_local_use


def get_results(url, headers):
    request = Request(url, headers=headers)
    response = urlopen(request).read()
    result = json.loads(response.decode())
    # time
    return result


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
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
              '~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print('####', fullname, one_stars, one_forks, v_name, semantic)
    except Exception as exp:
        print("************** get search repo_detail error", exp, '*******************************************')
        v_name = 'master'
        semantic = False
        one_stars = 0
        one_forks = 0
        one_updated = ''
        issue = issue + '<11111111111 get_repo_detail:' + fullname + '>'
    return one_stars, one_forks, one_updated, v_name, semantic, issue


def get_releases_url(fullname, headers, issue):
    # page_detail = []
    # 先判断有无子模块
    repo_name_list = fullname.split('/')
    repo_name = repo_name_list[0] + '/' + repo_name_list[1]
    subdir_name = ''
    c = 0
    for n in repo_name_list:
        c = c + 1
        if c > 2:
            subdir_name = subdir_name + '/' + n
    if subdir_name:
        print('1.拆分出主模块路径和子模块的相对路径：', repo_name, subdir_name, '**********************************'
                                                              '**get_releases_url*******')
        d_url = 'https://api.github.com/repos/' + repo_name
    else:
        d_url = 'https://api.github.com/repos/' + fullname
    try:
        one_page_results = get_results(d_url, headers)
        releases_url = one_page_results['releases_url']  # 获取版本信息api
        (v_name, semantic) = get_version(releases_url, headers)
    except Exception as exp:
        print("************** get search releases_url error", exp, '*******************************************')
        v_name = 'master'
        semantic = False
        issue = issue + '<get_releases_url:' + fullname + '>'
    return v_name, semantic, issue


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


# 检测子模块是否为实体路径
def check_path_real(repo_name, repo_version, headers, issue):
    result = 0
    (main_mod_name, sub_mod_path, imp_siv, repo_version, v_siv) = deal_require_path(repo_name, repo_version)
    v_siv_num = int(v_siv)
    # print('imp_siv与v_siv作比较', imp_siv, '和', v_siv)
    if imp_siv == ('/v' + v_siv) and repo_version:  # 导入路径中存在siv
        # print('路径中有siv, 且经验证与主版本号一致')  # 不一致的就当做没有siv
        # 创建路径，通过api（并非search 的api，因为无法限定版本），获取是否能读取数据
        d_url = 'https://api.github.com/repos/' + main_mod_name + '/contents' + sub_mod_path + '?ref=' + repo_version
        try:
            page_detail = get_results(d_url, headers)
            if imp_siv == sub_mod_path:
                result = 5
            else:
                result = 8
        except Exception as exp:
            print("check1.[-5,-8]可能是版本获取不到：", exp, '************************************check_path_real*******')
            d_url = 'https://api.github.com/repos/' + main_mod_name + '/contents' + sub_mod_path
            try:
                page_detail = get_results(d_url, headers)
                if imp_siv == sub_mod_path:
                    result = -5
                else:
                    result = -8
            except Exception as exp:
                print('check2.[4,7]可能siv不是实体路径：', exp, '*********************************check_path_real*******')
                if imp_siv == sub_mod_path:  # usr/repo/siv
                    d_url = 'https://api.github.com/repos/' + main_mod_name + '/contents?ref=' + repo_version
                    try:
                        page_detail = get_results(d_url, headers)
                        result = 4
                    except Exception as exp:
                        print("check3.[-4]可能是版本获取不到：", exp, '***************************check_path_real*******')
                        d_url = 'https://api.github.com/repos/' + main_mod_name + '/contents'
                        try:
                            page_detail = get_results(d_url, headers)
                            result = -4
                        except Exception as exp:
                            print("check4.[0]可能是repo名不准确：", exp, '**********************check_path_real********')
                            page_detail = []
                            issue = issue + '<' + 'get_go_mod:' + main_mod_name + '>'
                else:  # usr/repo/submod/siv
                    sub_mod_path = sub_mod_path.replace(imp_siv, '')
                    d_url = 'https://api.github.com/repos/' + main_mod_name + '/contents' + sub_mod_path
                    d_url = d_url + '?ref=' + repo_version
                    try:
                        page_detail = get_results(d_url, headers)
                        result = 7
                    except Exception as exp:
                        print("check3.[-7]可能是版本获取不到：", exp, '**************************check_path_real*******')
                        d_url = 'https://api.github.com/repos/' + main_mod_name + '/contents' + sub_mod_path
                        try:
                            page_detail = get_results(d_url, headers)
                            result = -7
                        except Exception as exp:
                            print("check4.[6]可能是submod为非实体：", exp, '********************************************'
                                                                   '***************check_path_real********')
                            d_url = 'https://api.github.com/repos/' + main_mod_name + '/contents'
                            d_url = d_url + '?ref=' + repo_version
                            try:
                                page_detail = get_results(d_url, headers)
                                result = 6
                            except Exception as exp:
                                print("check3.[-6]可能是版本获取不到：", exp,
                                      '************************************check_path_real*******')
                                d_url = 'https://api.github.com/repos/' + main_mod_name + '/contents'
                                try:
                                    page_detail = get_results(d_url, headers)
                                    result = -6
                                except Exception as exp:
                                    print("check4.[0]可能是repo名不准确：", exp,
                                          '****************************check_path_real********')
                                    page_detail = []
                                    issue = issue + '<' + 'get_go_mod:' + main_mod_name + '>'
    elif imp_siv != ('/v' + v_siv) and repo_version:
        imp_siv = ''
        # print('路径中无siv')
        # 创建路径，通过api（并非search 的api，因为无法限定版本），获取是否能读取数据
        if sub_mod_path:  # usr/repo/submod
            d_url = 'https://api.github.com/repos/' + main_mod_name + '/contents' + sub_mod_path
            d_url = d_url + '?ref=' + repo_version
            try:
                page_detail = get_results(d_url, headers)
                result = 3
            except Exception as exp:
                print("check1.[-3]可能是版本获取不到：", exp, '**********************************check_path_real*******')
                d_url = 'https://api.github.com/repos/' + main_mod_name + '/contents' + sub_mod_path
                try:
                    page_detail = get_results(d_url, headers)
                    result = -3
                except Exception as exp:
                    print('check2.[2]可能是submod为非实体：', exp, '*****************************check_path_real*******')
                    d_url = 'https://api.github.com/repos/' + main_mod_name + '/contents?ref=' + repo_version
                    try:
                        page_detail = get_results(d_url, headers)
                        result = 2
                    except Exception as exp:
                        print("check3.[-2]可能是版本获取不到：", exp,
                              '************************************check_path_real*******')
                        d_url = 'https://api.github.com/repos/' + main_mod_name + '/contents'
                        try:
                            page_detail = get_results(d_url, headers)
                            result = -2
                        except Exception as exp:
                            print("check4.[0]可能是repo名不准确：", exp,
                                  '****************************check_path_real********')
                            page_detail = []
                            issue = issue + '<' + 'get_go_mod:' + main_mod_name + '>'
        else:  # usr/repo
            d_url = 'https://api.github.com/repos/' + main_mod_name + '/contents?ref=' + repo_version
            try:
                page_detail = get_results(d_url, headers)
                result = 1
            except Exception as exp:
                print("check1.[-1]可能是版本获取不到：", exp, '************************************check_path_real******')
                d_url = 'https://api.github.com/repos/' + main_mod_name + '/contents'
                try:
                    page_detail = get_results(d_url, headers)
                    result = -1
                except Exception as exp:
                    print("check2.[0]可能是repo名不准确：", exp, '****************************check_path_real********')
                    page_detail = []
                    issue = issue + '<' + 'get_go_mod:' + main_mod_name + '>'
    else:  # 无版本号
        imp_siv = ''
        # print('路径中无siv，无版本号')
        # 创建路径，通过api（并非search 的api，因为无法限定版本），获取是否能读取数据
        if sub_mod_path:  # usr/repo/submod
            d_url = 'https://api.github.com/repos/' + main_mod_name + '/contents' + sub_mod_path
            try:
                page_detail = get_results(d_url, headers)
                result = 3
            except Exception as exp:
                print('check2.[2]可能是submod为非实体：', exp, '*****************************check_path_real*******')
                d_url = 'https://api.github.com/repos/' + main_mod_name + '/contents'
                try:
                    page_detail = get_results(d_url, headers)
                    result = 2
                except Exception as exp:
                    print("check3.[0]可能是repo名不准确：", exp,
                          '*****************************************************check_path_real********')
                    page_detail = []
                    issue = issue + '<' + 'get_go_mod:' + main_mod_name + '>'
        else:  # usr/repo
            d_url = 'https://api.github.com/repos/' + main_mod_name + '/contents'
            try:
                page_detail = get_results(d_url, headers)
                result = 1
            except Exception as exp:
                print("check2.[0]可能是repo名不准确：", exp, '****************************check_path_real********')
                page_detail = []
                issue = issue + '<' + 'get_go_mod:' + main_mod_name + '>'
    print('导入模块路径的类型为：', result)
    go_mod = 0  # 存：是否有go.mod的指标。【0无；1有但为空；2有且非空】
    go_mod_url = ''
    v_dir_url = ''
    # version_dir = 0  # 存：是否有主要子目录的指标。【0无；1有但为空；2有且非空】
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
        if v_siv_num > 1:  # 版本号>=2
            if f['name'] == ('v' + v_siv) or f['name'] == ('.' + 'v' + v_siv) and f['type'] == 'dir':
                # print('yes')
                # version_dir = 2
                v_dir_url = f['url']
                # sub_dir_result = get_results(f['url'], headers)
                # if len(sub_dir_result):
                #     # print('have sub direct')
                #     version_dir = 2
                #     go_mod = 0
                #     for sub_dir_f in sub_dir_result:
                #         # 判断有无go.mod文件
                #         if sub_dir_f['name'] == 'go.mod':
                #             # print('yes')
                #             if sub_dir_f['size'] == 0:
                #                 go_mod = 1
                #             else:
                #                 go_mod = 2
                #             go_mod_url = sub_dir_f['url']
                #         else:
                #             # print('nothing in sub direct')
                #             version_dir = 1
    return main_mod_name, sub_mod_path, imp_siv, repo_version, v_siv, result, go_mod, go_mod_url, v_dir_url, issue


# 解析go_mod文件
def check_go_mod_detail(main_mod_name, sub_mod_path, imp_siv, v_siv, go_mod_url, headers):
    # print(go_mod_url)
    go_mod_result = get_results(go_mod_url, headers)  # 获取go.mod内容
    # 解码后，使用正则表达式，获取module声明的模块路径
    go_mod_content = base64.b64decode(go_mod_result['content'])
    module = re.findall(r"^module\s*(.+?)$", go_mod_content.decode().replace('"', ''), re.M)
    print('check_go_mod_detail函数：获取module声明，', module)

    if module:
        go_mod_module = module[0].strip()  # go.mod中module声明的模块路径
    else:
        print('没有获取到，', go_mod_content.decode().replace('"', ''))
        module = go_mod_content.decode()
        go_mod_module = module.replace('module ', '').strip()
    modle_name = go_mod_module
    if re.findall(r"^k8s.com", go_mod_module):
        go_mod_module = go_mod_module.replace('k8s.com', 'github.com/kubernetes')
    if imp_siv:
        module_path = 'github.com/' + main_mod_name + sub_mod_path.replace(imp_siv, '')
        module_version_path = module_path + '/v' + v_siv
        if go_mod_module == module_version_path:
            path_match = 2  # 完全一致
        elif go_mod_module == module_path:
            path_match = 1  # 没有导入语义版本，问题3（C）
        else:
            path_match = 0  # 路径完全不一致，问题4
    else:
        if int(v_siv) >= 2:
            module_version_path = 'github.com/' + main_mod_name + sub_mod_path + '/v' + v_siv
            module_path = 'github.com/' + main_mod_name + sub_mod_path
            # print(module_version_path)
            if go_mod_module == module_version_path:
                path_match = 2  # 完全一致
            elif go_mod_module == module_path:
                path_match = 1  # 没有导入语义版本，问题3（C）
            else:
                path_match = 0  # 路径完全不一致，问题4
        else:
            module_version_path = 'github.com/' + main_mod_name + sub_mod_path
            if go_mod_module == module_version_path:
                path_match = 2  # 完全一致
            else:
                path_match = 0  # 路径完全不一致，问题4
    # version_number, path_match
    return path_match, modle_name


# 通过go.mod文件的解析路径，获取文件内容，解析出github存储库中的依赖信息，replace_c是一个判断值，输入0，不获取replace信息，1获取
def get_mod_require(go_mod_url, requires_list, headers, replace_c):
    go_mod_result = get_results(go_mod_url, headers)  # 获取go.mod内容
    # 解码后，使用正则表达式，获取module声明的模块路径
    go_mod_content = base64.b64decode(go_mod_result['content'])

    require_part = go_mod_content.decode()
    require_part = require_part.replace('"', '')
    # 匹配得到所有require语句
    mod_requires = re.findall(r"require\s*\(\n*(.+?)\n*\)", require_part, re.S)
    if mod_requires:
        require_l = re.findall(r"^[^/]*github\.com/(.+?)$", mod_requires[0], re.M)
        for require_r in require_l:
            require_r = require_r.strip()
            if require_r and (require_r not in requires_list):
                requires_list.append(require_r)
                # print('1.依赖项_1:', require_r)
        # k8s.com=github.com/kubernetes
        require_l = re.findall(r"^[^/]*k8s.com/(.+?)$", mod_requires[0], re.M)
        for require_r in require_l:
            if require_r:
                require_r = "kubernetes/" + require_r.strip()
                if require_r not in requires_list:
                    requires_list.append(require_r)
                    print('1.依赖项_k8s_1:', require_r)

    mod_requires = re.findall(r"^require\s+github\.com/(.+?)$", require_part, re.M)
    for require_r in mod_requires:
        require_r = require_r.strip()
        if require_r and (require_r not in requires_list):
            requires_list.append(require_r)
            # print('1.依赖项_2:', require_r)
    # k8s.com=github.com/kubernetes
    mod_requires = re.findall(r"^require\s+k8s\.com/(.+?)$", require_part, re.M)
    for require_r in mod_requires:
        if require_r:
            require_r = "kubernetes/" + require_r.strip()
            if require_r not in requires_list:
                requires_list.append(require_r)
                print('1.依赖项_k8s_2:', require_r)
    replaces_list = []
    if replace_c == 1:

        # 匹配得到所有replace语句
        mod_replaces = re.findall(r"replace\s*\(\n*(.+?)\n*\)", require_part, re.S)
        if mod_replaces:
            replace_l = re.findall(r"^[^/]*github\.com/(.+?)=>", mod_replaces[0], re.M)
            for replace_p in replace_l:
                replace_rl = re.findall(r"^(.+?)\s", replace_p)

                if replace_rl:
                    replace_r = replace_rl[0].strip()
                    if replace_r and (replace_r not in replaces_list):
                        replaces_list.append(replace_r)
                    # print('1.替换项_1:', replace_r)
                else:
                    replace_r = replace_p.strip()
                    if replace_r and (replace_r not in replaces_list):
                        replaces_list.append(replace_r)
                    # print('1.替换项_1:', replace_r)
            # k8s.com=github.com/kubernetes
            replace_l = re.findall(r"^[^/]*k8s\.com/(.+?)=>", mod_replaces[0], re.M)
            for replace_p in replace_l:
                replace_rl = re.findall(r"^(.+?)\s", replace_p)

                if replace_rl:
                    replace_r = "kubernetes/" + replace_rl[0].strip()
                    if replace_r and (replace_r not in replaces_list):
                        replaces_list.append(replace_r)
                    print('1.替换项_k8s_1:', replace_r)
                else:
                    replace_r = "kubernetes/" + replace_p.strip()
                    if replace_r and (replace_r not in replaces_list):
                        replaces_list.append(replace_r)
                    print('1.替换项_k8s_1:', replace_r)

        mod_replaces = re.findall(r"^replace\s+github\.com/(.+?)=>", require_part, re.M)
        for replace_r in mod_replaces:
            replace_rl = re.findall(r"^(.+?)\s", replace_r)
            if replace_rl:
                replace_r = replace_rl[0].strip()
                if replace_r and (replace_r not in replaces_list):
                    replaces_list.append(replace_r)
                # print('1.替换项_2:', replace_r)
            else:
                replace_r = replace_r.strip()
                if replace_r and (replace_r not in replaces_list):
                    replaces_list.append(replace_r)
                # print('1.替换项_2:', replace_r)
        # k8s.com=github.com/kubernetes
        mod_replaces = re.findall(r"^replace\s+k8s\.com/(.+?)=>", require_part, re.M)
        for replace_r in mod_replaces:
            if replace_r:
                replace_rl = re.findall(r"^(.+?)\s", replace_r)
                if replace_rl:
                    replace_r = "kubernetes/" + replace_rl[0].strip()
                    if replace_r and (replace_r not in replaces_list):
                        replaces_list.append(replace_r)
                    print('1.替换项_k8s_2:', replace_r)
                else:
                    replace_r = "kubernetes/" + replace_r.strip()
                    if replace_r and (replace_r not in replaces_list):
                        replaces_list.append(replace_r)
                    print('1.替换项_k8s_2:', replace_r)
        return requires_list, replaces_list
    else:
        return requires_list


def check_bug_new_repo(modname, go_mod_url, bug_type_num, bug_list, break_type_num, break_list, replace_num,
                       replace_list, headers, issue, time_w):
    if re.findall(r"^[^/]+?/[^/]+?(/.+?)$", modname):
        fullname = re.findall(r"^([^/]+?/[^/]+?)/.+?$", modname)[0]
        # sub_mod = re.findall(r"^[^/]+?/[^/]+?(/.+?)$", modname)[0]
    else:
        fullname = modname
        # sub_mod = ''
    # print(go_mod_url)
    requires_list = []
    (requires_list, replaces_list) = get_mod_require(go_mod_url, requires_list, headers, 1)

    if requires_list:
        dir_list = []
        indir_list = []
        for require in requires_list:
            if require:
                if re.findall(r"// indirect", require):
                    indir_list.append(require)
                else:
                    dir_list.append(require)
        dir_old_list = []
        dir_mod_list = []
        for require in dir_list:
            require = require.replace('// indirect', '').replace('+incompatible', '')
            # 将导入语句拆分成，模块名和版本号
            repo_n = re.findall(r"^(.+?)\s+", require)  # 无github前缀，可能有SIV，无版本号
            if repo_n:
                # imp_mod = re.findall(r"github\.com/([^/]+?/[^/]+?)/.+?", repo_git_name[0])
                repo_name = repo_n[0].strip()
                # print('2,获得repo的fullname：', repo_name)
                repo_v = re.findall(r"^.+?\s+(.+?)$", require)
                if repo_v:
                    repo_version = repo_v[0].strip()
                    print('3,分路径：', require, '-->', repo_name, '和', repo_version)
                else:
                    repo_version = ''
                    print('3,分路径：', require, '-->', repo_name, '未发现版本号')
            else:
                repo_name = require
                repo_version = ''
                print('3,分路径：', require, '-->', repo_name, '未发现版本号')
                # print('3,解析路径，并拆分：', require, '-->', repo_name, '未发现版本号')

            (main_mod_name, sub_mod_path, imp_siv, repo_version, v_siv, result, go_mod, go_mod_url, v_dir_url,
             issue) = check_path_real(repo_name, repo_version, headers, issue)
            print('###直接依赖项【', result, '】 ', main_mod_name, sub_mod_path, 'imp_siv:', imp_siv, repo_version, 'v_siv:',
                  v_siv, go_mod)
            dir_mod_list.append(main_mod_name)
            if go_mod < 2:
                # 直接依赖的旧机制
                dir_old_list.append(main_mod_name)
            time.sleep(time_w)
            l_1 = [8, 5, -8, -5]  # -8, -5
            if result in l_1:  # siv为实体路径，旧机制可以获取到
                if go_mod == 2:
                    (path_match, modle_name) = check_go_mod_detail(main_mod_name, sub_mod_path, imp_siv, v_siv,
                                                                   go_mod_url, headers)
                    if repo_name not in replaces_list:
                        if path_match != 2 and result > 0:
                            # 问题4-2，D，已经发生
                            break_type_num[3] = break_type_num[3] + 1
                            break_list[3] = break_list[3] + '$' + repo_name + ' ' + repo_version
                            print('[8,5]问题4-2', repo_name + ' ' + repo_version)
                        elif path_match != 2 and result < 0:
                            # 问题4-1，D，升级预警
                            (r, issue) = get_local_use(fullname, modle_name, '4-1', time_w, issue)
                            if r == 0:
                                bug_type_num[7] = bug_type_num[7] + 1
                                bug_list[7] = bug_list[7] + '$' + repo_name + ' ' + repo_version + '~'
                                print('[8,5]问题4-1', repo_name + ' ' + repo_version)
                    else:
                        # 问题4，D，通过replace替换
                        replace_num[3] = replace_num[3] + 1
                        replace_list[3] = replace_list[3] + '$' + repo_name + ' ' + repo_version
                        print('[8,5]问题4-replace', repo_name + ' ' + repo_version)
                        # if path_match != 2:

                else:
                    issue = issue + '导入路径出错' + repo_name + ' ' + repo_version
                    print('[8,5]导入路径出错' + repo_name + ' ' + repo_version)
            l_2 = [7, 6, 4, -7, -6, -4]  # , -7, -6, -4
            if result in l_2:
                # 问题1-0，A，下游预警
                bug_1_0_type = '1.0'
                bug_type_num[0] = bug_type_num[0] + 1
                bug_list[0] = bug_list[0] + '$' + bug_1_0_type + ':' + repo_name + ' ' + repo_version
                print('[7]问题1-0', repo_name + ' ' + repo_version)

                if go_mod == 2:
                    (path_match, modle_name) = check_go_mod_detail(main_mod_name, sub_mod_path, imp_siv, v_siv,
                                                                   go_mod_url, headers)
                    if path_match == 1 and result > 0:
                        if repo_name not in replaces_list:
                            # 问题3-2，C，已经发生
                            break_type_num[2] = break_type_num[2] + 1
                            break_list[2] = break_list[2] + '$' + repo_name + ' ' + repo_version
                            print('[7]问题3-2', repo_name + ' ' + repo_version)
                        else:
                            # 问题3，C，通过replace替换
                            replace_num[2] = replace_num[2] + 1
                            replace_list[2] = replace_list[2] + '$' + repo_name + ' ' + repo_version
                            print('[7]问题3-replace', repo_name + ' ' + repo_version)

                    elif path_match == 0 and result > 0:
                        if repo_name not in replaces_list:
                            # 问题4-2，D，已经发生
                            break_type_num[3] = break_type_num[3] + 1
                            break_list[3] = break_list[3] + '$' + repo_name + ' ' + repo_version
                            print('[7]问题4-2', repo_name + ' ' + repo_version)
                        else:
                            # 问题4，D，通过replace替换
                            replace_num[3] = replace_num[3] + 1
                            replace_list[3] = replace_list[3] + '$' + repo_name + ' ' + repo_version
                            print('[7]问题4-replace', repo_name + ' ' + repo_version)

                    elif path_match == 1 and result < 0:
                        if repo_name not in replaces_list:
                            # 问题3-1，C，升级预警
                            (r, issue) = get_local_use(fullname, modle_name, '3-1', time_w, issue)
                            if r == 0:
                                bug_type_num[5] = bug_type_num[5] + 1
                                bug_list[5] = bug_list[5] + '$' + repo_name + ' ' + repo_version + '~'
                                print('[7]问题3-1', repo_name + ' ' + repo_version)
                        else:
                            # 问题3，C，通过replace替换
                            replace_num[2] = replace_num[2] + 1
                            replace_list[2] = replace_list[2] + '$' + repo_name + ' ' + repo_version
                            print('[7]问题3-replace', repo_name + ' ' + repo_version)
                    elif path_match == 0 and result < 0:
                        if repo_name not in replaces_list:
                            # 问题4-1，D，升级预警
                            (r, issue) = get_local_use(fullname, modle_name, '4-1', time_w, issue)
                            if r == 0:
                                bug_type_num[7] = bug_type_num[7] + 1
                                bug_list[7] = bug_list[7] + '$' + repo_name + ' ' + repo_version + '~'
                                print('[7]问题4-1', repo_name + ' ' + repo_version)
                        else:
                            # 问题4，D，通过replace替换
                            replace_num[3] = replace_num[3] + 1
                            replace_list[3] = replace_list[3] + '$' + repo_name + ' ' + repo_version
                            print('[7]问题4-replace', repo_name + ' ' + repo_version)

                else:
                    issue = issue + '导入路径出错' + repo_name + ' ' + repo_version
                    print('[7]导入路径出错' + repo_name + ' ' + repo_version)

            l_3 = [3, 2, 1, -3, -2]  # -3, -2, -1
            if result in l_3:

                if go_mod == 2:
                    (path_match, modle_name) = check_go_mod_detail(main_mod_name, sub_mod_path, imp_siv, v_siv,
                                                                   go_mod_url, headers)
                    if v_dir_url:
                        version_dir = 2
                    else:
                        version_dir = 0
                    require_type = judge_repo_type(go_mod, int(v_siv), path_match, version_dir)

                    if result > 0:
                        if require_type == 2:
                            if repo_name not in replaces_list:
                                # 问题2-2，B，已经发生
                                break_type_num[1] = break_type_num[1] + 1
                                break_list[1] = break_list[1] + '$' + repo_name + ' ' + repo_version
                                print('[3]问题2-1', repo_name + ' ' + repo_version)
                            else:
                                # 问题2，B，通过replace替换
                                replace_num[1] = replace_num[1] + 1
                                replace_list[1] = replace_list[1] + '$' + repo_name + ' ' + repo_version
                                print('[3]问题2-replace', repo_name + ' ' + repo_version)

                        elif require_type == 4:
                            if repo_name not in replaces_list:
                                # 问题3-2，C，已经发生
                                break_type_num[2] = break_type_num[2] + 1
                                break_list[2] = break_list[2] + '$' + repo_name + ' ' + repo_version
                                print('[3]问题3-2', repo_name + ' ' + repo_version)
                            else:
                                # 问题3，C，通过replace替换
                                replace_num[2] = replace_num[2] + 1
                                replace_list[2] = replace_list[2] + '$' + repo_name + ' ' + repo_version
                                print('[3]问题3-replace', repo_name + ' ' + repo_version)

                        elif require_type == 10 and result != 2:
                            if repo_name not in replaces_list:
                                # 问题4-2，D，已经发生
                                break_type_num[3] = break_type_num[3] + 1
                                break_list[3] = break_list[3] + '$' + repo_name + ' ' + repo_version
                                print('[3]问题4-2', repo_name + ' ' + repo_version)
                            else:
                                # 问题4，D，通过replace替换
                                replace_num[3] = replace_num[3] + 1
                                replace_list[3] = replace_list[3] + '$' + repo_name + ' ' + repo_version
                                print('[3]问题4-replace', repo_name + ' ' + repo_version)

                        elif path_match == 0 and result == 2:
                            issue = issue + '导入路径出错' + repo_name + ' ' + repo_version
                            print('[3]导入路径出错' + repo_name + ' ' + repo_version)
                    else:

                        if require_type == 2:
                            if repo_name in replaces_list:
                                # 问题2，B，通过replace替换
                                replace_num[1] = replace_num[1] + 1
                                replace_list[1] = replace_list[1] + '$' + repo_name + ' ' + repo_version
                                print('[3]问题2-replace', repo_name + ' ' + repo_version)

                        elif require_type == 4:
                            if repo_name in replaces_list:
                                # 问题3，C，通过replace替换
                                replace_num[2] = replace_num[2] + 1
                                replace_list[2] = replace_list[2] + '$' + repo_name + ' ' + repo_version
                                print('[3]问题3-replace', repo_name + ' ' + repo_version)

                        elif require_type == 10 and result != 2:
                            if repo_name in replaces_list:
                                # 问题4，D，通过replace替换
                                replace_num[3] = replace_num[3] + 1
                                replace_list[3] = replace_list[3] + '$' + repo_name + ' ' + repo_version
                                print('[3]问题4-replace', repo_name + ' ' + repo_version)

                        elif path_match == 0 and result == 2:
                            issue = issue + '导入路径出错' + repo_name + ' ' + repo_version
                            print('[3]导入路径出错' + repo_name + ' ' + repo_version)

                elif go_mod != 2 and result != 1:
                    issue = issue + '导入路径出错' + repo_name + ' ' + repo_version
                    print('[3]导入路径出错' + repo_name + ' ' + repo_version)
        for require in indir_list:
            # 间接依赖会发生问题的地方
            indir_bug_type_num = [0, 0, 0, 0, 0, 0, 0, 0]  # 没有问题，默认为0
            indir_bug_list = ['', '', '', '', '', '', '', '']
            # 间接依赖已经发生问题的地方
            indir_break_type_num = [0, 0, 0, 0]
            indir_break_list = ['', '', '', '']
            # 间接依赖替换列表
            indir_replace_num = [0, 0, 0, 0]
            indir_replace_list = ['', '', '', '']
            indir_issue = 0
            require = require.replace('// indirect', '').replace('+incompatible', '')
            # 将导入语句拆分成，模块名和版本号
            repo_n = re.findall(r"^(.+?)\s+", require)  # 无github前缀，可能有SIV，无版本号
            if repo_n:
                # imp_mod = re.findall(r"github\.com/([^/]+?/[^/]+?)/.+?", repo_git_name[0])
                repo_name = repo_n[0].strip()
                # print('2,获得repo的fullname：', repo_name)
                repo_v = re.findall(r"^.+?\s+(.+?)$", require)
                if repo_v:
                    repo_version = repo_v[0].strip()
                    print('3,分路径：', require, '-->', repo_name, '和', repo_version)
                else:
                    repo_version = ''
                    print('3,分路径：', require, '-->', repo_name, '未发现版本号')
            else:
                repo_name = require
                repo_version = ''
                print('3,分路径：', require, '-->', repo_name, '未发现版本号')
                # print('3,解析路径，并拆分：', require, '-->', repo_name, '未发现版本号')

            (main_mod_name, sub_mod_path, imp_siv, repo_version, v_siv, result, go_mod, go_mod_url, v_dir_url,
             issue) = check_path_real(repo_name, repo_version, headers, issue)
            print('###间接依赖项【', result, '】 ', main_mod_name, sub_mod_path, 'imp_siv:', imp_siv, repo_version, 'v_siv:',
                  v_siv, go_mod)
            time.sleep(time_w)
            l_1 = [8, 5, -8, -5]  # -8, -5
            if result in l_1:  # siv为实体路径，旧机制可以获取到
                if go_mod == 2:
                    (path_match, modle_name) = check_go_mod_detail(main_mod_name, sub_mod_path, imp_siv, v_siv,
                                                                   go_mod_url, headers)
                    if repo_name not in replaces_list:
                        if path_match != 2 and result > 0:
                            # 问题4-2，D，已经发生
                            indir_break_type_num[3] = indir_break_type_num[3] + 1
                            indir_break_list[3] = indir_break_list[3] + '$' + repo_name + ' ' + repo_version
                            print('[8,5]问题4-2', repo_name + ' ' + repo_version)
                            indir_issue = indir_issue + 1
                        elif path_match != 2 and result < 0:
                            # 问题4-1，D，升级预警
                            indir_bug_type_num[7] = indir_bug_type_num[7] + 1
                            indir_bug_list[7] = indir_bug_list[7] + '$' + repo_name + ' ' + repo_version + '~'
                            print('[8,5]问题4-1', repo_name + ' ' + repo_version)
                            indir_issue = indir_issue + 1

                    else:
                        # 问题4，D，通过replace替换
                        indir_replace_num[3] = indir_replace_num[3] + 1
                        indir_replace_list[3] = indir_replace_list[3] + '$' + repo_name + ' ' + repo_version
                        print('[8,5]问题4-replace', repo_name + ' ' + repo_version)
                        # if path_match != 2:
                        indir_issue = indir_issue + 1

                else:
                    issue = issue + '导入路径出错' + repo_name + ' ' + repo_version
                    print('[8,5]导入路径出错' + repo_name + ' ' + repo_version)
            l_2 = [7, 6, 4, -7, -6, -4]  # , -7, -6, -4
            if result in l_2:
                if go_mod == 2:
                    (path_match, modle_name) = check_go_mod_detail(main_mod_name, sub_mod_path, imp_siv, v_siv,
                                                                   go_mod_url, headers)
                    if path_match == 1 and result > 0:
                        if repo_name not in replaces_list:
                            # 问题3-2，C，已经发生
                            indir_break_type_num[2] = indir_break_type_num[2] + 1
                            indir_break_list[2] = indir_break_list[2] + '$' + repo_name + ' ' + repo_version
                            print('[7]问题3-2', repo_name + ' ' + repo_version)
                            indir_issue = indir_issue + 1
                        else:
                            # 问题3，C，通过replace替换
                            indir_replace_num[2] = indir_replace_num[2] + 1
                            indir_replace_list[2] = indir_replace_list[2] + '$' + repo_name + ' ' + repo_version
                            print('[7]问题3-replace', repo_name + ' ' + repo_version)
                            indir_issue = indir_issue + 1

                    elif path_match == 0 and result > 0:
                        if repo_name not in replaces_list:
                            # 问题4-2，D，已经发生
                            indir_break_type_num[3] = indir_break_type_num[3] + 1
                            indir_break_list[3] = indir_break_list[3] + '$' + repo_name + ' ' + repo_version
                            print('[7]问题4-2', repo_name + ' ' + repo_version)
                            indir_issue = indir_issue + 1
                        else:
                            # 问题4，D，通过replace替换
                            indir_replace_num[3] = indir_replace_num[3] + 1
                            indir_replace_list[3] = indir_replace_list[3] + '$' + repo_name + ' ' + repo_version
                            print('[7]问题4-replace', repo_name + ' ' + repo_version)
                            indir_issue = indir_issue + 1

                    elif path_match == 1 and result < 0:
                        if repo_name not in replaces_list:
                            # 问题3-1，C，升级预警
                            indir_bug_type_num[5] = indir_bug_type_num[5] + 1
                            indir_bug_list[5] = indir_bug_list[5] + '$' + repo_name + ' ' + repo_version + '~'
                            print('[7]问题3-1', repo_name + ' ' + repo_version)
                            indir_issue = indir_issue + 1
                        else:
                            # 问题3，C，通过replace替换
                            indir_replace_num[2] = indir_replace_num[2] + 1
                            indir_replace_list[2] = indir_replace_list[2] + '$' + repo_name + ' ' + repo_version
                            print('[7]问题3-replace', repo_name + ' ' + repo_version)
                            indir_issue = indir_issue + 1
                    elif path_match == 0 and result < 0:
                        if repo_name not in replaces_list:
                            # 问题4-1，D，升级预警
                            indir_bug_type_num[7] = indir_bug_type_num[7] + 1
                            indir_bug_list[7] = indir_bug_list[7] + '$' + repo_name + ' ' + repo_version + '~'
                            print('[7]问题4-1', repo_name + ' ' + repo_version)
                            indir_issue = indir_issue + 1
                        else:
                            # 问题4，D，通过replace替换
                            indir_replace_num[3] = indir_replace_num[3] + 1
                            indir_replace_list[3] = indir_replace_list[3] + '$' + repo_name + ' ' + repo_version
                            print('[7]问题4-replace', repo_name + ' ' + repo_version)
                            indir_issue = indir_issue + 1

                else:
                    issue = issue + '导入路径出错' + repo_name + ' ' + repo_version
                    print('[7]导入路径出错' + repo_name + ' ' + repo_version)

            l_3 = [3, 2, 1, -3, -2]  # -3, -2, -1
            if result in l_3:

                if go_mod == 2:
                    (path_match, modle_name) = check_go_mod_detail(main_mod_name, sub_mod_path, imp_siv, v_siv,
                                                                   go_mod_url, headers)
                    if v_dir_url:
                        version_dir = 2
                    else:
                        version_dir = 0
                    require_type = judge_repo_type(go_mod, int(v_siv), path_match, version_dir)

                    if result > 0:
                        if require_type == 2:
                            if repo_name not in replaces_list:
                                # 问题2-2，B，已经发生
                                indir_break_type_num[1] = indir_break_type_num[1] + 1
                                indir_break_list[1] = indir_break_list[1] + '$' + repo_name + ' ' + repo_version
                                print('[3]问题2-1', repo_name + ' ' + repo_version)
                                indir_issue = indir_issue + 1
                            else:
                                # 问题2，B，通过replace替换
                                indir_replace_num[1] = indir_replace_num[1] + 1
                                indir_replace_list[1] = indir_replace_list[1] + '$' + repo_name + ' ' + repo_version
                                print('[3]问题2-replace', repo_name + ' ' + repo_version)
                                indir_issue = indir_issue + 1

                        elif require_type == 4:
                            if repo_name not in replaces_list:
                                # 问题3-2，C，已经发生
                                indir_break_type_num[2] = indir_break_type_num[2] + 1
                                indir_break_list[2] = indir_break_list[2] + '$' + repo_name + ' ' + repo_version
                                print('[3]问题3-2', repo_name + ' ' + repo_version)
                                indir_issue = indir_issue + 1
                            else:
                                # 问题3，C，通过replace替换
                                indir_replace_num[2] = indir_replace_num[2] + 1
                                indir_replace_list[2] = indir_replace_list[2] + '$' + repo_name + ' ' + repo_version
                                print('[3]问题3-replace', repo_name + ' ' + repo_version)
                                indir_issue = indir_issue + 1

                        elif require_type == 10 and result != 2:
                            if repo_name not in replaces_list:
                                # 问题4-2，D，已经发生
                                indir_break_type_num[3] = indir_break_type_num[3] + 1
                                indir_break_list[3] = indir_break_list[3] + '$' + repo_name + ' ' + repo_version
                                print('[3]问题4-2', repo_name + ' ' + repo_version)
                                indir_issue = indir_issue + 1
                            else:
                                # 问题4，D，通过replace替换
                                indir_replace_num[3] = indir_replace_num[3] + 1
                                indir_replace_list[3] = indir_replace_list[3] + '$' + repo_name + ' ' + repo_version
                                print('[3]问题4-replace', repo_name + ' ' + repo_version)
                                indir_issue = indir_issue + 1

                        elif path_match == 0 and result == 2:
                            issue = issue + '导入路径出错' + repo_name + ' ' + repo_version
                            print('[3]导入路径出错' + repo_name + ' ' + repo_version)
                    else:

                        if require_type == 2:
                            if repo_name not in replaces_list:
                                # 问题2-1，B，升级预警
                                # u_repo = fullname, d_repo = repo_fullname
                                indir_bug_type_num[3] = indir_bug_type_num[3] + 1
                                indir_bug_list[3] = indir_bug_list[3] + '$' + repo_name + ' ' + repo_version + '~'
                                print('[3]问题2-1', repo_name + ' ' + repo_version)
                                indir_issue = indir_issue + 1
                            else:
                                # 问题2，B，通过replace替换
                                indir_replace_num[1] = indir_replace_num[1] + 1
                                indir_replace_list[1] = indir_replace_list[1] + '$' + repo_name + ' ' + repo_version
                                print('[3]问题2-replace', repo_name + ' ' + repo_version)
                                indir_issue = indir_issue + 1
                        elif require_type == 4:
                            if repo_name not in replaces_list:
                                # 问题3-1，C，升级预警
                                indir_bug_type_num[5] = indir_bug_type_num[5] + 1
                                indir_bug_list[5] = indir_bug_list[5] + '$' + repo_name + ' ' + repo_version + '~'
                                print('[3]问题3-1', repo_name + ' ' + repo_version)
                                indir_issue = indir_issue + 1
                            else:
                                # 问题3，C，通过replace替换
                                indir_replace_num[2] = indir_replace_num[2] + 1
                                indir_replace_list[2] = indir_replace_list[2] + '$' + repo_name + ' ' + repo_version
                                print('[3]问题3-replace', repo_name + ' ' + repo_version)
                                indir_issue = indir_issue + 1

                        elif require_type == 10 and result != 2:
                            if repo_name not in replaces_list:
                                # 问题4-1，D，升级预警
                                indir_bug_type_num[7] = indir_bug_type_num[7] + 1
                                indir_bug_list[7] = indir_bug_list[7] + '$' + repo_name + ' ' + repo_version + '~'
                                print('[3]问题4-1', repo_name + ' ' + repo_version)
                                indir_issue = indir_issue + 1
                            else:
                                # 问题4，D，通过replace替换
                                indir_replace_num[3] = indir_replace_num[3] + 1
                                indir_replace_list[3] = indir_replace_list[3] + '$' + repo_name + ' ' + repo_version
                                print('[3]问题4-replace', repo_name + ' ' + repo_version)
                                indir_issue = indir_issue + 1

                        elif path_match == 0 and result == 2:
                            issue = issue + '导入路径出错' + repo_name + ' ' + repo_version
                            print('[3]导入路径出错' + repo_name + ' ' + repo_version)

                elif go_mod != 2 and result != 1:
                    issue = issue + '导入路径出错' + repo_name + ' ' + repo_version
                    print('[3]导入路径出错' + repo_name + ' ' + repo_version)

            if (result in l_3) and result > 0:
                (n_r_v_name, n_r_semantic, issue) = get_releases_url(repo_name, headers, issue)
                (main_mod_name, sub_mod_path, imp_siv, repo_version, v_siv, result, go_mod, go_mod_url, v_dir_url,
                 issue) = check_path_real(repo_name, n_r_v_name, headers, issue)
                print('###间接依赖项的新版本【', result, '】 ', main_mod_name, sub_mod_path, 'imp_siv:', imp_siv, repo_version,
                      'v_siv:', v_siv, go_mod)
                if go_mod == 2:
                    (path_match, modle_name) = check_go_mod_detail(main_mod_name, sub_mod_path, imp_siv, v_siv,
                                                                   go_mod_url, headers)
                    if v_dir_url:
                        version_dir = 2
                    else:
                        version_dir = 0
                    require_type = judge_repo_type(go_mod, int(v_siv), path_match, version_dir)
                    print('是模块：', path_match, modle_name, require_type)

                    if require_type == 2:
                        if repo_name not in replaces_list:
                            # 问题2-1，B，升级预警
                            # u_repo = fullname, d_repo = repo_fullname
                            indir_bug_type_num[3] = indir_bug_type_num[3] + 1
                            indir_bug_list[3] = indir_bug_list[3] + '$' + repo_name + ' ' + repo_version + '~'
                            print('[3]问题2-1', repo_name + ' ' + repo_version)
                            indir_issue = indir_issue + 1
                        else:
                            # 问题2，B，通过replace替换
                            indir_replace_num[1] = indir_replace_num[1] + 1
                            indir_replace_list[1] = indir_replace_list[1] + '$' + repo_name + ' ' + repo_version
                            print('[3]问题2-replace', repo_name + ' ' + repo_version)
                            indir_issue = indir_issue + 1

                    elif require_type == 4:
                        if repo_name not in replaces_list:
                            # 问题3-1，C，升级预警
                            indir_bug_type_num[5] = indir_bug_type_num[5] + 1
                            indir_bug_list[5] = indir_bug_list[5] + '$' + repo_name + ' ' + repo_version + '~'
                            print('[3]问题3-1', repo_name + ' ' + repo_version)
                            indir_issue = indir_issue + 1
                        else:
                            # 问题3，C，通过replace替换
                            indir_replace_num[2] = indir_replace_num[2] + 1
                            indir_replace_list[2] = indir_replace_list[2] + '$' + repo_name + ' ' + repo_version
                            print('[3]问题3-replace', repo_name + ' ' + repo_version)
                            indir_issue = indir_issue + 1

                    elif require_type == 10 and result != 2:
                        if repo_name not in replaces_list:
                            # 问题4-1，D，升级预警
                            indir_bug_type_num[7] = indir_bug_type_num[7] + 1
                            indir_bug_list[7] = indir_bug_list[7] + '$' + repo_name + ' ' + repo_version + '~'
                            print('[3]问题4-1', repo_name + ' ' + repo_version)
                            indir_issue = indir_issue + 1
                        else:
                            # 问题4，D，通过replace替换
                            indir_replace_num[3] = indir_replace_num[3] + 1
                            indir_replace_list[3] = indir_replace_list[3] + '$' + repo_name + ' ' + repo_version
                            print('[3]问题4-replace', repo_name + ' ' + repo_version)
                            indir_issue = indir_issue + 1

            if indir_issue > 0:
                print('间接依赖项有问题，找上游')
                # 间接依赖存在问题， 找上游：
                up_repo_str = ''
                for modle_name in dir_mod_list:
                    (r, issue) = new_indir_use(modle_name, main_mod_name, time_w, issue)
                    if r > 0:
                        up_repo_str = up_repo_str + modle_name + ' '
                print('依赖项的上游：', up_repo_str)
                for i in range(0, 8):
                    if indir_bug_type_num[i] > 0:
                        bug_type_num[i] = bug_type_num[i] + indir_bug_type_num[i]
                        bug_list[i] = bug_list[i] + indir_bug_list[i] + '[' + up_repo_str + ']'
                for i in range(0, 4):
                    if indir_break_type_num[i] > 0:
                        break_type_num[i] = break_type_num[i] + indir_break_type_num[i]
                        break_list[i] = break_list[i] + indir_break_list[i] + '[' + up_repo_str + ']'
                    if indir_replace_num[i] > 0:
                        replace_num[i] = replace_num[i] + indir_replace_num[i]
                        replace_list[i] = replace_list[i] + indir_replace_list[i] + '[' + up_repo_str + ']'


            # # 未来更新时会发生的bug，检测该包的最新版本
            # if result == -1 or result == 1:  # and (repo_name not in replaces_list)
            #     (r, issue) = get_local_use(fullname, repo_name, 'check-new', time_w, issue)
            #     if r == 0 and re.findall(r"^kubernetes/", repo_name):
            #         repo_name = repo_name.replace('kubernetes/', 'k8s.com/')
            #         (r, issue) = get_local_use(fullname, repo_name, 'check-new', time_w, issue)
            #     if r == 0:
            #         (r_v_name_new, r_semantic_new, issue) = get_releases_url(main_mod_name, headers, issue)
            #         if r_v_name_new == '' or r_v_name_new == 'master':
            #             r_v_name_new = ''
            #         (main_mod_name, sub_mod_path, imp_siv, r_v_name_new, v_siv, result, go_mod, go_mod_url,
            #          v_dir_url, issue) = check_path_real(repo_name, r_v_name_new, headers, issue)
            #         if go_mod == 2:
            #             (path_match, mod_name) = check_go_mod_detail(main_mod_name, sub_mod_path, imp_siv, v_siv,
            #                                                          go_mod_url, headers)
            #             if int(v_siv) >= 2 and path_match == 2:
            #                 if repo_name not in replaces_list:
            #                     # 问题2-1，B，升级预警
            #                     bug_type_num[3] = bug_type_num[3] + 1
            #                     bug_list[3] = bug_list[3] + '$' + repo_name + ' ' + repo_version + '~'
            #                     print('[1]问题2-1', repo_name + ' ' + repo_version)
            #                 elif imp_indir == 1:
            #                     # 问题2，B，通过replace替换
            #                     replace_num[1] = replace_num[1] + 1
            #                     replace_list[1] = replace_list[1] + '$' + repo_name + ' ' + repo_version
            #                     print('[1]问题2-replace', repo_name + ' ' + repo_version)
            #                     ins_replace = ins_replace + 1
            #
            #             elif int(v_siv) >= 2 and path_match == 1:
            #                 if repo_name not in replaces_list:
            #                     # 问题3-1，C，升级预警
            #                     bug_type_num[5] = bug_type_num[5] + 1
            #                     bug_list[5] = bug_list[5] + '$' + repo_name + ' ' + repo_version + '~'
            #                     print('[1]问题3-1', repo_name + ' ' + repo_version)
            #                 else:
            #                     # 问题3，C，通过replace替换
            #                     replace_num[2] = replace_num[2] + 1
            #                     replace_list[2] = replace_list[2] + '$' + repo_name + ' ' + repo_version
            #                     print('[1]问题3-replace', repo_name + ' ' + repo_version)
            #                     ins_replace = ins_replace + 1
            #
            #             elif path_match == 0:
            #                 if repo_name not in replaces_list:
            #                     # 问题4-1，D，升级预警
            #                     bug_type_num[7] = bug_type_num[7] + 1
            #                     bug_list[7] = bug_list[7] + '$' + repo_name + ' ' + repo_version + '~'
            #                     print('[1]问题4-1', repo_name + ' ' + repo_version)
            #                 else:
            #                     # 问题4，D，通过replace替换
            #                     replace_num[3] = replace_num[3] + 1
            #                     replace_list[3] = replace_list[3] + '$' + repo_name + ' ' + repo_version
            #                     print('[1]问题4-replace', repo_name + ' ' + repo_version)
            #                     ins_replace = ins_replace + 1
            # if result in l_3 and ins_replace == 0 and imp_indir == 1:
            #     # 问题2，B，通过replace替换
            #     replace_num[1] = replace_num[1] + 1
            #     replace_list[1] = replace_list[1] + '$' + repo_name + ' ' + repo_version
            #     print('[3]问题2-replace', repo_name + ' ' + repo_version)
            # else:
            #     # 非github存储库的，记录一下，可能存在其他问题
            #     if bug_1_0:
            #         bug_list[0] = bug_list[0] + '$' + '-1.1' + ':' + require_record
            # time.sleep(0.5)
    else:
        print('【go.mod文件无依赖项】****************no requires！****************************[mark:fine]')
    return bug_type_num, bug_list, break_type_num, break_list, replace_num, replace_list, issue


# 输入repo名，以获得下游信息
def new_indir_use(reponame, upname, time_w, issue):
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    # 查询数据库是否有
    # (check_result, down_list) = check_down_repo(repo_name, check_time)
    # url = 'https://api.github.com/' + reponame + '/search/code?q=' + upname + \
    #       '+extension:go&page=1&per_page=10'
    url = 'https://api.github.com/search/code?q="' + upname + \
          '"+repo:' + reponame + '&page=1&per_page=10'
    print(url)
    try:
        results = get_results(url, headers)
        # print(results)
        items = results['items']
        if items:
            c = 0  # 计数器
            r = 0
            for i in items:
                # i_filename = i['name']  # 存：文件名字
                i_path = i['path']  # 存：文件相对路径
                i_repo = i['repository']
                i_reponame = i_repo['full_name']
                i_fileurl = i['git_url']
                c = c + 1
                # print('【bug', b_type, '】', 'local requires ', c, ': ', i_reponame, i_path)
            if c:
                return c, issue
            else:
                return 0, issue
        else:
            return 0, issue
    except Exception as exp:
        print("get search repo local use(new_indir_use) error", exp)
        issue = issue + '<' + 'new_indir_use:' + reponame + '~' + upname + '>'
        return -1, issue


# 获取详情页的：go.mod文件【是否有，module声明】，版本号，子文件夹/vN，module声明的路径是否符合模块机制的要求
def get_detail_page(fullname, name, semantic, headers, stars, forks, update, host, user, password, db_name, check_date,
                    insert_error, check_error, update_error, insert_success, update_success, issue_l, time_w):
    # 未来会发生问题的地方
    bug_type_num = [0, 0, 0, 0, 0, 0, 0, 0]  # 没有问题，默认为0
    bug_list = ['', '', '', '', '', '', '', '']
    # 已经发生问题的地方
    break_type_num = [0, 0, 0, 0]
    break_list = ['', '', '', '']

    # replaces_list 是go.mod文件中replace语句替换的repos，replace_list是这些替换曾经有问题的bug记录表
    issue = ''
    # 获取本项目的go.mod文件的情况
    # (go_mod, main_version, go_mod_url, version_dir, issue) = get_go_mod(fullname, name, semantic, headers,
    #                                                                     issue)
    (go_mod_module, version_number, path_match, go_mod, main_version, go_mod_url, version_dir,
     issue) = get_go_mod_detail(fullname, name, semantic, headers, issue)
    r_type = judge_repo_type(go_mod, version_number, path_match, version_dir)
    check_local_self = 0
    if r_type == 4:
        # 问题3-0，C，下游新用户升级预警
        bug_type_num[4] = bug_type_num[4] + 1
        bug_list[4] = bug_list[4] + '$' + fullname + ' ' + name
    elif r_type == 10:

        # 问题4-0，D，下游新用户升级预警
        bug_type_num[6] = bug_type_num[6] + 1
        bug_list[6] = bug_list[6] + '$' + fullname + ' ' + name
        # print(go_mod_module)
        if version_number >= 2:
            module_siv = re.findall(r"/v" + str(version_number) + "$", go_mod_module)
            if not module_siv:
                # 问题3-0，C，下游新用户升级预警
                bug_type_num[4] = bug_type_num[4] + 1
                bug_list[4] = bug_list[4] + '$' + fullname + ' ' + name
            else:
                check_local_self = 1
    if r_type == 2 or check_local_self == 1:
        # 检测该项目是否存在自身调用，因为如果本项目是分支法创建的v>=2的，且本地有调用自己的代码则会出现影响下游的情况。
        (r, issue) = get_local_use(fullname, go_mod_module, 'check_self_use:1-0', time_w, issue)
        if r > 0:
            # 问题1-0，A，下游预警
            bug_1_0_type = '1.0'
            bug_type_num[0] = bug_type_num[0] + 1
            bug_list[0] = bug_list[0] + '$' + bug_1_0_type + ':' + fullname + ' ' + name
            print('[*]问题1-0', fullname + ' ' + name, ' 参数：', r_type, check_local_self)

    # print('*新机制*')
    if go_mod == 2:  # 如果有非空的go.mod文件，说明是新机制
        # 通过replace替换的地方
        replace_num = [0, 0, 0, 0]
        replace_list = ['', '', '', '']
        (bug_type_num, bug_list, break_type_num, break_list, replace_num, replace_list,
         issue) = check_bug_new_repo(fullname, go_mod_url, bug_type_num, bug_list, break_type_num, break_list,
                                     replace_num, replace_list, headers, issue, time_w)

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

        if insert:
            (check_error, insert_error,
             insert_success) = insert_info(time_num, fullname, stars, forks, update, name, bug_type_num, bug_list,
                                           break_type_num, break_list, impact, host, user, password, db_name,
                                           check_date, check_error, insert_error, insert_success)
        if replace:
            (check_error, insert_error, update_error, insert_success,
             update_success) = insert_replace(time_num, fullname, name, replace_num, replace_list, host, user, password,
                                              db_name, check_error, insert_error, update_error, insert_success,
                                              update_success)
        (insert_error, update_error, check_error, insert_success,
         update_success) = insert_impact(time_num, fullname, update, name, bug_type_num, break_type_num, impact, host,
                                         user, password, db_name, insert_error, update_error, check_error,
                                         insert_success, update_success)

    else:
        if go_mod == 1:
            print('【go.mod文件为空文件】**************************************************************[mark:middle]')
        else:
            # 遍历获取import导包语句
            print('本项目为非模块机制，需要从源文件中读取导包路径')
    if issue:
        issue_l = issue_l + '【' + fullname + ':' + issue + '】'
    return insert_error, check_error, update_error, insert_success, update_success, issue_l


# 插入数据库的方法
def insert_info(time_num, fullname, stars, forks, update, name, bug_type, bug_list, break_type, break_list, impact,
                host, user, password, db_name, check_date, check_error, insert_error, insert_success):
    # 查重
    check_result = 0
    # check_result = check_record(check_date, fullname, update, impact, host, user, password, db_name)
    if check_result == 0:
        insert_sql = "INSERT INTO github_go_repos_findbug (id,checkdate,full_name,star,fork,update_time, v_name, " \
                     "num1_0,list1_0,num2_1,list2_1,break2,break_list2,num3_1,list3_1,break3,break_list3,num4_1," \
                     "list4_1,break4,break_list4,old_impact,new_impact,repo_type) VALUES ('%d','%d','%s','%d'," \
                     "'%d','%s','%s','%d','%s','%d','%s','%d','%s','%d','%s','%d','%s','%d','%s','%d','%s'," \
                     "'%d','%d','%d')" % (time_num, check_date, fullname, stars, forks, update, name, bug_type[0],
                                          bug_list[0], bug_type[3], bug_list[3], break_type[1], break_list[1],
                                          bug_type[5], bug_list[5], break_type[2], break_list[2], bug_type[7],
                                          bug_list[7], break_type[3], break_list[3], impact[0], impact[1], 1)
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
            print('insert github_go_repos_findbug error exception is:', exp, '----------------------------------------'
                                                                             '---------------------')
            print('insert github_go_repos_findbug error sql:', insert_sql)
            insert_error = insert_error + 1
            # 发生错误时回滚
            db.rollback()
        db.close()
    elif check_result == 1:
        print('already insert')
    else:
        print('check github_go_repos_findbug error', fullname, '---------------------------------------------------'
                                                               '----------')
        check_error = check_error + 1
    return check_error, insert_error, insert_success


# 查重
def check_record(check_date, fullname, update, impact, host, user, password, db_name):
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT id FROM github_go_repos_findbug WHERE (checkdate='%d' AND full_name='%s' AND update_time='%s' AND " \
          "old_impact='%d' AND new_impact='%d')" % (check_date, fullname, update, impact[0], impact[1])
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            print('查重结果，有：', check_result)
            return 1
        else:
            return 0
    except Exception as exp:
        print("check github_go_repos_findbug error:", exp, '-----------------------------------------------------'
                                                           '--------')
        return -1


# 更新数据库表repo_impact
def insert_replace(time_num, fullname, v_name, replace_num, replace_list, host, user, password, db_name, check_error,
                   insert_error, update_error, insert_success, update_success):
    for i in range(0, 4):
        if len(replace_list[i]) > 400:
            replace_list[i] = replace_list[i][0:400]
    # 查重
    (result_id, result_list) = check_replace(fullname, v_name, host, user, password, db_name)

    if result_id <= 0:
        insert_sql = "INSERT INTO replace_bug_repo (id,full_name,v_name,replace1,list1,replace2,list2,replace3,list3," \
                     "replace4,list4) VALUES ('%d','%s','%s','%d','%s','%d','%s','%d','%s'," \
                     "'%d','%s')" % (time_num, fullname, v_name, replace_num[0], replace_list[0], replace_num[1],
                                     replace_list[1], replace_num[2], replace_list[2], replace_num[3], replace_list[3])
        db = pymysql.connect(host, user, password, db_name)
        try:
            insert_cursor = db.cursor()
            # 执行sql语句
            insert_cursor.execute(insert_sql)
            db.commit()
            insert_cursor.close()
            print('insert replace_bug_repo successful', fullname)
            insert_success = insert_success + 1
        except Exception as exp:
            print('insert replace_bug_repo error exception is:', exp, '-------------------------------------------'
                                                                      '------------------')
            print('insert replace_bug_repo error sql:', insert_sql)
            insert_error = insert_error + 1
            # 发生错误时回滚
            db.rollback()
        db.close()
    elif result_id > 0:
        need_update = 0
        for i in range(0, 4):
            if result_list[i] != replace_list[i]:
                need_update = need_update + 1
        # print('already insert at replace_bug_repo')
        # update_time,v_name,o_bug,n_bug,old_impact,new_impact,gomod
        # print(type(result_list[2]), type(result_list[4]))
        if need_update > 0:
            # repo_impact (id,full_name,update_time,old_impact,new_impact)new_impact
            update_sql = "UPDATE replace_bug_repo SET id='%d',replace1='%d',list1='%s',replace2='%d',list2='%s'," \
                         "replace3='%d',list3='%s',replace4='%d',list4='%s' " \
                         "WHERE id='%d'" % (time_num, replace_num[0], replace_list[0], replace_num[1], replace_list[1],
                                            replace_num[2], replace_list[2], replace_num[3], replace_list[3], result_id)
            db = pymysql.connect(host, user, password, db_name)
            try:
                update_cursor = db.cursor()
                # 执行sql语句
                update_cursor.execute(update_sql)
                db.commit()
                update_cursor.close()
                print('update replace_bug_repo successful', fullname, '@', v_name)
                update_success = update_success + 1
            except Exception as exp:
                print('update replace_bug_repo error exception is:', exp)
                print('update replace_bug_repo error sql:', update_sql)
                update_error = update_error + 1
                # 发生错误时回滚
                db.rollback()
            db.close()

    else:
        print('check repo_impact error', fullname, '@', v_name, '-----------------------------------------------------')
        check_error = check_error + 1
    return check_error, insert_error, update_error, insert_success, update_success


# 查重: 数据库表repo_impact
def check_replace(fullname, v_name, host, user, password, db_name):
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT id,list1,list2,list3,list4 " \
          "FROM replace_bug_repo WHERE full_name='%s' AND v_name='%s'" % (fullname, v_name)
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            print('replace_bug_repo：', check_result)
            result_id = check_result[0][0]
            result_list = [check_result[0][1], check_result[0][2], check_result[0][3], check_result[0][4]]
            return result_id, result_list
        else:
            return 0, []
    except Exception as exp:
        print("check repo_impact error --", fullname, '@', v_name, ':', exp, '------------------------------------'
                                                                             '-------------------------')
        return -1, []


# 更新数据库表repo_impact
def insert_impact(time_num, fullname, update, name, bug_type, break_type, impact, host, user, password, db_name,
                  insert_error, update_error, check_error, insert_success, update_success):
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
                                                                                       impact[1], 1)
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
            print('insert repo_impact error exception is:', exp, '-------------------------------------------------'
                                                                 '------------')
            print('insert repo_impact error sql:', insert_sql)
            insert_error = insert_error + 1
            # 发生错误时回滚
            db.rollback()
        db.close()
    elif check_result == 1:
        print('already insert at repo_impact')
        # update_time,v_name,o_bug,n_bug,old_impact,new_impact,gomod
        # print(type(result_list[2]), type(result_list[4]))
        if result_list[2] != o_bug or result_list[3] != n_bug or result_list[4] != impact[0] \
                or result_list[5] != impact[1] or result_list[6] != 1:
            before_bug = result_list[2] + '&' + result_list[3]
            now_bug = o_bug + '&' + n_bug
            impact_change = [time_num, fullname, result_list[0], result_list[1], update, name, before_bug, now_bug,
                             result_list[4], result_list[5], impact[0], impact[1], result_list[6], 1]
            (insert_error, insert_success) = insert_impact_change(impact_change, host, user, password, db_name,
                                                                  insert_error, insert_success)
        # repo_impact (id,full_name,update_time,old_impact,new_impact)new_impact
        update_sql = "UPDATE repo_impact SET id='%d',update_time='%s',v_name='%s',o_bug='%s',n_bug='%s'," \
                     "old_impact='%d',new_impact='%d',gomod='%d' WHERE full_name='%s'" % (time_num, update, name,
                                                                                          o_bug, n_bug, impact[0],
                                                                                          impact[1], 1, fullname)
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
            print('update repo_impact error exception is:', exp)
            print('update repo_impact error sql:', update_sql)
            update_error = update_error + 1
            # 发生错误时回滚
            db.rollback()
        db.close()
    else:
        print('check repo_impact error', fullname, '-------------------------------------------------------------')
        check_error = check_error + 1
    return insert_error, update_error, check_error, insert_success, update_success


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
        print("check repo_impact error:", exp, '-------------------------------------------------------------')
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
        print('insert repo_impact_change error exception is:', exp, '-----------------------------------------------'
                                                                    '--------------')
        print('insert repo_impact_change error sql:', insert_sql)
        insert_error = insert_error + 1
        # 发生错误时回滚
        db.rollback()
    db.close()
    return insert_error, insert_success


def update_new_bug(new_fullname, check_date, host, user, password, db_name, insert_e, search_e, check_e,
                   update_e, insert_s, update_s, issue, time_w):
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    (stars, forks, update, v_name, semantic, issue) = get_repo_detail(new_fullname, headers, issue)
    (insert_e, check_e, update_e, insert_s, update_s,
     issue) = get_detail_page(new_fullname, v_name, semantic, headers, stars, forks, update, host, user, password,
                              db_name, check_date, insert_e, check_e, update_e, insert_s, update_s, issue, time_w)
    return insert_e, search_e, check_e, update_e, insert_s, update_s, issue


def main():
    user = 'root'
    host = '47.254.86.255'
    password = 'Ella1996'
    db_name = 'githubspider'
    insert_e = 0
    search_e = 0
    check_e = 0
    update_e = 0
    insert_s = 0
    update_s = 0
    issue_l = ''
    time_w = 0.8
    time_s = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    # headers = {'User-Agent': 'Mozilla/5.0',
    #            'Content-Type': 'application/json',
    #            'Accept': 'application/json',
    #            'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    # fullname = 'google/go-cloud'
    # fullname_list = ['google/go-cloud', 'restic/restic', 'vitessio/vitess', 'hashicorp/consul', 'rclone/rclone',
    #                  'minio/minio', 'hashicorp/terraform', 'fabiolb/fabio', 'wtfutil/wtf', 'rancher/rancher',
    #                  'future-architect/vuls', 'hashicorp/vault', 'go-kit/kit', 'ory/hydra', 'kubernetes/minikube',
    #                  'GoogleContainerTools/skaffold', 'istio/istio', 'ethereum/go-ethereum', 'prometheus/prometheus',
    #                  'gin-gonic/gin', 'kubernetes/dashboard']
    fullname_list = ['flynn/flynn']
    for fullname in fullname_list:
        check_date = int(time.strftime('%Y%m%d', time.localtime(time.time())))
        (insert_e, search_e, check_e, update_e, insert_s, update_s,
         issue_l) = update_new_bug(fullname, check_date, host, user, password, db_name, insert_e, search_e, check_e,
                                   update_e, insert_s, update_s, issue_l, time_w)

    # (stars, forks, update, v_name, semantic) = get_repo_detail(fullname, headers)
    # get_detail_page(fullname, v_name, semantic, headers, stars, forks, update)
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
