import json
import os
import random
import re
import shutil
import time
from urllib.request import Request, urlopen
import requests
from bs4 import BeautifulSoup
import pymysql
# from download import DOWNLOAD
# from download import PATH
# import repoDep
from .download import DOWNLOAD
from .download import PATH
from . import repoDep


# get result through url [public-method]
def get_results(url, headers):
    request = Request(url, headers=headers)
    response = urlopen(request).read()
    result = json.loads(response.decode())
    return result


def get_repo_insert_db():
    return 'repo'


def get_db_search():
    host = '47.254.86.255'
    user = 'root'
    password = 'Ella1996'
    db_name = 'githubspider'
    return host, user, password, db_name


def get_db_insert():
    host = '47.254.86.255'
    user = 'root'
    password = 'Ella1996'
    db_name = 'hero-tool'
    return host, user, password, db_name


def get_tool_name_list():
    tool_name_list = ['Godeps.json', 'vendor.conf', 'vendor.json', 'glide.toml', 'Gopkg.toml', 'Godep.json']
    return tool_name_list


def get_tool_name_list_2():
    tool_name_list = ['glide.lock', 'Gopkg.lock']
    return tool_name_list


# get random headers [public-method]
def get_headers():
    # headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0',
    #            'Content-Type': 'application/json', 'Accept': 'application/json'}
    # token 0a6cca72aa3cc98993950500c87831bfef7e5707
    # token ad418c5441a67ad8b2c95188e131876c6a1187fe [end]
    # token abdd967d350662632381f130cd62268ed2f961a1 [end]
    # token ff4e63b2dba8febac0aeb59aa3b8829a05de97e7 [hu]
    # token a41ca9587818fc355b015376e814df47223fc136 [me]
    index_num = random.randint(0, 2)
    headers_1 = {'User-Agent': 'Mozilla/5.0',
                 'Content-Type': 'application/json', 'Accept': 'application/json',
                 'Authorization': 'token a41ca9587818fc355b015376e814df47223fc136'}
    headers_2 = {'User-Agent': 'Mozilla/5.0',
                 'Content-Type': 'application/json', 'Accept': 'application/json',
                 'Authorization': 'token ff4e63b2dba8febac0aeb59aa3b8829a05de97e7'}
    headers_3 = {'User-Agent': 'Mozilla/5.0',
                 'Content-Type': 'application/json', 'Accept': 'application/json',
                 'Authorization': 'token 0a6cca72aa3cc98993950500c87831bfef7e5707'}
    headers_list = [headers_1, headers_2, headers_3]
    return headers_list[index_num]


def get_last_version(fullname):
    headers = get_headers()
    repo_name_list = fullname.split('/')
    repo_name = repo_name_list[0] + '/' + repo_name_list[1]
    subdir_name = ''
    c = 0
    for n in repo_name_list:
        c = c + 1
        if c > 2:
            subdir_name = subdir_name + '/' + n
    if subdir_name:
        print('1.:', repo_name, subdir_name, '************************************get_releases_url*******')
        d_url = 'https://api.github.com/repos/' + repo_name
    else:
        d_url = 'https://api.github.com/repos/' + fullname
    try:
        one_page_results = get_results(d_url, headers)
        releases_url = one_page_results['releases_url']
        (v_name, semantic) = get_version(releases_url)
    except Exception as exp:
        print("************** get search releases_url error", exp, '*******************************************')
        v_name = 'master'
        semantic = False
    return v_name, semantic


def get_version(releases_url):
    headers = get_headers()
    v_url = releases_url.replace('{/id}', '')
    version_result = get_results(v_url, headers)
    # v_id = ''
    v_name = ''
    semantic = True
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
    return v_name, semantic


def get_last_hash(repo_name):
    repo_name_list = repo_name.split('/')
    fullname = repo_name_list[0] + '/' + repo_name_list[1]
    # https://api.github.com/repos/robfig/cron/commits
    url = 'https://api.github.com/repos/' + fullname + '/commits'
    headers = get_headers()
    try:
        commts = get_results(url, headers)
        last_commt = commts[0]["sha"][0:7]
        print('%%%%get the last commit hash is:', last_commt, fullname)
    except Exception as exp:
        last_commt = ''
        print("************** get search releases_url error", exp, '*******************************************')
    return last_commt


# check repo exit or not : 0 can find; 1 repo name wrong; 2 repo version wrong [public-method]
def check_insert_mes(in_repo_name, in_version):
    insert_error = 0
    repo_exit = check_repo_version_exit_web(in_repo_name, in_version)
    print('check_repo_version_exit_web: ', repo_exit)
    if repo_exit == 0 or repo_exit < 0:
        repo_url = 'https://api.github.com/repos/' + in_repo_name + '/contents?ref=' + in_version
        print(repo_url)
        headers = get_headers()
        try:
            insert_error = 0
            page_detail = get_results(repo_url, headers)
        except Exception as exp:

            print("Maybe cannot find version: ", exp, '**************************************************')
            repo_url = 'https://api.github.com/repos/' + in_repo_name
            try:
                page_detail = get_results(repo_url, headers)
                insert_error = 2
                print(in_repo_name, insert_error, 'The repo version name is not correct!')
            except Exception as exp:
                insert_error = 1
                print(in_repo_name, insert_error, 'The repo name is not correct:', exp, '*****************************'
                                                                                        '*********************')
    else:
        insert_error = 0
    print('check_insert_mes', insert_error)
    return insert_error


def check_repo_exit_web(repo_name):
    url = 'https://github.com/' + repo_name.replace('github.com/', '').strip()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0'
    }
    try:
        response = requests.get(url, headers=headers)
        content = response.content.decode('utf-8')
        soup = BeautifulSoup(content, "lxml")
        str_all = str(soup)
        # f6 link-gray text-mono ml-2 d-none d-lg-inline
        # main = str(soup.find('body'))
        div_msg = str_all.strip('').replace('\n', '')
        # print(div_msg)
        error_str = re.findall(r"https://github.githubassets.com/_error.js", div_msg)
        notfound_str = re.findall(r"Not Found", div_msg)
        # print(hash_str)
        if error_str or notfound_str:
            repo_exit = -1
        else:
            repo_exit = 1
    except Exception as exp:
        repo_exit = 0
        print("get repo error:", exp, "**************************************************")
    return repo_exit


def check_repo_version_exit_web(repo_name, repo_version):
    url = 'https://github.com/' + repo_name.replace('github.com/', '').strip() + '/tree/' + repo_version.strip()
    print(url)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0'
    }
    try:
        response = requests.get(url, headers=headers)
        content = response.content.decode('utf-8')
        soup = BeautifulSoup(content, "lxml")
        # f6 link-gray text-mono ml-2 d-none d-lg-inline
        # main = str(soup.find('body'))
        main = str(soup)
        div_msg = main.strip('').replace('\n', '')
        # print(div_msg)
        hash_str = re.findall(r"https://github.githubassets.com/_error.js", div_msg)
        notfound_str = re.findall(r"Not Found", div_msg)
        # print(hash_str)
        if hash_str or notfound_str:
            repo_exit = -1
        else:
            repo_exit = check_repo_exit_web(repo_name)
            if repo_exit == 1:
                repo_exit = -2
            elif repo_exit == -1:
                repo_exit = -1
    except Exception as exp:
        repo_exit = 0
        print("get repo error:", exp, "**************************************************")
    return repo_exit


# check repo exit or not : 0 can find; -1 repo name wrong; -2 repo version wrong [public-method]
def check_repo_exit(repo_name):
    # print('check_repo_exit', repo_name, type(repo_name))
    repo_name = repo_name.replace('github.com/', '')
    repo_name = repo_name.strip()
    repo_exit = check_repo_exit_web(repo_name)
    if repo_exit == 0:
        repo_url = 'https://api.github.com/repos/' + repo_name
        headers = get_headers()
        try:
            repo_exit = 1
            page_detail = get_results(repo_url, headers)
            if 'message' in page_detail:
                if page_detail['message'] == 'Not Found':
                    repo_exit = -1
        except Exception as exp:
            repo_exit = -1
            print("The repo name is not correct: ", exp, '**************************************************')
    return repo_exit


# get page detail through repo_name and repo_version [public-method]
def get_page_detail(repo_name, repo_version, search_e):
    repo_url = 'https://api.github.com/repos/' + repo_name + '/contents?ref=' + repo_version
    headers = get_headers()
    try:
        page_detail = get_results(repo_url, headers)
    except Exception as exp:
        print("get search error ", repo_name, ' : ', exp)
        time.sleep(2)
        try:
            page_detail = get_results(repo_url, headers)
        except Exception as exp:
            page_detail = ''
            print("get search error ", repo_name, ' : ', exp)
            search_e = search_e + 1
    return page_detail, search_e


# get dependency manager  [public-method][need update, can only get the latest condition]
def get_dm_msg(repo_name, headers, search_e):
    mod_count = -1
    tool_count = -1
    mod_url_list = []
    tool_url_list = []
    # get go.mod count num
    url_mod = 'https://api.github.com/search/code?q=repo:' + repo_name + '+filename:go.mod'
    print(url_mod)
    try:
        results_mod = get_results(url_mod, headers)
        mod_count = results_mod['total_count']
        if mod_count > 30:
            for page in range(1, 11):
                url_mod = url_mod + '&page=' + str(page) + '&per_page=100'
                print(url_mod)
                results_mod = get_results(url_mod, headers)
                items = results_mod['items']
                if items:
                    vendor = 0  # check vendor counter
                    not_go_mod = 0
                    for i in items:
                        mod_path = i['path']
                        file_name = i['name']
                        mod_path = mod_path.replace(file_name, '')
                        if file_name != 'go.mod':
                            not_go_mod = not_go_mod + 1
                        elif re.findall(r"vendor/", mod_path) or re.findall(r"/vendor/", mod_path):
                            vendor = vendor + 1
                        else:
                            # /xx/xx/
                            mod_url_list.append('/' + mod_path)
                    mod_count = mod_count - vendor - not_go_mod
                else:
                    break
        else:
            items = results_mod['items']
            if items:
                vendor = 0  # check vendor counter
                not_go_mod = 0
                for i in items:
                    mod_path = i['path']
                    file_name = i['name']
                    mod_path = mod_path.replace(file_name, '')
                    if file_name != 'go.mod':
                        not_go_mod = not_go_mod + 1
                    elif re.findall(r"vendor/", mod_path) or re.findall(r"/vendor/", mod_path):
                        vendor = vendor + 1
                    else:
                        mod_url_list.append('/' + mod_path)  # /xx/xx/
                mod_count = mod_count - vendor - not_go_mod
            else:
                mod_count = 0
    except Exception as exp:
        print("Get go.mod count failed: ", exp, '**************************************************')
        search_e = search_e + 1
    # get third party dependency manager count num
    # for now can recognise these files  [@@need add more@@]
    tool_name_list = get_tool_name_list()
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
                    vendor = 0  # check vendor counter
                    not_tool = 0
                    for i in items:
                        tool_path = i['path']
                        file_name = i['name']
                        tool_path = tool_path.replace(file_name, '')
                        if file_name not in tool_name_list:
                            not_tool = not_tool + 1
                        elif re.findall(r"vendor/", tool_path) or re.findall(r"/vendor/", tool_path):
                            vendor = vendor + 1
                        else:
                            tool_url_list.append('/' + tool_path)  # /xx/xx/
                    tool_count = tool_count - vendor - not_tool
                else:
                    break
        else:
            items = results_tool['items']
            if items:
                vendor = 0  # check vendor counter
                not_tool = 0
                for i in items:
                    tool_path = i['path']
                    file_name = i['name']
                    tool_path = tool_path.replace(file_name, '')
                    if file_name not in tool_name_list:
                        not_tool = not_tool + 1
                    elif re.findall(r"vendor/", tool_path) or re.findall(r"/vendor/", tool_path):
                        vendor = vendor + 1
                    else:
                        tool_url_list.append('/' + tool_path)  # /xx/xx/
                tool_count = tool_count - vendor - not_tool
            else:
                tool_count = 0
    except Exception as exp:
        print("Get tool count failed", exp, '***********************************************')
        search_e = search_e + 1
    if mod_url_list:
        mod_url_list.sort(key=lambda m: len(m), reverse=False)
    if tool_url_list:
        tool_url_list.sort(key=lambda t: len(t), reverse=False)

    return mod_count, mod_url_list, tool_count, tool_url_list, search_e


# get the redirected repo name
def get_redirect_repo(old_repo):
    # repo_name_update
    check_db_name = 'repo_name_update'
    (host, user, password, db_name) = get_db_search()
    sql = "SELECT now_repo_name FROM " + check_db_name + " WHERE now_repo_name!='0' and old_repo_name='%s'" % old_repo
    db_check = pymysql.connect(host, user, password, db_name)
    try:
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            return check_result[0][0]
        else:
            return ''
    except Exception as exp:
        print("get redirected repo name from ", check_db_name, " error",
              exp, '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
        return ''


# get the new web url
def get_new_url(old_url):
    # new_web_name
    check_db_name = 'new_web_name'
    (host, user, password, db_name) = get_db_search()
    sql = "SELECT now_url FROM " + check_db_name + " WHERE old_url='%s' or " \
                                                   "old_url='%s'" % (old_url, 'github.com/' + old_url)
    db_check = pymysql.connect(host, user, password, db_name)
    try:
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            return check_result[0][0]
        else:
            return ''
    except Exception as exp:
        print("get new url from ", check_db_name, " error",
              exp, '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
        return ''


# insert into new_web_name
def insert_new_url(old_url, now_url, insert_e, insert_s):
    # new_web_name
    insert_db_name = 'new_web_name'
    (host, user, password, db_name) = get_db_search()
    sql = "INSERT INTO " + insert_db_name + " (old_url,now_url) VALUES ('%s','%s')" % (old_url, now_url)
    db = pymysql.connect(host, user, password, db_name)
    try:
        insert_cursor = db.cursor()
        insert_cursor.execute(sql)
        db.commit()
        insert_cursor.close()
        print('insert ', sql, ' successful', old_url, now_url)
        insert_s = insert_s + 1
    except Exception as exp:
        print('insert ', sql, ' error exception is:', exp)
        print('insert ', sql, ' error sql:', sql)
        insert_e = insert_e + 1
        db.rollback()
    db.close()
    return insert_e, insert_s


# get hash through version
def get_hash(url, search_e):
    v_hash = ''
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0'
    }
    try:
        response = requests.get(url, headers=headers)
        content = response.content.decode('utf-8')
        soup = BeautifulSoup(content, "lxml")
        # f6 link-gray text-mono ml-2 d-none d-lg-inline
        div_msg = str(soup.find('a', class_='f6 link-gray text-mono ml-2 d-none d-lg-inline'))
        div_msg = div_msg.strip('').replace('\n', '')
        # print(div_msg)
        hash_str = re.findall(r">([0-9a-zA-Z]+?)</a>", div_msg)
        # print(hash_str)
        if hash_str:
            v_hash = hash_str[0]
    except Exception as exp:
        search_e = search_e + 1
        print("get hash error:", exp, "**************************************************")
    return v_hash, search_e


# deal local repo
def deal_local_repo(root_url, local_url, go_list, mod_list, tool_list, vendor_list):
    tool_list_1 = []
    tool_list_2 = []
    dir_list = []
    tool_name_list = get_tool_name_list()
    tool_name_list_2 = get_tool_name_list_2()
    local_list = os.listdir(local_url)
    for f in local_list:
        n_path = os.path.join(local_url, f)
        n_r_path = n_path.replace(root_url, '')
        # print(n_r_path)
        if os.path.isdir(n_path) and f == 'vendor':
            vendor_list.append(n_r_path)
            # print(n_r_path)
            vendor_dir_list = os.listdir(n_path)
            for v in vendor_dir_list:
                v_path = os.path.join(n_path, v)
                v_r_path = v_path.replace(root_url, '')
                # print(v_r_path)
                if os.path.isfile(v_path) and v in tool_name_list:
                    tool_list.append(v_r_path)
                # elif os.path.isdir(v_path):
                #     shutil.rmtree(v_path)
                # elif os.path.isfile(v_path):
                #     os.remove(v_path)
        elif os.path.isdir(n_path):  # go file
            # print(n_path)
            if n_path not in dir_list:
                dir_list.append(n_path)
        elif os.path.isfile(n_path) and re.findall(r"\.go$", f):  # go file
            if n_r_path not in go_list:
                go_list.append(n_r_path)
            # print(n_r_path)
        elif os.path.isfile(n_path) and f == 'go.mod':  # go.mod
            print(n_path)
            # if not n_r_path.replace('go.mod', '').strip():
            #     mod_list.append('/')
            # else:
            mod_path = n_r_path.replace('go.mod', '').strip()
            if mod_path not in mod_list:
                mod_list.append(mod_path)
        elif os.path.isfile(n_path) and f in tool_name_list:  # tool
            # print(n_r_path)
            if n_r_path not in tool_list_1:
                tool_list_1.append(n_r_path)
        elif os.path.isfile(n_path) and f in tool_name_list_2:  # tool 2
            # print(n_r_path)
            if n_r_path not in tool_list_2:
                tool_list_2.append(n_r_path)
    if (not tool_list_1) and tool_list_2:
        for t in tool_list_2:
            tool_list.append(t)
    for p in dir_list:
        (go_list, mod_list, tool_list, vendor_list) = deal_local_repo(root_url, p, go_list, mod_list, tool_list,
                                                                      vendor_list)
    return go_list, mod_list, tool_list, vendor_list


def get_mod_require(mod_url, requires_list, replaces_list):
    print('go.mod:', mod_url)
    f = open(mod_url)
    go_mod_content = f.read()
    require_part = go_mod_content.replace('"', '')
    f.close()
    # get all require
    mod_requires = re.findall(r"require\s*\(\n*(.+?)\n*\)", require_part, re.S)
    if mod_requires:
        require_l = mod_requires[0].split('\n')
        for require_r in require_l:
            require_r = require_r.strip().replace('+incompatible', '')
            # (not re.findall(r"^[0-9a-zA-Z]+?/[0-9a-zA-Z]+?$", require_r))
            #                 and (not re.findall(r"^[0-9a-zA-Z]+?$", require_r)) and
            if require_r and (not re.findall(r"^//.+?", require_r)) and (require_r not in requires_list):
                requires_list.append(require_r)
                # print(require_r)
    mod_requires = re.findall(r"^require\s+([^(]+?)$", require_part, re.M)
    for require_r in mod_requires:
        require_r = require_r.strip().replace('+incompatible', '')
        if require_r and (require_r not in requires_list):
            requires_list.append(require_r)
            # print(require_r)
    # get all replace
    mod_replaces = re.findall(r"replace\s*\(\n*(.+?)\n*\)", require_part, re.S)
    if mod_replaces:
        replace_l = mod_requires[0].split('\n')
        for replace_p in replace_l:
            replace_p = replace_p.strip().replace('+incompatible', '')
            if replace_p and (not re.findall(r"^//.+?", replace_p)):
                replace_rl = re.findall(r"^(.+?)\s", replace_p)
                replace_rr = re.findall(r"=>\s(.+?)$", replace_p)
                if replace_rl and replace_rr and ([replace_rl[0], replace_rr[0]] not in replaces_list):
                    replaces_list.append([replace_rl[0], replace_rr[0]])
                    for r in requires_list:
                        if re.findall(r"^" + replace_rl[0] + r"\s", r):
                            requires_list.remove(r)
                            replace_rr_ind = replace_rr[0] + ' +replace'
                            if (replace_rr[0] not in requires_list) and (replace_rr_ind not in requires_list):
                                requires_list.append(replace_rr_ind)  # +replace
                                print(replace_rr_ind + ' +replace')
    mod_replaces = re.findall(r"^replace\s+([^(]+?)$", require_part, re.M)
    for replace_r in mod_replaces:
        replace_r = replace_r.strip()
        if replace_r:
            replace_rl = re.findall(r"^(.+?)\s", replace_r)
            replace_rr = re.findall(r"=>\s(.+?)$", replace_r)
            if replace_rl and replace_rr and ([replace_rl[0], replace_rr[0]] not in replaces_list):
                replaces_list.append([replace_rl[0], replace_rr[0]])
                for r in requires_list:
                    if re.findall(r"^" + replace_rl[0] + r"\s", r):
                        requires_list.remove(r)
                        replace_rr_ind = replace_rr[0] + ' +replace'
                        if (replace_rr[0] not in requires_list) and (replace_rr_ind not in requires_list):
                            requires_list.append(replace_rr_ind)  # +replace
                            print(replace_rr_ind + ' +replace')
    return requires_list, replaces_list


def get_requires_from_file(file_url, import_list):
    f = open(file_url)
    file_content = f.read()
    file_import = re.findall(r"import\s*\(\n(.+?)\n\)", file_content, re.S)
    # print(file_import)
    f.close()
    if file_import:
        i_list = file_import[0].split('\n')
        for imp in i_list:
            imp = imp.strip()
            # print(imp)
            # (not re.findall(r"^[0-9a-zA-Z]+?/[0-9a-zA-Z]+?$", require_r))
            #                 and (not re.findall(r"^[0-9a-zA-Z]+?$", require_r)) and
            if (not re.findall(r"^//.+?", imp)) and (not re.findall(r"\"[0-9a-zA-Z]+?/[0-9a-zA-Z]+?\"", imp)) and \
                    (not re.findall(r"\"[0-9a-zA-Z]+?\"", imp)):
                if re.findall(r"\"(.+?)\"", imp):
                    import_path = re.findall(r"\"(.+?)\"", imp)[0].strip()
                    # print(import_path)
                    if import_path not in import_list:
                        import_list.append(import_path)
                        # print(import_path)
    return import_list


def get_github_name_db(spec_name):
    (host, user, password, db_name) = get_db_search()
    sql = "SELECT old_url FROM new_web_name WHERE now_url='%s'" % spec_name
    db_check = pymysql.connect(host, user, password, db_name)
    try:
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


def get_github_name(dep_name):
    siv_path = ''
    git_mod_name = ''
    if re.findall(r"(/v\d+?)$", dep_name):
        siv_path = re.findall(r"(/v\d+?)$", dep_name)[0]
    elif re.findall(r"(\.v\d+?)$", dep_name):
        siv_path = re.findall(r"(\.v\d+?)$", dep_name)[0]
    (r, git_name) = get_github_name_db(dep_name.replace(siv_path, ''))
    if git_name:
        git_mod_name = git_name + siv_path.replace('.', '/')
    else:
        insert_new_spec_db(dep_name.replace(siv_path, ''))

    return git_mod_name


def return_repo_name(dep_name):  # make xxx/xxxx/xxx  ->  xxx/xxx
    if re.findall(r"^([^/]+?/[^/]+?)$", dep_name):
        repo_name = dep_name
    elif re.findall(r"^([^/]+?/[^/]+?)/", dep_name):
        repo_name = re.findall(r"^([^/]+?/[^/]+?)/", dep_name)[0]
    else:
        repo_name = ''
    return repo_name


def get_repo_name(dep_name):
    # repo_name = ''
    if re.findall(r"go.etcd.io/", dep_name):
        dep_name = dep_name.replace('go.etcd.io/', 'etcd-io/')
        repo_name = return_repo_name(dep_name)
    elif re.findall(r"golang.org/x/", dep_name):
        dep_name = dep_name.replace('golang.org/x/', 'golang/')
        repo_name = return_repo_name(dep_name)
    elif re.findall(r"^github\.com/", dep_name):
        dep_name = dep_name.strip()
        repo_name = return_repo_name(dep_name)
    elif re.findall(r"^gopkg.in/([^/]+?/[^/]+?)\.v\d", dep_name):
        repo_name = re.findall(r"^gopkg.in/([^/]+?/[^/]+?)\.v\d", dep_name)[0]
    else:
        # gopkg.in/alecthomas/gometalinter.v2   golang.org/x/sync
        if re.findall(r"^(gopkg.in/.+?)\.v\d", dep_name):
            # gopkg.in/cheggaaa/pb.v1
            repo_name = re.findall(r"^(gopkg.in/.+?)\.v\d", dep_name)[0]
        else:
            if re.findall(r"^([^/]+?/[^/]+?)$", dep_name):
                repo_name = re.findall(r"^([^/]+?/[^/]+?)$", dep_name)[0]
            elif re.findall(r"^([^/]+?/[^/]+?)/", dep_name):
                repo_name = re.findall(r"^([^/]+?/[^/]+?)/", dep_name)[0]
            else:
                repo_name = dep_name
            git_name = get_github_name(repo_name)
            if not git_name:
                if re.findall(r"^([^/]+?/[^/]+?/[^/]+?)$", dep_name):
                    repo_name = re.findall(r"^([^/]+?/[^/]+?/[^/]+?)$", dep_name)[0]
                elif re.findall(r"^([^/]+?/[^/]+?/[^/]+?)/", dep_name):
                    repo_name = re.findall(r"^([^/]+?/[^/]+?/[^/]+?)/", dep_name)[0]
                git_name = get_github_name(repo_name)
                if git_name:
                    repo_name = git_name
                else:
                    if re.findall(r"^([^/]+?/[^/]+?)$", dep_name):
                        repo_name = re.findall(r"^([^/]+?/[^/]+?)$", dep_name)[0]
                    elif re.findall(r"^([^/]+?/[^/]+?)/", dep_name):
                        repo_name = re.findall(r"^([^/]+?/[^/]+?)/", dep_name)[0]
                    else:
                        repo_name = ''
                    if repo_name:
                        insert_error = check_repo_exit(repo_name)
                        if insert_error != 1:
                            repo_name = ''
                        else:
                            repo_name = dep_name
            else:
                repo_name = git_name
        repo_name = repo_name.replace('github.com/', '')
    return repo_name


def deal_repo_name_version(dep_name, dep_version):
    # if dep_name.strip() == 'go.etcd.io/bbolt':
    #     dep_name = 'etcd-io/bbolt'
    repo_name_n = ''
    repo_name = get_repo_name(dep_name)
    # ** consider def mecthod **
    insert_error = 1
    if repo_name:
        repo_version = deal_dep_version(dep_version)
        r = check_insert_mes(repo_name, repo_version)
        if r == 2 and repo_version:
            print('**get the latest version**')
            last_commit = get_last_hash(repo_name)
            if last_commit:
                insert_error = 0
                repo_version = last_commit
                # r = check_insert_mes(repo_name, last_commit)
                # if r == 0:
                #
                #     insert_error = 0
                # else:
                #     insert_error = -2
            else:
                insert_error = 2
        elif r == 1:
            insert_error = 1
        else:
            insert_error = 0
        if insert_error == 1:
            (r, now_name) = check_is_redirected(repo_name)
            if now_name:
                insert_error = 0
                repo_name_n = repo_name
                repo_name = now_name
                r = check_insert_mes(repo_name, repo_version)
                if r == 2 and repo_version:
                    print('**get the latest version**')
                    last_commit = get_last_hash(repo_name)
                    if last_commit:
                        repo_version = last_commit
                        insert_error = 0
                        # r = check_insert_mes(repo_name, last_commit)
                        # if r == 0:
                        #
                        # else:
                        #     insert_error = -2
                    else:
                        insert_error = 2
            else:
                insert_error = 1
        print('after deal: ', repo_name, repo_version)
    else:
        repo_version = ''
    return insert_error, repo_name, repo_version, repo_name_n


def check_is_redirected(dep):
    repo_name = dep.replace('github.com/', '')
    repo_name_list = repo_name.split('/')
    if len(repo_name_list) >= 2:
        fullname = repo_name_list[0] + '/' + repo_name_list[1]
    else:
        fullname = repo_name
    (host, user, password, db_name) = get_db_search()
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


def check_new_spec_db(spec_name):
    (host, user, password, db_name) = get_db_insert()
    sql = "SELECT count(*) FROM new_spec_db WHERE spec_name='%s'" % spec_name
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        return check_result[0][0]
    except Exception as exp:
        print("check new_spec_db error:", exp, '-------------------------------------------------------------')
        return -1


def insert_new_spec_db(spec_name):
    (host, user, password, db_name) = get_db_insert()
    r = check_new_spec_db(spec_name)
    if r <= 0:
        sql = "INSERT INTO new_spec_db (spec_name, github_repo) VALUES ('%s','%s')" % (spec_name, '-')
        db = pymysql.connect(host, user, password, db_name)
        try:
            insert_cursor = db.cursor()
            insert_cursor.execute(sql)
            db.commit()
            insert_cursor.close()
            print('insert new_spec_db successful', spec_name)
        except Exception as exp:
            print('insert new_spec_db error exception is:', exp)
            print('insert new_spec_db error sql:', sql)
            db.rollback()
        db.close()


def get_git_repo_name(dep):
    repo_name = ''
    if re.findall(r"^github\.com/([^/]+?/[^/]+?)$", dep):
        repo_name = re.findall(r"^github\.com/([^/]+?/[^/]+?)$", dep)[0]
    elif re.findall(r"^github\.com/([^/]+?/[^/]+?)/", dep):
        repo_name = re.findall(r"^github\.com/([^/]+?/[^/]+?)/", dep)[0]
    return repo_name


def deal_dep_version(dep_version):
    dep_version = dep_version.replace('// indirect', '').replace('+incompatible', '').strip()
    not_semantic = re.findall(r"^v\d+?\.\d+?\.\d+?-*[^-]*?-[0-9.]+?-([A-Za-z0-9]+?)$", dep_version)
    not_semantic_2 = re.findall(r"^v\d+?\.\d+?\.\d+?-.+?-([A-Za-z0-9]+?)$", dep_version)
    # bug_main_version = ''
    if not_semantic:
        repo_version = not_semantic[0][0:7]
    else:
        if not_semantic_2:
            repo_version = not_semantic_2[0][0:7]
        else:
            repo_version = dep_version
    return repo_version


class Repo:
    # repo_name, stars, v_name, v_siv, v_hash, mod_num, mod_siv,mod_name, mod_url, tool_num, tool_url, v_dir, v_num,
    # path_match, r_type
    stars = -1  # can find init or not
    v_name = ''
    v_siv = -1  # 2 siv; 1 not siv; 0 not version, is hash.  Can find init or not
    mod_siv = -1  # 2 siv; 1 not siv; 0 not need add vN.  Can find init or not
    v_hash = ''
    search_e = 0
    insert_e = 0
    insert_s = 0
    update_e = 0
    update_s = 0
    mod_num = -1  # can find init or not
    tool_num = -1  # can find init or not
    mod_url = []  # insert into db, need turn to string
    tool_url = []  # insert into db, need turn to string
    go_list = []
    vendor_list = []
    mod_name = ''
    v_num = '-2'  # can find init or not
    v_dir = -1  # can find init or not: 0 not have; 1 have
    path_match = -1  # 0 not match; 1 match url; 2 match siv url; 3 not mod
    r_type = -1  # can find init or not
    mod_full_path = ''
    mod_req_list = []
    mod_rep_list = []
    mod_dep_list = []  # go.mod, [mod_name，version，type]  type: 1-direct dep; 2-indirect dep; 3-replace
    direct_dep_list = []
    direct_repo_list = []
    not_exit_list = []  # dep tree
    all_dep_list = []  # no mod
    import_list = []
    self_ref = -1

    # mod_path = ''

    # only update repo_name, v_name, v_siv, v_hash
    def __init__(self, repo_name, insert_version):
        self.repo_name = repo_name
        self.check_version(insert_version)
        self.v_hash = self.v_hash[0:7]
        if self.v_hash == '' and self.v_name:
            self.get_hash()
        v_name = self.v_name
        v_hash = self.v_hash
        if self.v_hash:
            self.id = self.repo_name.replace('/', '=') + '@' + self.v_hash
        else:
            self.id = self.repo_name.replace('/', '=') + '@' + self.v_name
        self.init_from_repo_db()
        if self.v_hash == '' and v_hash:
            self.v_hash = v_hash
            # self.id = self.repo_name.replace('/', '=') + '@' + self.v_hash
        elif self.v_name == '' and v_name:
            self.v_name = v_name

    def init_repo_dep_db(self, repo_name, repo_version, repo_hash):
        print(repo_name, repo_version, repo_hash)
        if self.v_hash == '' and repo_hash:
            self.v_hash = repo_hash
            # self.id = self.repo_name.replace('/', '=') + '@' + self.v_hash
        elif self.v_name == '' and repo_version:
            self.v_name = repo_version

    # update the rest param: stars, mod_num, mod_siv, mod_name, mod_url, tool_num, tool_url, v_dir, v_num,
    # path_match, search_e, r_type
    def init_all(self):
        if self.stars == -1:
            self.get_stars()  # stars, search_e
        self.mod_url = []
        self.mod_num = 0
        self.tool_num = 0
        self.tool_num = []
        self.get_dm_local()
        if self.v_name and self.v_num == '-2':
            self.get_v_num()  # v_num -- if have no version name, don't need update this
        if self.mod_num > 0:
            self.get_mod_detail_local()  # v_dir, mod_name, path_match
            self.judge_repo_type()  # r_type

    def init_no_starts(self):
        if self.mod_num == -1 or self.tool_num == -1:
            self.get_dm_local()  # mod_num, mod_url, tool_num, tool_url
        if self.v_name and self.v_num == '-2':
            self.get_v_num()  # v_num -- if have no version name, don't need update this
        if self.mod_num > 0 and (self.v_dir == -1 or self.path_match == -1):
            self.get_mod_detail_local()  # v_dir, mod_name, path_match
        if self.r_type == -1:
            self.judge_repo_type()  # r_type

    def init_starts(self):
        if self.stars == -1:
            self.get_stars()  # stars, search_e

    def init_for_repo_dep(self):
        if self.stars == -1:
            self.get_stars()  # stars, search_e
        if self.mod_num == -1 or self.tool_num == -1:
            self.get_dm_local()  # mod_num, mod_url, tool_num, tool_url

    def init_from_repo_db(self):
        (host, user, password, db_name) = get_db_insert()
        insert_db = get_repo_insert_db()
        sql = "SELECT stars,v_siv,mod_num,mod_siv,mod_name,mod_url,tool_num,tool_url,v_dir,v_num," \
              "path_match,r_type,v_name,v_hash,id FROM "
        sql = sql + insert_db + " WHERE repo_name='%s' AND (v_hash='%s' OR " \
                                "v_name='%s')" % (self.repo_name, self.v_hash, self.v_name)
        try:
            # 执行sql语句
            db_check = pymysql.connect(host, user, password, db_name)
            check_cursor = db_check.cursor()
            check_cursor.execute(sql)
            check_result = check_cursor.fetchall()
            check_cursor.close()
            db_check.close()
            if check_result:
                self.stars = check_result[0][0]
                self.v_siv = check_result[0][1]
                self.mod_num = check_result[0][2]
                self.mod_siv = check_result[0][3]
                self.mod_name = check_result[0][4]
                # self.mod_url = check_result[0][5].strip('&').split('&')
                mod_url_str = check_result[0][5].strip('&')
                if re.findall(r"&", mod_url_str):
                    self.mod_url = mod_url_str.split('&')
                else:
                    self.mod_url = [mod_url_str]
                self.tool_num = check_result[0][6]
                # self.tool_url = check_result[0][7].strip('&').split('&')
                tool_url_str = check_result[0][7].strip('&')
                if re.findall(r"&", tool_url_str):
                    self.tool_url = tool_url_str.split('&')
                else:
                    self.tool_url = [tool_url_str]
                self.v_dir = check_result[0][8]
                self.v_num = str(check_result[0][9])
                self.path_match = check_result[0][10]
                self.r_type = check_result[0][11]
                self.v_name = check_result[0][12]
                self.v_hash = check_result[0][13]
                self.id = check_result[0][14]
        except Exception as exp:
            self.search_e = self.search_e + 1
            print("get repos ", self.repo_name, self.v_name, self.v_hash, " from ", insert_db, " error:", exp)

    def download_repo(self):
        if self.v_hash:
            data = [self.repo_name, self.v_hash]
        else:
            data = [self.repo_name, self.v_name]
        down = DOWNLOAD(data)
        down.down_load_unzip()
        if down.download_result == -1:
            if self.v_hash:
                d_version = self.v_hash
                r = check_insert_mes(self.repo_name, d_version)
                if r == -2 and self.v_name:
                    d_version = self.v_name
                    r = check_insert_mes(self.repo_name, self.v_name)
                if r == -2:
                    last_commit = get_last_hash(self.repo_name)
                    if last_commit:
                        self.v_hash = last_commit
                        d_version = last_commit
                        # (r, page) = check_insert_mes(self.repo_name, last_commit)
                        # if r == 0:
                if r == 0:
                    data = [self.repo_name, d_version]
                    down = DOWNLOAD(data)
                    down.down_load_unzip()

    def get_dep_tree(self):
        layer = 1
        print('now is ', layer, ' layer: ', self.repo_name)
        (db_data, up_list) = repoDep.get_dir_up_from_db(self.repo_name, self.v_name, self.v_hash)
        if db_data > 0:
            # u_repo,u_mod,u_version,u_hash
            all_dep_name_l = []
            for dep in up_list:
                all_dep_name_l.append(dep[0])
                if dep[3]:
                    self.all_dep_list.append([dep[0], dep[3]])
                else:
                    self.all_dep_list.append([dep[0], dep[2]])
            for dep in up_list:
                (r_db_data, r_up_list) = repoDep.get_dir_up_from_db(dep[0], dep[2], dep[3])
                if r_db_data <= 0:
                    dep_repo = Repo(dep[0], dep[2])
                    print('Repo1:', dep[0], dep[2])
                    dep_repo.init_repo_dep_db(dep[0], dep[2], dep[3])
                    dep_repo.init_all()
                    d_sql = dep_repo.insert_repo()
                    if self.mod_num <= 0:
                        self.not_exit_list = []
                        (self.not_exit_list, self.all_dep_list,
                         all_dep_name_l) = dep_repo.get_dep_tree_nomod(layer, self.not_exit_list, self.all_dep_list,
                                                                       all_dep_name_l)
                    else:
                        mod_dep_l = []
                        self.not_exit_list = []
                        self.not_exit_list = dep_repo.get_dep_tree_mod(layer, mod_dep_l, self.not_exit_list)
        else:
            mod_dep_l = []  # not use for now, to record all deps in go.mod
            all_dep_name_l = []
            print(self.repo_name, 'go.mod count: ', self.mod_num)
            if self.mod_num <= 0:
                print('use old way gat dependencies')
                self.get_all_direct_dep()
                direct_list = self.direct_repo_list
                for dd in direct_list:
                    if dd[0] not in all_dep_name_l:
                        self.all_dep_list.append([dd[0], dd[1]])
                        all_dep_name_l.append(dd[0])
            else:
                print('use mod way get dependencies')
                self.get_all_direct_depmod()
                direct_list = self.direct_dep_list
                print('mod-direct-dep-list', direct_list)
                print('mod-dep-list-all', self.mod_dep_list)
            # direct_dep_list
            print(self.repo_name, 'direct build number: ', len(direct_list))
            repo_list = []
            for dep in direct_list:
                print('build tree: ', dep)
                dep_name = dep[0].replace('github.com/', '')
                # 'go.etcd.io/bbolt
                if re.findall(r"go.etcd.io/", dep_name):
                    dep_name = dep_name.replace('go.etcd.io/', 'etcd-io/')
                dep_version = dep[1]
                (insert_error, repo_name, repo_version, repo_name_n) = deal_repo_name_version(dep_name, dep_version)
                print('get_dep_tree', insert_error)
                if insert_error == 0:
                    print('build Repo object: ', repo_name)
                    dep_repo = Repo(repo_name, repo_version)
                    repo_list.append([repo_name, repo_version])
                    dep_repo.init_all()
                    d_sql = dep_repo.insert_repo()
                    # repoDep
                    d_list = [self.repo_name, self.v_name, self.v_hash]
                    u_list = [dep_repo.repo_name, dep_repo.v_name, dep_repo.v_hash]
                    print('build repoDep class: ', d_list, u_list)
                    repo_dep_r = repoDep.RepoDep(d_list, u_list)
                    d_list = [self.mod_num, self.stars]
                    u_list = [dep_repo.mod_num, dep_repo.stars]
                    repo_dep_r.init_no_issue(d_list, u_list)
                    repo_dep_r.insert_repo()
                elif insert_error == -1 and repo_name not in self.not_exit_list:
                    print(self.not_exit_list, type(self.not_exit_list))
                    self.not_exit_list.append([repo_name, self.repo_name])
            for dep in repo_list:
                dep_repo = Repo(dep[0], dep[1])
                dep_repo.init_all()
                d_sql = dep_repo.insert_repo()
                (r_db_data, r_up_list) = repoDep.get_dir_up_from_db(dep_repo.repo_name, dep_repo.v_name,
                                                                    dep_repo.v_hash)
                if r_db_data <= 0:
                    if self.mod_num <= 0:
                        (self.not_exit_list, self.all_dep_list,
                         all_dep_name_l) = dep_repo.get_dep_tree_nomod(layer, self.not_exit_list, self.all_dep_list,
                                                                       all_dep_name_l)
                    else:
                        self.not_exit_list = dep_repo.get_dep_tree_mod(layer, mod_dep_l, self.not_exit_list)

    def get_dep_tree_mod(self, layer, mod_dep_list, n_e_list):
        layer = layer - 1
        print('mod-', layer, 'layer', self.repo_name)
        if self.mod_num <= 0:
            self.get_all_direct_dep()
            direct_list = self.direct_repo_list
        else:
            self.get_all_direct_depmod()
            direct_list = self.direct_dep_list
        print(self.repo_name, 'go.mod: ', self.mod_num)
        # direct_dep_list
        repo_list = []
        for dep in direct_list:
            dep_name = dep[0]
            dep_version = dep[1]
            (insert_error, repo_name, repo_version, repo_name_n) = deal_repo_name_version(dep_name, dep_version)
            print('get_dep_tree_mod', insert_error)
            if insert_error == 0:
                print('mod-', layer, 'layer: c-build-Repo object: ', self.repo_name)
                dep_repo = Repo(repo_name, repo_version)
                repo_list.append([repo_name, repo_version])
                dep_repo.init_all()
                d_sql = dep_repo.insert_repo()
                # repoDep
                d_list = [self.repo_name, self.v_name, self.v_hash]
                u_list = [dep_repo.repo_name, dep_repo.v_name, dep_repo.v_hash]
                print('build repoDep class: ', d_list, u_list)
                repo_dep_r = repoDep.RepoDep(d_list, u_list)
                d_list = [self.mod_num, self.stars]
                u_list = [dep_repo.mod_num, dep_repo.stars]
                repo_dep_r.init_no_issue(d_list, u_list)
                repo_dep_r.insert_repo()
            elif insert_error == -1 and repo_name not in n_e_list:
                n_e_list.append([repo_name, self.repo_name])
        if layer:
            for dep in repo_list:
                dep_repo = Repo(dep[0], dep[1])
                dep_repo.init_all()
                d_sql = dep_repo.insert_repo()
                (r_db_data, r_up_list) = repoDep.get_dir_up_from_db(dep_repo.repo_name, dep_repo.v_name,
                                                                    dep_repo.v_hash)
                if r_db_data <= 0:
                    n_e_list = dep_repo.get_dep_tree_mod(layer, mod_dep_list, n_e_list)
        repo_local = self.get_local_url()
        check_result = os.path.isdir(repo_local)
        if check_result:
            shutil.rmtree(repo_local)
        return n_e_list

    def get_dep_tree_nomod(self, layer, n_e_list, all_dep_list, all_dep_name_l):
        layer = layer - 1
        print('nomod-', layer, 'layer: ', self.repo_name)
        if self.mod_num <= 0:
            self.get_all_direct_dep()
            direct_list = self.direct_repo_list
        else:
            direct_list = self.get_mdl_last_commit()
        print(self.repo_name, 'go.mod count: ', self.mod_num)
        # direct_dep_list
        repo_list = []
        for dep in direct_list:
            if dep[0] not in all_dep_name_l:
                all_dep_name_l.append(dep[0])
                all_dep_list.append([dep[0], dep[1]])
                dep_name = dep[0]
                dep_version = dep[1]
                (insert_error, repo_name, repo_version, repo_name_n) = deal_repo_name_version(dep_name, dep_version)
                print('get_dep_tree_nomod', insert_error)
                if insert_error == 0:
                    print('nomod-', layer, 'layer: c-build-Repo object: ', self.repo_name)
                    dep_repo = Repo(repo_name, repo_version)
                    repo_list.append([repo_name, repo_version])
                    dep_repo.init_all()
                    d_sql = dep_repo.insert_repo()
                    # repoDep
                    d_list = [self.repo_name, self.v_name, self.v_hash]
                    u_list = [dep_repo.repo_name, dep_repo.v_name, dep_repo.v_hash]
                    print('build repoDep class: ', d_list, u_list)
                    repo_dep_r = repoDep.RepoDep(d_list, u_list)
                    d_list = [self.mod_num, self.stars]
                    u_list = [dep_repo.mod_num, dep_repo.stars]
                    repo_dep_r.init_no_issue(d_list, u_list)
                    repo_dep_r.init_from_repo_db()
                elif insert_error == -1 and repo_name not in n_e_list:
                    n_e_list.append([repo_name, self.repo_name])
        if layer:
            for dep in repo_list:
                dep_repo = Repo(dep[0], dep[1])
                dep_repo.init_all()
                d_sql = dep_repo.insert_repo()
                (r_db_data, r_up_list) = repoDep.get_dir_up_from_db(dep_repo.repo_name, dep_repo.v_name,
                                                                    dep_repo.v_hash)
                if r_db_data <= 0:
                    n_e_list = dep_repo.get_dep_tree_nomod(layer, n_e_list, all_dep_list, all_dep_name_l)
        repo_local = self.get_local_url()
        check_result = os.path.isdir(repo_local)
        if check_result:
            shutil.rmtree(repo_local)
        return n_e_list, all_dep_list, all_dep_name_l

    def get_mdl_last_commit(self):
        self.get_all_direct_depmod()
        mdl_lcl = []
        for dep in self.direct_dep_list:
            repo_name = get_repo_name(dep[0])
            if repo_name:
                last_commit = get_last_hash(repo_name.replace('github.com/', ''))
                if last_commit:
                    mdl_lcl.append([dep[0], last_commit])
                else:
                    print('*******get last commit failed*********************')
        return mdl_lcl

    def get_mdl_last_version(self):
        self.get_all_direct_depmod()
        mdl_lvl = []
        for dep in self.direct_dep_list:
            repo_name = get_repo_name(dep[0])
            if repo_name:
                (last_version, semantic) = get_last_version(repo_name.replace('github.com/', ''))
                if last_version:
                    mdl_lvl.append([dep[0], last_version])
                else:
                    print('*******get last commit failed*********************')
                    last_commit = get_last_hash(repo_name.replace('github.com/', ''))
                    if last_commit:
                        mdl_lvl.append([dep[0], last_commit])
                    else:
                        print('*******get last commit failed*********************')
        return mdl_lvl

    def get_hash(self):
        url = "https://github.com/" + self.repo_name + '/tree/' + self.v_name
        (self.v_hash, self.search_e) = get_hash(url, self.search_e)

    # def get_dm(self):
    #     headers = get_headers()
    #     (self.mod_num, self.mod_url, self.tool_num, self.tool_url,
    #      self.search_e) = get_dm_msg(self.repo_name, headers,self.search_e)

    def get_local_url(self):  # get local repo dir
        path_c = PATH()
        path = path_c.path
        repo_local_r = os.path.join('pkg', self.id)  # pkg/kiali=kiali@v1.0.0
        repo_local = os.path.join(path, repo_local_r)
        return repo_local

    def get_dm_local(self):
        self.path_match = 3
        self.v_dir = 0
        self.mod_num = 0
        self.tool_num = 0
        self.mod_url = []
        self.tool_url = []
        self.download_repo()
        repo_local = self.get_local_url()
        root_url = repo_local
        # print('get_dm_local', root_url, repo_local)
        (self.go_list, self.mod_url, self.tool_url,
         self.vendor_list) = deal_local_repo(root_url, repo_local, self.go_list, self.mod_url, self.tool_url,
                                             self.vendor_list)
        # print('go_list', self.go_list)
        self.mod_num = len(self.mod_url)
        self.tool_num = len(self.tool_url)
        if self.mod_num > 0:
            self.mod_url.sort(key=lambda m: len(m), reverse=False)
        if self.tool_num > 0:
            self.tool_url.sort(key=lambda t: len(t), reverse=False)
        # print(self.go_list)

    def check_version(self, insert_version):
        insert_version = insert_version.strip()
        if re.findall(r"^v\d+?.\d+?.\d+?-[0-9a-zA-Z.]+?$", insert_version) or re.findall(r"^v\d+?.\d+?.\d+?$",
                                                                                         insert_version):
            # siv version
            self.v_siv = 2
        elif re.findall(r"^[0-9a-zA-Z]+?$", insert_version) and len(insert_version) >= 7:
            if re.findall(r"^v\d+?$", insert_version) or re.findall(r"^[a-zA-Z]+?$", insert_version) or \
                    re.findall(r"^RELEASE.+?$", insert_version):
                self.v_siv = 1  # version not siv
            elif re.findall(r"^20\d+?$", insert_version) and 2000 < int(insert_version[0:4]) <= 2021:
                self.v_siv = 1  # version not siv
            else:
                self.v_siv = 0  # not version, is hash
        else:
            self.v_siv = 1
        if self.v_siv == 0:
            self.v_hash = insert_version
            self.v_name = ''
        else:
            self.v_name = insert_version
            self.v_hash = ''
        # (insert_error, repo_name, repo_version, repo_name_n) = deal_repo_name_version(self.repo_name, insert_version)
        # if insert_error == 0 and repo_version != insert_version:
        #     if re.findall(r"^v\d+?.\d+?.\d+?-[0-9a-zA-Z.]+?$", repo_version) or re.findall(r"^v\d+?.\d+?.\d+?$",
        #                                                                                      repo_version):
        #         # siv version
        #         self.v_siv = 2
        #     elif re.findall(r"^[0-9a-zA-Z]+?$", repo_version) and len(repo_version) >= 7:
        #         if re.findall(r"^v\d+?$", repo_version) or re.findall(r"^[a-zA-Z]+?$", repo_version) or \
        #                 re.findall(r"^RELEASE.+?$", repo_version):
        #             self.v_siv = 1  # version not siv
        #         elif re.findall(r"^20\d+?$", repo_version) and 2000 < int(repo_version[0:4]) <= 2021:
        #             self.v_siv = 1  # version not siv
        #         else:
        #             self.v_siv = 0  # not version, is hash
        #     else:
        #         self.v_siv = 1
        #     if self.v_siv == 0:
        #         self.v_hash = repo_version
        #         self.v_name = ''
        #     else:
        #         self.v_name = repo_version
        #         self.v_hash = ''
        # else:
        #     self.v_name = ''
        #     self.v_hash = ''

    def get_stars(self):
        repo_name_url = 'https://api.github.com/repos/' + self.repo_name
        print(repo_name_url)
        headers = get_headers()
        try:
            page_results = get_results(repo_name_url, headers)
            self.stars = page_results['stargazers_count']
        except Exception as exp:
            print("get search error ", self.repo_name, ' : ', exp)
            time.sleep(2)
            try:
                page_results = get_results(repo_name_url, headers)
                self.stars = page_results['stargazers_count']
            except Exception as exp:
                print("get search error ", self.repo_name, ' : ', exp)
                self.search_e = self.search_e + 1

    def get_v_num(self):
        if re.findall(r"^v(\d+?)\.", self.v_name):
            self.v_num = re.findall(r"^v(\d+?)\.", self.v_name)[0]  # string
        else:
            if re.findall(r"^v(\d+?)$", self.v_name):
                self.v_num = re.findall(r"^v(\d+?)$", self.v_name)[0]
            else:
                self.v_num = '-1'

    # def get_mod_detail(self):
    #     if self.v_hash:
    #         s_version = self.v_hash
    #     else:
    #         s_version = self.v_name
    #     sub_dir = ''
    #     mod_cu = ''
    #     mod_detail = {'content': ''}
    #     if int(self.v_num) > 1:
    #         sub_dir = 'v' + self.v_num
    #         for p in self.mod_url:
    #             if re.findall(r"/v" + self.v_num + "/$", p):
    #                 mod_cu = p  # have v_dir
    #                 break
    #     self.v_dir = 0
    #     if mod_cu:
    #         self.v_dir = 1
    #         mod_path_ns = ('github.com/' + self.repo_name + mod_cu).strip('/')
    #         mod_path = ('github.com/' + self.repo_name + mod_cu).strip('/')  # as siv said, mod path should be this
    #     else:
    #         mod_cu = self.mod_url[0]
    #         mod_path = ('github.com/' + self.repo_name + mod_cu + sub_dir).strip('/')
    #         if sub_dir:
    #             mod_path_ns = ('github.com/' + self.repo_name + mod_cu).strip('/')
    #         else:
    #             mod_path_ns = mod_path
    #     if mod_cu.strip('/'):
    #         m_url = 'https://api.github.com/repos/' + self.repo_name + '/contents/' + mod_cu.strip('/') + '/go.mod'
    #         m_url = m_url + '?ref=' + s_version
    #     else:
    #         m_url = 'https://api.github.com/repos/' + self.repo_name + '/contents/go.mod?ref=' + s_version
    #     headers = get_headers()
    #     try:
    #         mod_detail = get_results(m_url, headers)
    #     except Exception as exp:
    #         print("get url result error ", m_url, ' : ', exp)
    #         time.sleep(1)
    #         try:
    #             mod_detail = get_results(m_url, headers)
    #         except Exception as exp:
    #             print("get url result error ", m_url, ' : ', exp)
    #             self.search_e = self.search_e + 1
    #     if mod_detail['content']:
    #         go_mod_content_ud = base64.b64decode(mod_detail['content'])
    #         go_mod_content = go_mod_content_ud.decode()
    #         self.deal_go_mod(go_mod_content, sub_dir, mod_path, mod_path_ns, mod_cu)

    def get_mod_detail_local(self):
        sub_dir = ''
        mod_cu = ''
        if int(self.v_num) > 1:
            sub_dir = 'v' + self.v_num
            for p in self.mod_url:
                if re.findall(r"/v" + self.v_num + "/$", p):
                    mod_cu = p  # have v_dir
                    break
        else:
            for p in self.mod_url:
                if re.findall(r"/v\d+?/$", p):
                    path_v = re.findall(r"/v(\d+?)/$", p)[0]
                    if int(path_v) >= 2:
                        self.v_num = path_v
                        mod_cu = p  # have v_dir
                    break
        self.v_dir = 0
        if mod_cu:
            self.v_dir = 1
            mod_path_ns = ('github.com/' + self.repo_name + mod_cu).strip('/')
            mod_path = ('github.com/' + self.repo_name + mod_cu).strip('/')  # as siv said, mod path should be this
        else:
            mod_cu = self.mod_url[0]
            mod_path = ('github.com/' + self.repo_name + mod_cu + sub_dir).strip('/')
            if sub_dir:
                mod_path_ns = ('github.com/' + self.repo_name + mod_cu).strip('/')
            else:
                mod_path_ns = mod_path
        repo_local = self.get_local_url()
        m_url = repo_local + mod_cu + 'go.mod'
        if os.path.isfile(m_url):
            f = open(m_url)
            go_mod_content = f.read()
            f.close()
            self.deal_go_mod(go_mod_content, sub_dir, mod_path, mod_path_ns, mod_cu)

    def deal_go_mod(self, go_mod_content, sub_dir, mod_path, mod_path_ns, mod_cu):
        # 0 not match; 1 match url; 2 match siv url; 3 not mod
        # mod_path_ns not siv; mod_path siv.
        module = re.findall(r"^module\s*(.+?)$", go_mod_content, re.M)
        if module:
            go_mod_module = module[0].replace('"', '').strip()
        else:
            go_mod_module = ''
        self.mod_full_path = go_mod_module
        mod_siv_path = ''
        if re.findall(r"^.+?/(v\d+?)$", go_mod_module):
            mod_siv_path = re.findall(r"^.+?/(v\d+?)$", go_mod_module)[0]
        elif re.findall(r"^.+?\.(v\d+?)$", go_mod_module):
            mod_siv_path = re.findall(r"^.+?\.(v\d+?)$", go_mod_module)[0]
        if not self.v_name:
            if mod_siv_path:
                self.mod_siv = 2
                self.v_num = mod_siv_path.replace('v', '')
                sub_dir = 'v' + self.v_num
                mod_path = mod_path + '/' + sub_dir
        if sub_dir:
            if re.findall(r"^.+?/" + sub_dir, go_mod_module) or re.findall(r"^.+?\." + sub_dir, go_mod_module):
                self.mod_siv = 2
                self.mod_name = go_mod_module.replace('/' + sub_dir, '').replace('.' + sub_dir, '')
            else:
                self.mod_siv = 1
                self.mod_name = go_mod_module
        else:
            self.mod_siv = 0
            self.mod_name = go_mod_module
        if go_mod_module != mod_path and go_mod_module != mod_path_ns:
            repo_name = get_repo_name(go_mod_module)
            if repo_name and repo_name == self.repo_name:
                # self.path_match = 0
                if int(self.v_num) > 1 and self.mod_siv == 2:
                    self.path_match = 2
                elif int(self.v_num) > 1 and self.mod_siv == 1:
                    self.path_match = 1
                elif int(self.v_num) <= 1:
                    self.path_match = 2
            else:
                if re.findall(r"^(gopkg\.in/.+?)\.v\d", go_mod_module):
                    self.path_match = 2
                elif re.findall(r"^(k8s\.com/.+?)$", go_mod_module):
                    if int(self.v_num) > 1 and self.mod_siv == 2:
                        self.path_match = 2
                    elif int(self.v_num) > 1 and self.mod_siv == 1:
                        self.path_match = 1
                    elif int(self.v_num) <= 1:
                        self.path_match = 2
                else:
                    self.path_match = 0
        elif go_mod_module == mod_path:
            self.path_match = 2
        elif go_mod_module == mod_path_ns and go_mod_module != mod_path:
            self.path_match = 1

            # check_1 = get_redirect_repo(self.repo_name)
            # check_2 = get_new_url(self.repo_name)
            # if check_1 == '' and check_2 == '':
            #     # for now can recognise these types  [@@need add more@@]
            #     if re.findall(r"^k8s\.com", go_mod_module) and re.findall(r"^gopkg\.in/", go_mod_module):
            #         old_url = 'github.com/' + self.repo_name
            #         if re.findall(r"^(k8s\.com/.+?)/", go_mod_module):
            #             now_url = re.findall(r"^(k8s\.com/.+?)/", go_mod_module)[0]
            #         elif re.findall(r"^(k8s\.com/.+?)$", go_mod_module):
            #             now_url = re.findall(r"^(k8s\.com/.+?)$", go_mod_module)[0]
            #         elif re.findall(r"^(gopkg\.in/.+?)\.v\d", go_mod_module):
            #             now_url = re.findall(r"^(gopkg\.in/.+?)\.v\d", go_mod_module)[0]
            #         elif re.findall(r"^(golang.org/x/[^/]+?)", go_mod_module):
            #             now_url = re.findall(r"^(golang.org/x/[^/]+?)", go_mod_module)[0]
            #         else:
            #             now_url = ''
            #         # update new_web_name
            #         if now_url:
            #             (self.insert_e, self.insert_s) = insert_new_url(old_url, now_url, self.insert_e, self.insert_s)
            #         check_1 = get_redirect_repo(self.repo_name)
            #         check_2 = get_new_url(self.repo_name)
            # if check_1 == '' and check_2 == '':
            #     self.path_match = 0
            # else:
            #     if check_2:
            #         n_mod_url = check_2
            #     else:
            #         n_mod_url = 'github.com/' + check_1
            #     mod_path = mod_path.replace('github.com/' + self.repo_name, n_mod_url)
            #     mod_path_ns = mod_path_ns.replace('github.com/' + self.repo_name, n_mod_url)
            #     if re.findall(r"^gopkg\.in/", mod_path):
            #         sub_dir_gopkg = '.v' + self.v_num
            #         mod_path = (n_mod_url + sub_dir_gopkg + mod_cu).strip('/')
            #         mod_path_ns = mod_path
            #     if go_mod_module != mod_path and go_mod_module != mod_path_ns:
            #         self.path_match = 0
            #     elif go_mod_module == mod_path_ns and go_mod_module != mod_path:
            #         self.path_match = 1
            #     else:
            #         self.path_match = 2

    def judge_repo_type(self):
        self.r_type = 0
        if self.mod_num >= 0 and self.v_dir >= 0 and self.path_match >= 0:
            if self.mod_num > 0:
                if 2 > int(self.v_num) >= 0:
                    if self.path_match == 2:
                        self.r_type = 1
                if int(self.v_num) >= 2:
                    if self.v_dir == 0:
                        if self.path_match == 2:
                            self.r_type = 2
                        elif self.path_match == 1:
                            self.r_type = 4
                    elif self.v_dir == 1:
                        if self.path_match == 2:
                            self.r_type = 3
            elif self.mod_num == 0:
                if 2 > int(self.v_num) >= 0:
                    self.r_type = 7
                if int(self.v_num) >= 2:
                    self.r_type = 9
            if self.v_name == '':
                if self.mod_num > 0:
                    self.r_type = 5
                else:
                    self.r_type = 6
            if self.path_match == 0:
                self.r_type = 10
        else:
            if self.mod_num == -1:
                self.get_dm_local()  # mod_num, mod_url, tool_num, tool_url, search_e,
                if self.v_name:
                    self.get_v_num()  # v_num -- if have no version name, don't need update this
                if self.mod_num > 0:
                    self.get_mod_detail_local()  # v_dir, mod_name, path_match
            if self.path_match == -1:
                if self.v_name and self.v_num == '-2':
                    self.get_v_num()  # v_num -- if have no version name, don't need update this
                if self.mod_num > 0:
                    self.get_mod_detail_local()  # v_dir, mod_name, path_match
                self.judge_repo_type()

    def check_repo_db(self):
        (host, user, password, db_name) = get_db_insert()
        insert_db = get_repo_insert_db()
        sql = "SELECT stars,v_siv,mod_num,mod_siv,mod_name,mod_url,tool_num,tool_url,v_dir,v_num," \
              "path_match,r_type,v_name,v_hash,id FROM "
        sql = sql + insert_db + " WHERE repo_name='%s' AND (v_hash='%s' OR " \
                                "v_name='%s')" % (self.repo_name, self.v_hash, self.v_name)
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
            print("check repos ", self.repo_name, self.v_name, self.v_hash, " from ", insert_db, " error:", exp)
            return -1, []

    def insert_repo(self):
        (host, user, password, db_name) = get_db_insert()
        insert_db = get_repo_insert_db()
        (check_result, result_list) = self.check_repo_db()
        mod_url_str = ''
        tool_url_str = ''
        sql = ''
        for i in self.mod_url:
            mod_url_str = mod_url_str + i + '&'
        for i in self.tool_url:
            tool_url_str = tool_url_str + i + '&'
        if check_result < 1:
            insert_sql = "INSERT INTO " + insert_db
            insert_sql = insert_sql + " (id,repo_name,stars,v_name,v_siv,v_hash,mod_num,mod_siv,mod_name,mod_url," \
                                      "tool_num,tool_url,v_dir,v_num,path_match,r_type) VALUES ('%s','%s','%d','%s'," \
                                      "'%d','%s','%d','%d','%s','%s','%d','%s','%d','%d','%d'," \
                                      "'%d')" % (self.id, self.repo_name, self.stars, self.v_name, self.v_siv,
                                                 self.v_hash, self.mod_num, self.mod_siv, self.mod_name, mod_url_str,
                                                 self.tool_num, tool_url_str, self.v_dir, int(self.v_num),
                                                 self.path_match, self.r_type)
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
            # stars,v_siv,mod_num,mod_siv,mod_name,mod_url,tool_num,tool_url,v_dir,v_num,path_match,r_type
            class_list = [self.stars, self.v_siv, self.mod_num, self.mod_siv, self.mod_name, mod_url_str,
                          self.tool_num, tool_url_str, self.v_dir, int(self.v_num), self.path_match, self.r_type,
                          self.v_name, self.v_hash, self.id]
            change = 0
            for i in range(0, len(class_list)):
                if result_list[i] != class_list[i] and class_list[i] != '' and class_list[i] != '-2' \
                        and class_list[i] != -1:
                    change = change + 1
            if change > 0:
                update_sql = "UPDATE " + insert_db
                update_sql = update_sql + " SET stars='%d',v_siv='%d',mod_num='%d',mod_siv='%d',mod_name='%s'," \
                                          "mod_url='%s',tool_num='%d',tool_url='%s',v_dir='%d',v_num='%d'," \
                                          "path_match='%d',r_type='%d',v_name='%s',v_hash='%s',id='%s' " \
                                          "WHERE repo_name='%s' " \
                                          "AND id='%s'" % (self.stars, self.v_siv, self.mod_num, self.mod_siv,
                                                           self.mod_name, mod_url_str, self.tool_num, tool_url_str,
                                                           self.v_dir, int(self.v_num), self.path_match,
                                                           self.r_type, self.v_name, self.v_hash, self.id,
                                                           self.repo_name, result_list[14])
                db = pymysql.connect(host, user, password, db_name)
                # print(update_sql)
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

    def get_all_mod_requires(self):
        # print('get_all_mod_requires: ', self.mod_dep_list)
        if not self.mod_dep_list:
            for m_url in self.mod_url:
                repo_local = self.get_local_url()
                url = repo_local + m_url + 'go.mod'
                (self.mod_req_list, self.mod_rep_list) = get_mod_require(url, self.mod_req_list, self.mod_rep_list)
                # print('dependencies from go.mod files :', self.mod_req_list, self.mod_rep_list)
            # mod_dep_list
            for m in self.mod_req_list:
                dep = m.replace('+replace', '').replace('// indirect', '').strip().split(' ')
                if len(dep) > 1:
                    dep_version = deal_dep_version(dep[1])
                    if re.findall(r"\+replace", m) and dep:
                        self.mod_dep_list.append([dep[0], dep_version, 3])  # replace
                    elif re.findall(r"// indirect", m) and dep:
                        self.mod_dep_list.append([dep[0], dep_version, 2])  # dep from old repo
                    elif dep:
                        self.mod_dep_list.append([dep[0], dep_version, 1])  # normal
            # print('mod_dep_list:', self.mod_dep_list)

    def get_one_mod_requires(self, m_url):
        o_mod_req_list = []
        o_mod_rep_list = []
        repo_local = self.get_local_url()
        url = repo_local + m_url + 'go.mod'
        (o_mod_req_list, o_mod_rep_list) = get_mod_require(url, o_mod_req_list, o_mod_rep_list)
        return o_mod_req_list, o_mod_rep_list

    def get_all_direct_requires(self):
        # print('get_all_direct_requires: ', self.import_list, self.go_list)
        if not self.import_list:
            for f_url in self.go_list:
                repo_local = self.get_local_url()
                file_url = repo_local + f_url
                self.import_list = get_requires_from_file(file_url, self.import_list)
            delete_list = []
            for i in self.import_list:
                if self.mod_full_path:
                    delete_name = self.mod_full_path
                else:
                    delete_name = 'github.com/' + self.repo_name
                if re.findall(r"^" + delete_name, i):
                    delete_list.append(i)
            self.self_ref = len(delete_list)
            for d in delete_list:
                self.import_list.remove(d)

    def get_all_direct_dep(self):
        print('get_all_direct_dep：', self.import_list)
        if not self.import_list:
            self.get_all_direct_requires()
            print('import list :', self.import_list)
            repo_list = []
            dep_list = []
            delet_list = []
            for imp in self.import_list:
                if re.findall(r"^github\.com/" + self.repo_name, imp):
                    delet_list.append(imp)
                elif not re.findall(r"^github\.com/", imp):
                    repo_name = get_repo_name(imp)
                    if repo_name:
                        if (not re.findall(r"^" + repo_name, imp.replace('github.com/', ''))) \
                                and (not re.findall(r"^github\.com/", imp)):
                            now_name = get_new_url('github.com/' + repo_name)
                            if [repo_name, now_name] not in repo_list:
                                repo_list.append([repo_name, now_name])
                            if now_name:
                                if now_name not in dep_list:
                                    dep_list.append(now_name)
                            else:
                                dep_list.append(repo_name)
                else:
                    if re.findall(r"^github\.com/([^/]+?/[^/]+?)$", imp):
                        repo_name = re.findall(r"^github\.com/([^/]+?/[^/]+?)$", imp)[0]
                    elif re.findall(r"^github\.com/[^/]+?/([^/]+?)/", imp):
                        repo_name = re.findall(r"^github\.com/([^/]+?/[^/]+?)/", imp)[0]
                    else:
                        repo_name = ''
                    if repo_name and ([repo_name, ''] not in repo_list):
                        repo_list.append([repo_name, ''])
                        # print('get_all_direct_dep方法:', [repo_name, ''])
                    if repo_name and (repo_name not in dep_list):
                        dep_list.append(repo_name)
            for d in delet_list:
                self.import_list.remove(d)
            for dep in repo_list:
                # print('deal, need add last commit', dep)
                last_commit = get_last_hash(dep[0].replace('github.com/', ''))
                if last_commit:
                    # print('add version：', [dep[0], last_commit, dep[1]])
                    self.direct_repo_list.append([dep[0], last_commit, dep[1]])
                else:
                    print('*******get last commit failed*********************')
                    # self.direct_repo_list.append([dep[0], '', dep[1]])
            # print('direct_repo_list:', self.direct_repo_list)
        else:
            # print('import list :', self.import_list)
            repo_list = []
            dep_list = []
            delet_list = []
            for imp in self.import_list:
                if re.findall(r"^github\.com/" + self.repo_name, imp):
                    delet_list.append(imp)
                elif not re.findall(r"^github\.com/", imp):
                    repo_name = get_repo_name(imp)
                    if repo_name:
                        if (not re.findall(r"^" + repo_name, imp.replace('github.com/', ''))) \
                                and (not re.findall(r"^github\.com/", imp)):
                            now_name = get_new_url('github.com/' + repo_name)
                            if [repo_name, now_name] not in repo_list:
                                repo_list.append([repo_name, now_name])
                            if now_name:
                                if now_name not in dep_list:
                                    dep_list.append(now_name)
                            else:
                                dep_list.append(repo_name)
                else:
                    if re.findall(r"^github\.com/([^/]+?/[^/]+?)$", imp):
                        repo_name = re.findall(r"^github\.com/([^/]+?/[^/]+?)$", imp)[0]
                    elif re.findall(r"^github\.com/[^/]+?/([^/]+?)/", imp):
                        repo_name = re.findall(r"^github\.com/([^/]+?/[^/]+?)/", imp)[0]
                    else:
                        repo_name = ''
                    if repo_name and ([repo_name, ''] not in repo_list):
                        repo_list.append([repo_name, ''])
                    if repo_name and (repo_name not in dep_list):
                        dep_list.append(repo_name)
            for d in delet_list:
                self.import_list.remove(d)
            for dep in repo_list:
                last_commit = get_last_hash(dep[0].replace('github.com/', ''))
                if last_commit:
                    self.direct_repo_list.append([dep[0], last_commit, dep[1]])
                else:
                    print('*******get last commit failed*********************')
                    # self.direct_repo_list.append([dep[0], '', dep[1]])
            print('direct_repo_list为：', self.direct_repo_list)

    def get_all_direct_depmod(self):  # get direct dep through this
        # print('get_all_direct_depmod')
        # # direct_dep_list
        # print(self.import_list, self.mod_dep_list)
        if not self.import_list:
            self.get_all_direct_requires()
            print(self.import_list)
        if not self.mod_dep_list:
            self.get_all_mod_requires()

        for m_d in self.mod_dep_list:
            if m_d[2] == 1:
                for i in self.import_list:
                    if re.findall(r"^" + m_d[0], i) and ([m_d[0], m_d[1]] not in self.direct_dep_list):
                        self.direct_dep_list.append([m_d[0], m_d[1]])
                        break

    def get_e_s_param(self):
        return self.search_e, self.insert_e, self.insert_s, self.update_e, self.update_s

    def get_down_repo_msg(self):
        headers = get_headers()
        tool_name_list = get_tool_name_list()
        mod_down = 0
        mod_down_url = []
        tool_down = 0
        tool_down_url = []
        search_name_list = []
        search_name_1 = ''
        repo_name = 'github.com/' + self.repo_name
        tool_str = ''
        for t in tool_name_list:
            tool_str = tool_str + '+file:' + t
        if self.mod_full_path:
            seach_name_1 = self.mod_full_path
            search_name_list.append(seach_name_1)
        if search_name_1 and repo_name != search_name_1:
            search_name_2 = repo_name
            search_name_list.append(search_name_2)
        new_web_name = get_new_url(repo_name)
        if new_web_name:
            search_name_3 = new_web_name
            search_name_list.append(search_name_3)
        for search_name in search_name_list:
            url_mod = 'https://api.github.com/search/code?q=' + search_name + '+filename:go.mod'
            try:
                results_mod = get_results(url_mod, headers)
                down_mod_count = results_mod['total_count']
                # print('new users count:', down_mod_count)
                if down_mod_count > 0:
                    mod_down = mod_down + down_mod_count
                    mod_down_url.append(url_mod)
                time.sleep(1.2)
            except Exception as exp:
                print("get mod users error", exp, '***********************************************')
                time.sleep(2)
                try:
                    results_mod = get_results(url_mod, headers)
                    down_mod_count = results_mod['total_count']
                    if down_mod_count > 0:
                        mod_down = mod_down + down_mod_count
                        mod_down_url.append(url_mod)
                except Exception as exp:
                    print("get mod users error2", exp, '***********************************************')
            url_tool = 'https://api.github.com/search/code?q=' + search_name + tool_str
            print('url_old', url_tool)
            try:
                results_tool = get_results(url_tool, headers)
                down_tool_count = results_tool['total_count']
                # print('old users count:', down_old_count)
                if down_tool_count > 0:
                    tool_down = tool_down + down_tool_count
                    tool_down_url.append(url_tool)
                time.sleep(1.2)
            except Exception as exp:
                print("get tool users error", exp, '***********************************************')
                time.sleep(2)
                try:
                    results_tool = get_results(url_tool, headers)
                    down_tool_count = results_tool['total_count']
                    if down_tool_count > 0:
                        tool_down = tool_down + down_tool_count
                        tool_down_url.append(url_tool)
                    time.sleep(1.2)
                except Exception as exp:
                    print("get tool users error2", exp, '***********************************************')
        return [mod_down, mod_down_url, tool_down, tool_down_url]
