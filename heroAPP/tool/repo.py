import json
import os
import random
import re
import shutil
import time
from urllib.request import Request, urlopen

import chardet
import requests
from bs4 import BeautifulSoup
import pymysql
# from download import DOWNLOAD
# from download import PATH
# import repoDep
# import downDep
from .download import DOWNLOAD
from .download import PATH
from . import repoDep
from . import downDep
# import dealDmIntoFile


# get result through url [public-method]
def get_results(url, headers):
    request = Request(url, headers=headers)
    response = urlopen(request).read()
    result = json.loads(response.decode())
    return result


# start  一些参数
def get_repo_insert_db():
    return 'repo'


def get_db_search():
    host = '47.88.48.19'
    user = 'root'
    password = 'Ella1996'
    db_name = 'githubspider'
    return host, user, password, db_name


def get_db_insert():  # downDep 中有重复
    host = '47.88.48.19'
    user = 'root'
    password = 'Ella1996'
    db_name = 'hero-tool'
    return host, user, password, db_name


def get_tool_name_list():
    tool_name_list = ['Godeps.json', 'vendor.conf', 'vendor.json', 'glide.yaml', 'glide.toml', 'Gopkg.toml', 'Godep.json']
    return tool_name_list


def get_tool_name_list_2():
    tool_name_list = ['glide.lock', 'Gopkg.lock']
    return tool_name_list


def get_token():  # download 重复
    # token 0a6cca72aa3cc98993950500c87831bfef7e5707 [meng] x
    # token ad418c5441a67ad8b2c95188e131876c6a1187fe [end] x
    # token abdd967d350662632381f130cd62268ed2f961a1 [end] x
    # token ff4e63b2dba8febac0aeb59aa3b8829a05de97e7 [hu] x
    # token a41ca9587818fc355b015376e814df47223fc136 [me] x

    # token a8ad3ffb79d2ef67a1f19da8245ff361e624dc20 [ql] x
    # token 6f8454c973d4f7f07a57c2982db79d2ce543403d [zs] x
    # token 3e87d1e3a489815cdf597a10b426ad1e2a7426db [zs] x
    # token 24748c727dfbcbfa18c3478f495c2b8b6ed1703e [ql] x
    # token 412aed2204841af74b641fbbc7bfdd2274ca9d71 [ql]
    # token 7e874141d51454c0b7eeee77052bf4977588c076 [djt]
    # token c2f78adf111b7630ca6bd643876f6dd68b781f8f [zs] 
    token_list = ['412aed2204841af74b641fbbc7bfdd2274ca9d71', '7e874141d51454c0b7eeee77052bf4977588c076',
                  'c2f78adf111b7630ca6bd643876f6dd68b781f8f']
    index_num = random.randint(0, 2)
    return token_list[index_num]


# get random headers [public-method]
def get_headers():
    # headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0',
    #            'Content-Type': 'application/json', 'Accept': 'application/json'}
    token = get_token()
    token_str = 'token ' + token
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/json', 'Accept': 'application/json',
               'Authorization': token_str}
    # headers_2 = {'User-Agent': 'Mozilla/5.0',
    #              'Content-Type': 'application/json', 'Accept': 'application/json',
    #              'Authorization': 'token a8ad3ffb79d2ef67a1f19da8245ff361e624dc20'}
    # headers_3 = {'User-Agent': 'Mozilla/5.0',
    #              'Content-Type': 'application/json', 'Accept': 'application/json',
    #              'Authorization': 'token 0a6cca72aa3cc98993950500c87831bfef7e5707'}
    return headers
# end  一些参数


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
        # print('1.:', repo_name, subdir_name, '************************************get_releases_url*******')
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
            print("When find version: get search error", exp, '-------------------------------------------------------')
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
        # print('%%%%get the last commit hash is:', last_commt, fullname)
    except Exception as exp:
        last_commt = ''
        print("************** get search releases_url error", exp, '*******************************************')
    return last_commt


# get hash through version, 获取一个版本对应的哈希值，需要补充一个通过哈希值获取版本的方法 ~~~
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


def get_last_version_or_hashi(repo_name, search_e):
    v_name = ''
    v_hashi = ''
    (v_name, semantic) = get_last_version(repo_name)
    if not semantic:
        v_hashi = get_last_hash(repo_name)
    else:
        url = "https://github.com/" + repo_name + '/tree/' + v_name
        (v_hash, search_e) = get_hash(url, search_e)
    return v_name, v_hashi, search_e


# 4个issue report 中的特定方法
# check issue report repos or not
def get_repo_now_name(repo_name):
    (host, user, password, db_name) = get_db_insert()
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT now_repo FROM hashToVersion WHERE repo_name='%s'" % repo_name
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
            # result_num = int(check_result[0][0])
            return check_result[0][0]
        else:
            return '0'
    except Exception as exp:
        print('check hashToVersion error:',
              exp, '--------------------------------------------------------------------------------------------------')
        return '-1'


# check issue report repos or not
def get_fake_version_list():
    (host, user, password, db_name) = get_db_insert()
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT repo_name,r_hash,issue FROM fake_version"
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        if check_result:
            fake_list = []
            for c in check_result:
                if c and len(c) >= 3:
                    fake_list.append([c[0], c[1], c[2]])
            # print(check_result[0], ' type is: ', type(check_result[0]))
            # result_num = int(check_result[0][0])
            return 1, fake_list
        else:
            return 0, []
    except Exception as exp:
        print('check hashToVersion error:',
              exp, '--------------------------------------------------------------------------------------------------')
        return -1, []


# check issue report repos or not
def get_fake_version(repo_name, r_hash):
    (host, user, password, db_name) = get_db_insert()
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT fake_version FROM fake_version WHERE repo_name='%s' AND r_hash='%s'" % (repo_name, r_hash)
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
            # result_num = int(check_result[0][0])
            return check_result[0][0]
        else:
            return ''
    except Exception as exp:
        print('check hashToVersion error:',
              exp, '--------------------------------------------------------------------------------------------------')
        return ''


# check issue report repos or not
def check_hashToVersion(repo_name, r_hash):
    (host, user, password, db_name) = get_db_insert()
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT r_version FROM hashToVersion WHERE repo_name='%s' AND r_hash='%s' AND (repo_name NOT IN (SELECT " \
          "repo_name FROM fake_version WHERE repo_name='%s' AND r_hash='%s'))" % (repo_name, r_hash, repo_name, r_hash)
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
            # result_num = int(check_result[0][0])
            return 1, check_result[0][0]
        else:
            return 0, ''
    except Exception as exp:
        print('check hashToVersion error:',
              exp, '--------------------------------------------------------------------------------------------------')
        return -1, ''


# 4个检测repo和版本是否存在的方法
# check repo exit or not : 0 can find; 1 repo name wrong; 2 repo version wrong [public-method]
def check_insert_mes(in_repo_name, in_version):
    insert_error = 0
    repo_exit = check_repo_version_exit_web(in_repo_name, in_version)
    # print('check_repo_version_exit_web: ', repo_exit)
    if repo_exit == 0 or repo_exit < 0:
        repo_url = 'https://api.github.com/repos/' + in_repo_name + '/contents?ref=' + in_version
        # print(repo_url)
        headers = get_headers()
        # print(headers)
        try:
            insert_error = 0
            page_detail = get_results(repo_url, headers)
        except Exception as exp:

            # print("Maybe cannot find version: ", exp, '**************************************************')
            repo_url = 'https://api.github.com/repos/' + in_repo_name
            try:
                page_detail = get_results(repo_url, headers)
                insert_error = 2
                # print(in_repo_name, insert_error, 'The repo version name is not correct!')
            except Exception as exp:
                insert_error = 1
                # print(in_repo_name, insert_error, 'The repo name is not correct:', exp, '*************************')
    else:
        insert_error = 0
    # print('check_insert_mes', insert_error)
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
    # print(url)
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


# 使用api：get page detail through repo_name and repo_version [public-method]
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


# 使用api：get dependency manager  [public-method][need update, can only get the latest condition]
def get_dm_msg(repo_name, headers, search_e):
    mod_count = -1
    tool_count = -1
    mod_url_list = []
    tool_url_list = []
    # get go.mod count num
    url_mod = 'https://api.github.com/search/code?q=repo:' + repo_name + '+filename:go.mod'
    # print(url_mod)
    try:
        results_mod = get_results(url_mod, headers)
        mod_count = results_mod['total_count']
        if mod_count > 30:
            for page in range(1, 11):
                url_mod = url_mod + '&page=' + str(page) + '&per_page=100'
                # print(url_mod)
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


# 库查询：new_web_name , 通过其他新的web路径找旧的github的名字，通过个性化网址查github上的网址
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
            # print('This special url have related github url：', check_result[0][0])
            return 1, check_result[0][0]
        else:
            return 0, ''
    except Exception as exp:
        print("1. check new_web_name error:", exp, '-------------------------------------------------------------')
        print(sql)
        return -1, ''


# 库查询：new_web_name，get the new web url， 通过旧的（github上的旧网址）查新的（别的网站上的新网址，个性化网址）
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
        print("2. get new url from ", check_db_name, " error",
              exp, '%%%%%%%%%%%%%')
        print(sql)
        return ''


# 库查询：repo_name_update , get the redirected repo name, 不包括为0的返回项， 旧查新
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
              exp, '%%%%%%%%%%%%%')
        print(sql)
        return ''


# 库查询：repo_name_update , 包括为0的返回项， 旧查新
def check_repo_red_del(old_repo):
    # repo_name_update
    check_db_name = 'repo_name_update'
    (host, user, password, db_name) = get_db_search()
    sql = "SELECT now_repo_name FROM " + check_db_name + " WHERE old_repo_name='%s'" % old_repo
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
              exp, '%%%%%%%%%%%%%%%%%%%%%%%%')
        print(sql)
        return ''


# 库查询：repo_name_update , get the redirected repo name, 不包括为0的返回项， 新查旧
def get_redirect_old_repo(new_repo):
    # repo_name_update
    check_db_name = 'repo_name_update'
    (host, user, password, db_name) = get_db_search()
    sql = "SELECT old_repo_name FROM " + check_db_name + " WHERE now_repo_name='%s'" % new_repo
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
              exp, '%%%%%%%%%%%%%%%%%%%%%%%%')
        print(sql)
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
        # print('insert ', sql, ' successful', old_url, now_url)
        insert_s = insert_s + 1
    except Exception as exp:
        print('insert ', sql, ' error exception is:', exp)
        print('insert ', sql, ' error sql:', sql)
        insert_e = insert_e + 1
        db.rollback()
    db.close()
    return insert_e, insert_s


# 用于诊断问题1
def get_requires_from_mod(mod_url, requires_list, mod_require_list):
    # print('go.mod:', mod_url)
    f = open(mod_url)
    go_mod_content = f.read()
    require_part = go_mod_content.replace('"', '')
    f.close()
    # get all require
    mod_requires = re.findall(r"require\s*\(\n*(.+?)\n*\)", require_part, re.S)
    if mod_requires:
        require_l = mod_requires[0].split('\n')
        for require_r in require_l:
            require_r = require_r.strip().replace('+incompatible', '').replace(' // indirect', '')
            # (not re.findall(r"^[0-9a-zA-Z]+?/[0-9a-zA-Z]+?$", require_r))
            #                 and (not re.findall(r"^[0-9a-zA-Z]+?$", require_r)) and
            if require_r and (not re.findall(r"^//.+?", require_r)) and (require_r not in requires_list):
                requires_list.append(require_r)
                # print(require_r)
    mod_requires = re.findall(r"^require\s+([^(]+?)$", require_part, re.M)
    for require_r in mod_requires:
        require_r = require_r.strip().replace('+incompatible', '').replace(' // indirect', '')
        if require_r and (require_r not in requires_list):
            requires_list.append(require_r)
            # print(require_r)

    for require in requires_list:
        if len(require.split(' ')) >= 2:
            req = [require.split(' ')[0], require.split(' ')[1]]
            if req not in mod_require_list:
                mod_require_list.append(req)

    return requires_list, mod_require_list


# 用于诊断问题2-1  (有indirect是1，没有是0)
def get_req_from_mod(mod_url, ir_list):
    replaces_list = []
    # print('go.mod:', mod_url)
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
            # .replace(' // indirect', '')
            if re.findall(r"// indirect", require_r):
                require_r = require_r.replace('// indirect', '').strip()
                if len(require_r.split(' ')) >= 2:
                    req = [require_r.split(' ')[0], require_r.split(' ')[1], 1]
                    if req not in ir_list:
                        ir_list.append(req)
            else:
                require_r = require_r.strip()
                if len(require_r.split(' ')) >= 2:
                    req = [require_r.split(' ')[0], require_r.split(' ')[1], 0]
                    if req not in ir_list:
                        ir_list.append(req)
    mod_requires = re.findall(r"^require\s+([^(]+?)$", require_part, re.M)
    for require_r in mod_requires:
        require_r = require_r.strip().replace('+incompatible', '')
        if re.findall(r"// indirect", require_r):
            require_r = require_r.replace('// indirect', '').strip()
            if len(require_r.split(' ')) >= 2:
                req = [require_r.split(' ')[0], require_r.split(' ')[1], 1]
                if req not in ir_list:
                    ir_list.append(req)
        else:
            require_r = require_r.strip()
            if len(require_r.split(' ')) >= 2:
                req = [require_r.split(' ')[0], require_r.split(' ')[1], 0]
                if req not in ir_list:
                    ir_list.append(req)
    # get all replace
    mod_replaces = re.findall(r"replace\s*\(\n*(.+?)\n*\)", require_part, re.S)
    if mod_replaces:
        replace_l = mod_replaces[0].split('\n')
        for replace_p in replace_l:
            replace_p = replace_p.strip().replace('+incompatible', '')
            if replace_p and (not re.findall(r"^//.+?", replace_p)):
                replace_rl = re.findall(r"^(.+?)\s", replace_p)
                replace_rr = re.findall(r"=>\s(.+?)$", replace_p)
                if replace_rl and replace_rr and ([replace_rl[0], replace_rr[0]] not in replaces_list):
                    replaces_list.append([replace_rl[0], replace_rr[0]])

    mod_replaces = re.findall(r"^replace\s+([^(]+?)$", require_part, re.M)
    for replace_r in mod_replaces:
        replace_r = replace_r.strip()
        if replace_r:
            replace_rl = re.findall(r"^(.+?)\s", replace_r)
            replace_rr = re.findall(r"=>\s(.+?)$", replace_r)
            if replace_rl and replace_rr and ([replace_rl[0], replace_rr[0]] not in replaces_list):
                replaces_list.append([replace_rl[0], replace_rr[0]])
    return ir_list, replaces_list


def get_mod_require(mod_url, requires_list, replaces_list):
    # print('go.mod:', mod_url)
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
        replace_l = mod_replaces[0].split('\n')
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
                                # print(replace_rr_ind)
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
                            # print(replace_rr_ind)
    return requires_list, replaces_list


# 从.go源文件获取所有依赖项
def get_requires_from_file(file_url, import_list):
    f = open(file_url, 'rb')
    f_content = f.read()
    f_charInfo = chardet.detect(f_content)
    # print(f_charInfo)

    if not f_charInfo['encoding']:
        file_content = f_content.decode('utf-8', 'ignore')
    elif f_charInfo['encoding'] == 'EUC-TW':
        file_content = f_content.decode('utf-8', 'ignore')
    else:
        file_content = f_content.decode(f_charInfo['encoding'], errors='ignore')
    file_import = re.findall(r"import\s*\(\n(.+?)\n\)", file_content, re.S)
    # print(file_import)
    f.close()
    if file_import:
        i_list = file_import[0].split('\n')
        for imp in i_list:
            imp = imp.strip()
            # 排除库函数
            if (not re.findall(r"^//.+?", imp)) and (not re.findall(r"\"[0-9a-zA-Z]+?/[0-9a-zA-Z]+?\"", imp)) and \
                    (not re.findall(r"\"[0-9a-zA-Z]+?\"", imp)):
                if re.findall(r"\"(.+?)\"", imp):
                    import_path = re.findall(r"\"(.+?)\"", imp)[0].strip()
                    # print(import_path)
                    if import_path not in import_list:
                        import_list.append(import_path)
                        # print(import_path)
    return import_list


# 返回有github.com/的网址
def get_github_name(dep_name):
    siv_path = ''
    git_mod_name = ''
    repo_name = ''
    if re.findall(r"^(gopkg.in/.+?)\.v\d", dep_name):
        # gopkg.in/cheggaaa/pb.v1
        repo_name = re.findall(r"^(gopkg.in/.+?)\.v\d", dep_name)[0]
    siv_path = get_imp_siv_path(dep_name)
    nosiv_path = dep_name.replace(siv_path, '')
    if repo_name:
        (r, git_name) = get_github_name_db(repo_name)
        if git_name:
            git_mod_name = git_name
        else:
            insert_new_spec_db(repo_name)
    else:
        if re.findall(r"^([^/]+?/[^/]+?)$", nosiv_path):
            repo_name = re.findall(r"^([^/]+?/[^/]+?)$", nosiv_path)[0]
        elif re.findall(r"^([^/]+?/[^/]+?)/", nosiv_path):
            repo_name = re.findall(r"^([^/]+?/[^/]+?)/", nosiv_path)[0]
        else:
            repo_name = nosiv_path
        (r, git_name) = get_github_name_db(repo_name)

        if git_name:
            git_mod_name = git_name
        else:
            insert_new_spec_db(repo_name)
    return git_mod_name


# make xxx/xxxx/xxx/...  ->  xxx/xxx
def return_repo_name(dep_name):
    dep_name = 'github.com' + dep_name.replace('github.com/', '')
    repo_name = get_git_repo_name(dep_name)
    return repo_name


# 将github.com/.../.../.../... 解析出repo_name
def get_git_repo_name(dep):
    repo_name = ''
    if re.findall(r"^github.com/([^/]+?/[^/]+?)$", dep):
        repo_name = re.findall(r"^github.com/([^/]+?/[^/]+?)$", dep)[0]
    elif re.findall(r"^github.com/([^/]+?/[^/]+?)/", dep):
        repo_name = re.findall(r"^github.com/([^/]+?/[^/]+?)/", dep)[0]
    return repo_name


# 解析得到路径中siv的部分，可能是siv
def get_imp_siv_path(dep_name):
    siv_path = ''
    if re.findall(r"(/v\d+?)$", dep_name):
        siv_path = re.findall(r"(/v\d+?)$", dep_name)[0]
    elif re.findall(r"(\.v\d+?)$", dep_name):
        siv_path = re.findall(r"(\.v\d+?)$", dep_name)[0]
    elif re.findall(r"(/v\d+?)/", dep_name):
        siv_path = re.findall(r"(/v\d+?)/", dep_name)[0]
    elif re.findall(r"(\.v\d+?)/", dep_name):
        siv_path = re.findall(r"(\.v\d+?)/", dep_name)[0]
    return siv_path


# import path 解析得到github上的repo_name
def get_repo_name(dep_name):
    repo_name = ''
    siv_path = get_imp_siv_path(dep_name)
    if re.findall(r"^github.com/", dep_name):
        repo_name = get_git_repo_name(dep_name)
    elif re.findall(r"^go.etcd.io/", dep_name):
        repo_name = dep_name.replace('go.etcd.io/', 'etcd-io/')
        if repo_name != dep_name:
            repo_name = return_repo_name(repo_name)
        else:
            git_name = get_github_name(dep_name)
            # gopkg.in/alecthomas/gometalinter.v2   golang.org/x/sync
            if git_name:
                repo_name = git_name
    elif re.findall(r"^golang.org/x/", dep_name):
        repo_name = dep_name.replace('golang.org/x/', 'golang/')
        if repo_name != dep_name:
            repo_name = return_repo_name(repo_name)
        else:
            git_name = get_github_name(dep_name)
            # gopkg.in/alecthomas/gometalinter.v2   golang.org/x/sync
            if git_name:
                repo_name = git_name
    elif re.findall(r"^gopkg\.in/", dep_name):
        if re.findall(r"^gopkg\.in/([^/]+?/[^/]+?)\.v\d", dep_name):
            repo_name = re.findall(r"^gopkg\.in/([^/]+?/[^/]+?)\.v\d", dep_name)[0]
        else:
            if re.findall(r"^gopkg\.in/([^/]+?/[^/]+?)\.", dep_name):
                repo_name = re.findall(r"^gopkg\.in/([^/]+?/[^/]+?)\.", dep_name)[0]
            else:
                if re.findall(r"^gopkg\.in/([^/]+?/[^/]+?)/", dep_name):
                    repo_name = re.findall(r"^gopkg\.in/([^/]+?/[^/]+?)/", dep_name)[0]
                else:
                    git_name = get_github_name(dep_name)
                    # gopkg.in/alecthomas/gometalinter.v2   golang.org/x/sync
                    if git_name:
                        repo_name = git_name
    else:
        git_name = get_github_name(dep_name)
        # gopkg.in/alecthomas/gometalinter.v2   golang.org/x/sync
        if git_name:
            repo_name = git_name

    repo_name = repo_name.replace('github.com/', '')
    return repo_name, siv_path


def deal_repo_name_version(repo_name, dep_version):
    search_e = 0
    # if dep_name.strip() == 'go.etcd.io/bbolt':
    #     dep_name = 'etcd-io/bbolt'
    repo_name_n = ''
    # (repo_name, siv_path) = get_repo_name(dep_name)
    # ** consider def mecthod **
    insert_error = 1
    repo_version = deal_dep_version(dep_version)
    r = check_insert_mes(repo_name, repo_version)
    if r == 2 and repo_version:
        # print('**get the latest version**')
        (v_name, v_hash, search_e) = get_last_version_or_hashi(repo_name, search_e)
        if v_name or v_hash:
            insert_error = 0
            if v_name:
                repo_version = v_name
            else:
                repo_version = v_hash
        else:
            insert_error = 2
    elif r == 1:
        insert_error = 1
    else:
        insert_error = 0
    if insert_error == 1:
        now_name = get_redirect_repo(repo_name)
        if now_name:
            insert_error = 0
            repo_name_n = repo_name
            repo_name = now_name
            r = check_insert_mes(repo_name, repo_version)
            if r == 2 and repo_version:
                # print('**get the latest version**')
                (v_name, v_hash, search_e) = get_last_version_or_hashi(repo_name, search_e)
                if v_name or v_hash:
                    insert_error = 0
                    if v_name:
                        repo_version = v_name
                    else:
                        repo_version = v_hash
                else:
                    insert_error = 2
        else:
            insert_error = 1
    # print('after deal: ', repo_name, repo_version)
    return insert_error, repo_name, repo_version, repo_name_n


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
            print('Cannot find so insert into new_spec_db:', spec_name)
        except Exception as exp:
            print('insert new_spec_db error exception is:', exp)
            print('insert new_spec_db error sql:', sql)
            db.rollback()
        db.close()


# 处理伪版本， 从中解析得到哈希值
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


def get_all_repo_dir_list(local_url):
    local_list = os.listdir(local_url)
    repo_dir_list = []
    for d in local_list:
        d_path = os.path.join(local_url, d)
        r_path = d_path.replace(local_url, '')
        if os.path.isdir(d_path) and d != '1' and (r_path not in repo_dir_list):
            repo_dir_list.append(r_path)
    return repo_dir_list


# 存储go.mod文件，处理go.mod文件
def l_deal_mod(mod_list, repo_url, mod_dir_name, repo_name):
    mod_dep_list = []
    mod_req_list = []
    mod_rep_list = []
    l_mod_list = []
    count = 0
    mod_cu = ''
    for p in mod_list:
        if re.findall(r"/v\d+?/$", p):
            path_v = re.findall(r"/v(\d+?)/$", p)[0]
            if int(path_v) >= 2:
                # self.v_num = path_v
                mod_cu = p  # have v_dir
                break
    if not mod_cu:
        mod_cu = mod_list[0]
    m_url = repo_url + mod_cu + 'go.mod'
    go_mod_module = ''
    if os.path.isfile(m_url):
        f = open(m_url)
        go_mod_content = f.read()
        module = re.findall(r"^module\s*(.+?)$", go_mod_content, re.M)
        if module:
            go_mod_module = module[0].replace('"', '').strip()
        else:
            go_mod_module = ''
        f.close()
    if not go_mod_module and repo_name:
        go_mod_module = 'github.com/' + repo_name
    for m_url in mod_list:
        count = count + 1
        url = repo_url + m_url + 'go.mod'

        if os.path.isfile(url):
            cd_url = os.path.join(mod_dir_name, str(count) + '_go.mod')
            l_mod_list.append(str(count) + '_' + m_url)
            (mod_req_list, mod_rep_list) = get_mod_require(url, mod_req_list, mod_rep_list)
            shutil.copyfile(url, cd_url)
            # print('+++++++++++++++++++++++++++++++copy： ', url, cd_url, '++++++++++++++++++++++++++++++++++++++++')
            # print('dependencies from go.mod files :', self.mod_req_list, self.mod_rep_list)
    # mod_dep_list
    for m in mod_req_list:
        dep = m.replace('+replace', '').replace('// indirect', '').strip().split(' ')
        if len(dep) > 1:
            dep_version = deal_dep_version(dep[1])
            if re.findall(r"\+replace", m) and dep:
                mod_dep_list.append([dep[0], dep_version, 3])  # replace
            elif re.findall(r"// indirect", m) and dep:
                mod_dep_list.append([dep[0], dep_version, 2])  # dep from old repo
            elif dep:
                mod_dep_list.append([dep[0], dep_version, 1])  # normal
    return mod_dep_list, l_mod_list, go_mod_module


# 存储tool的配置文件
def l_deal_tool(tool_list, repo_url, tool_dir_name):
    l_tool_list = []
    count = 0
    for t_url in tool_list:
        count = count + 1
        url = repo_url + t_url
        t_file_name = ''
        if re.findall(r"/([^/]+?)$", t_url):
            t_file_name = re.findall(r"/([^/]+?)$", t_url)[0]
        elif re.findall(r"\\([^\\]+?)$", t_url):
            t_file_name = re.findall(r"\\([^\\]+?)$", t_url)[0]
        else:
            t_file_name = 'tool.txt'
        cd_url = os.path.join(tool_dir_name, str(count) + '_' + t_file_name)
        l_tool_list.append(str(count) + '_' + t_url)
        shutil.copyfile(url, cd_url)
        # print('+++++++++++++++++++++++++++++++copy： ', url, cd_url, '++++++++++++++++++++++++++++++++++++++++')
    return l_tool_list


def deal_go_files(go_list, repo_url, go_mod_module):
    import_list = []
    for f_url in go_list:
        file_url = repo_url + f_url
        import_list = get_requires_from_file(file_url, import_list)
    delete_list = []
    for i in import_list:
        # if go_mod_module:
        #     delete_list.append(go_mod_module)
        if go_mod_module and re.findall(r"^" + go_mod_module, i):
            delete_list.append(i)
    self_ref = len(delete_list)
    for d in delete_list:
        import_list.remove(d)
    return import_list, self_ref


# direct_repo_list = [git_name, version, befor_name, siv_path, old]  old: 1 是旧路径；0 是新路径
def get_all_direct_dep(import_list):
    search_e = 0
    repo_list = []
    # dep_list = []
    direct_repo_list = []
    # siv_path = ''
    for imp in import_list:
        (repo_name, siv_path) = get_repo_name(imp)
        if repo_name:
            if not re.findall(r"^github.com/", imp):
                web_name = get_new_url('github.com/' + repo_name)
                if [repo_name, web_name, siv_path, 0] not in repo_list:
                    repo_list.append([repo_name, web_name, siv_path, 0])
                # if web_name:
                #     if web_name not in dep_list:
                #         dep_list.append(web_name)
                # else:
                #     dep_list.append(repo_name)
            else:
                now_name = check_repo_red_del(repo_name)
                if not now_name and now_name != '0':
                    if [repo_name, '', siv_path, 0] not in repo_list:
                        repo_list.append([repo_name, '', siv_path, 0])
                        # print('get_all_direct_dep方法:', [repo_name, ''])
                else:
                    if [now_name, repo_name, siv_path, 1] not in repo_list:
                        repo_list.append([now_name, repo_name, siv_path, 1])
                        # print('get_all_direct_dep方法:', [repo_name, ''])
                # if repo_name not in dep_list:
                #     dep_list.append(repo_name)
    for dep in repo_list:
        if len(dep[0].split('/')) >= 2 and dep[0] != '0' and dep[0]:
            (v_name, v_hash, search_e) = get_last_version_or_hashi(dep[0], search_e)
            if v_name or v_hash:
                if v_name:
                    direct_repo_list.append([dep[0], v_name, dep[1], dep[2], dep[3]])
                else:
                    direct_repo_list.append([dep[0], v_hash, dep[1], dep[2], dep[3]])
            else:
                print('*******get last version failed*********************')
                direct_repo_list.append([dep[0], v_hash, dep[1], dep[2], dep[3]])
        else:
            direct_repo_list.append([dep[1], '', dep[0], dep[2], dep[3]])  # 存在已删除或重定向的依赖项
    # print('direct_repo_list:', direct_repo_list)
    return direct_repo_list


# 新机制获取所有的直接依赖项
# direct_repo_list = [git_name, version, befor_name, siv_path, old]  old: 1 是旧路径；0 是新路径
def get_all_direct_depmod(import_list, mod_dep_list):
    search_e = 0
    direct_dep_list = []
    repo_list = []
    for imp in import_list:
        (repo_name, siv_path) = get_repo_name(imp)
        if repo_name:
            if not re.findall(r"^github.com/", imp):
                web_name = get_new_url('github.com/' + repo_name)
                if [repo_name, web_name, siv_path, 0] not in repo_list:
                    repo_list.append([repo_name, web_name, siv_path, 0])
                # if web_name:
                #     if web_name not in dep_list:
                #         dep_list.append(web_name)
                # else:
                #     dep_list.append(repo_name)
            else:
                now_name = check_repo_red_del(repo_name)
                if not now_name and now_name != '0':
                    if [repo_name, '', siv_path, 0] not in repo_list:
                        repo_list.append([repo_name, '', siv_path, 0])
                        # print('get_all_direct_dep方法:', [repo_name, ''])
                else:
                    if [now_name, repo_name, siv_path, 1] not in repo_list:
                        repo_list.append([now_name, repo_name, siv_path, 1])
                        # print('get_all_direct_dep方法:', [repo_name, ''])
                # if repo_name not in dep_list:
                #     dep_list.append(repo_name)
    for dep in repo_list:
        if len(dep[0].split('/')) >= 2 and dep[0] != '0' and dep[0]:
            if dep[1]:
                d_r_name = dep[1]
            else:
                d_r_name = dep[0]
            d_r_path = d_r_name + dep[2]
            d_r_version = ''
            for m_d in mod_dep_list:
                if re.findall(r"^" + d_r_path, m_d[0]) or re.findall(r"^github.com/" + d_r_path, m_d[0]):
                    d_r_version = m_d[1]
                    break
            if d_r_version == '' and dep[2]:
                for m_d in mod_dep_list:
                    if re.findall(r"^" + d_r_name, m_d[0]) or re.findall(r"^github.com/" + d_r_name, m_d[0]):
                        d_r_version = m_d[1]
                        break
            if d_r_version == '':
                (v_name, v_hash, search_e) = get_last_version_or_hashi(dep[0], search_e)
                if v_name or v_hash:
                    if v_name:
                        direct_dep_list.append([dep[0], v_name, dep[1], dep[2], dep[3]])
                    else:
                        direct_dep_list.append([dep[0], v_hash, dep[1], dep[2], dep[3]])
                else:
                    print('*******get last version failed*********************')
                    direct_dep_list.append([dep[0], v_hash, dep[1], dep[2], dep[3]])
            else:
                direct_dep_list.append([dep[0], d_r_version, dep[1], dep[2], dep[3]])
        else:
            direct_dep_list.append([dep[1], '', dep[0], dep[2], dep[3]])  # 存在已删除或重定向的依赖项
    return direct_dep_list


# 解析hero.txt文件，获取信息
def get_msg_hero_go(file_name):
    f = open(file_name)
    file_content = f.read()
    # 写入文件：
    # $mod_num=2$   $tool_num=3$
    # vendor_list
    # l_mod_list  l_tool_list
    # self_ref
    # go_mod_module
    # direct_repo_list
    mod_num = 0
    tool_num = 0
    self_ref = 0
    go_mod_module = ''
    vendor_list = []
    mod_list = []
    tool_list = []
    direct_repo_list = []
    if re.findall(r"\$mod_num=(\d+?)\$", file_content):
        mod_num = int(re.findall(r"\$mod_num=(\d+?)\$", file_content)[0])
    if re.findall(r"\$tool_num=(\d+?)\$", file_content):
        tool_num = int(re.findall(r"\$tool_num=(\d+?)\$", file_content)[0])
    if re.findall(r"\$self_ref=(\d+?)\$", file_content):
        self_ref = int(re.findall(r"\$self_ref=(\d+?)\$", file_content)[0])
    if re.findall(r"\*go_mod_module=(.+?)\*", file_content):
        go_mod_module = re.findall(r"\*go_mod_module=(.+?)\*", file_content)[0]
    if re.findall(r"\$vendor:([^\$]+?)\$", file_content):
        vendor_list = re.findall(r"\$vendor:([^\$]+?)\$", file_content)[0].split(';')
        delete_list = []
        for v in vendor_list:
            if not v:
                delete_list.append(v)

        for d in delete_list:
            vendor_list.remove(d)
    if re.findall(r"\$go.mod:([^\$]+?)\$", file_content):
        l_mod_list = re.findall(r"\$go.mod:([^\$]+?)\$", file_content)[0].split(';')
        for l in l_mod_list:
            if re.findall(r"^\d+?_(.+?)$", l):
                l_mod = re.findall(r"^\d+?_(.+?)$", l)[0]
                if l_mod and (l_mod not in mod_list):
                    mod_list.append(l_mod)
    if re.findall(r"\$tool:([^\$]+?)\$", file_content):
        l_tool_list = re.findall(r"\$tool:([^\$]+?)\$", file_content)[0].split(';')
        for l in l_tool_list:
            if re.findall(r"^\d+?_(.+?)$", l):
                l_tool = re.findall(r"^\d+?_(.+?)$", l)[0]
                if l_tool and (l_tool not in tool_list):
                    tool_list.append(l_tool)
    if re.findall(r"\$direct_dep:([^\$]+?)\$", file_content):
        dd_list = re.findall(r"\$direct_dep:([^\$]+?)\$", file_content)[0].split(';')
        for d in dd_list:
            if d:
                d_i = d.replace('[', '').replace(']', '')
                d_l = d_i.split(',')
                if len(d_l) >= 2 and (d_l not in direct_repo_list):
                    direct_repo_list.append(d_l)
    # print(file_import)
    f.close()
    return mod_num, tool_num, vendor_list, self_ref, mod_list, tool_list, go_mod_module, direct_repo_list


# deal local repo
def deal_local_repo(root_url, local_url, go_list, mod_list, tool_list, vendor_list):
    tool_list_1 = []
    tool_list_2 = []
    dir_list = []
    tool_name_list = get_tool_name_list()
    tool_name_list_2 = get_tool_name_list_2()
    local_list = os.listdir(local_url)
    # print('^^^^^^^^ deal_local_repo   root_url: ', root_url)
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
                if os.path.isfile(v_path) and ((v in tool_name_list) or (v in tool_name_list_2)):
                    tool_list.append(v_r_path)
                elif os.path.isdir(v_path):
                    path_c = PATH()
                    nd_path = path_c.get_deal_local_dir()
                    nd_path_2 = os.path.join(nd_path, '@').strip('@')
                    # nd_path = os.path.join('root', 'www', 'run-tool', 'pkg', '2')
                    if re.findall(r"^" + nd_path + "$", v_path) \
                            or re.findall(r"^" + nd_path_2, v_path):
                        print('+++++++++++++++++++++++++++++++cannot delete： ', v_path)
                    else:
                        shutil.rmtree(v_path)
                        # print('+++++++++++++++delete： ', v_path, '++++++++++++++++++++++++++++++')
                # elif os.path.isfile(v_path):
                #     os.remove(v_path)
        elif os.path.isdir(n_path):  # go file
            # print(n_path)
            if n_path not in dir_list:
                dir_list.append(n_path)
        elif os.path.isfile(n_path):  # go file
            if re.findall(r"\.go$", f):
                if n_r_path not in go_list:
                    go_list.append(n_r_path)
            # print(n_path, n_r_path)
            elif f == 'go.mod':  # go.mod

                # if not n_r_path.replace('go.mod', '').strip():
                #     mod_list.append('/')
                # else:
                mod_path = n_r_path.replace('go.mod', '').strip()
                # print('go.mod files:', n_path, mod_path)
                if mod_path not in mod_list:
                    mod_list.append(mod_path)
                    # print('go.mod files into list:', n_path, mod_path)

            elif f in tool_name_list:  # tool
                # print(n_r_path)
                if n_r_path not in tool_list:
                    tool_list.append(n_r_path)
            elif f in tool_name_list_2:  # tool 2
                # print(n_r_path)
                if n_r_path not in tool_list:
                    tool_list.append(n_r_path)

    for p in dir_list:
        (go_list, mod_list, tool_list, vendor_list) = deal_local_repo(root_url, p, go_list, mod_list, tool_list,
                                                                      vendor_list)
    return go_list, mod_list, tool_list, vendor_list


# direct_repo_list = [git_name, version, befor_name, siv_path, old]  old: 1 是旧路径；0 是新路径
def deal_local_repo_dir(repo_id):
    path_c = PATH()
    pkg_local = path_c.get_pkg_dir()  # pkg
    nd_path = path_c.get_deal_local_dir()  # pkg/2
    deal_repo_path = os.path.join(nd_path, repo_id)  # pkg/2/id
    repo_url = os.path.join(pkg_local, repo_id)  # repo download dir  pkg/id
    file_name = os.path.join(deal_repo_path, 'hero-go.txt')
    mod_dir_name = os.path.join(deal_repo_path, 'mod')
    tool_dir_name = os.path.join(deal_repo_path, 'tool')
    go_list = []
    mod_list = []
    tool_list = []
    vendor_list = []
    if not os.path.exists(file_name):
        if not os.path.exists(deal_repo_path):
            os.makedirs(deal_repo_path)
            os.makedirs(mod_dir_name)
            os.makedirs(tool_dir_name)

        (go_list, mod_list, tool_list, vendor_list) = deal_local_repo(repo_url, repo_url, go_list, mod_list, tool_list,
                                                                      vendor_list)
        mod_num = len(mod_list)  # $mod_num=2$
        tool_num = len(tool_list)  # $tool_num=3$
        if mod_num > 0:
            mod_list.sort(key=lambda m: len(m), reverse=False)
        if tool_num > 0:
            tool_list.sort(key=lambda t: len(t), reverse=False)
        repo_name = ''
        if re.findall(r"/([^/]+?)@+?$", repo_url):
            repo_name = re.findall(r"/([^/]+?)@+?$", repo_url)[0].replace('=', '/')
        elif re.findall(r"\\([^\\]+?)@.+?$", repo_url):
            repo_name = re.findall(r"\\([^\\]+?)@.+?$", repo_url)[0].replace('=', '/')
        go_mod_module = ''
        mod_dep_list = []
        l_mod_list = []
        l_tool_list = []
        if mod_list:
            (mod_dep_list, l_mod_list, go_mod_module) = l_deal_mod(mod_list, repo_url, mod_dir_name, repo_name)
        if tool_list:
            l_tool_list = l_deal_tool(tool_list, repo_url, tool_dir_name)

        if not go_mod_module and repo_name:
            go_mod_module = 'github.com/' + repo_name
        (import_list, self_ref) = deal_go_files(go_list, repo_url, go_mod_module)

        if mod_dep_list and (mod_list[0] == '/' or mod_list == 0):
            direct_repo_list = get_all_direct_depmod(import_list, mod_dep_list)
        else:
            direct_repo_list = get_all_direct_dep(import_list)
        delete_list = []
        this_repo_name = repo_id.split('@')[0].replace('=', '/')
        for dep in direct_repo_list:
            if dep[0] == this_repo_name:
                self_ref = self_ref + 1
                delete_list.append(dep)

        for d in delete_list:
            direct_repo_list.remove(d)
        # 写入文件：
        # $mod_num=2$   $tool_num=3$
        # vendor_list
        # l_mod_list  l_tool_list
        # self_ref
        # go_mod_module
        # direct_repo_list
        if not mod_list:
            go_mod_module = ''
        file_str = '$mod_num=' + str(mod_num) + '$tool_num=' + str(tool_num) + '$self_ref=' + str(self_ref) + '$'
        if go_mod_module:
            file_str = file_str + '*go_mod_module=' + go_mod_module + '*'
        vendor_str = '$vendor:'
        for v in vendor_list:
            vendor_str = vendor_str + v + ';'
        file_str = file_str + vendor_str + '$'
        mod_str = '$go.mod:'
        for lm in l_mod_list:
            mod_str = mod_str + lm + ';'
        file_str = file_str + mod_str + '$'
        tool_str = '$tool:'
        for lt in l_tool_list:
            tool_str = tool_str + lt + ';'
        file_str = file_str + tool_str + '$'
        direct_dep_str = '$direct_dep:'
        for d in direct_repo_list:
            d_str = '['
            for d_s in d:
                if isinstance(d_s, int):
                    d_str = d_str + str(d_s) + ','
                else:
                    d_str = d_str + d_s + ','
            d_str = d_str.strip(',') + ']'
            direct_dep_str = direct_dep_str + d_str + ';'
        file_str = file_str + direct_dep_str + '$'

        file = open(file_name, 'w')
        file.write(file_str)  # msg也就是下面的Hello world!
        file.close()
        # nd_path = deal_path
        nd_path_2 = os.path.join(nd_path, '@').strip('@')
        if re.findall(r"^" + nd_path + "$", repo_url) \
                or re.findall(r"^" + nd_path_2, repo_url):
            print('+++++++++++++++++++++++++++++++cannot delete: ', repo_url)
        else:
            shutil.rmtree(repo_url)
            # print('+++++++++++++++++++++++++++++++delete: ', repo_url, '++++++++++++++++++++++++++++++++++++++++')
    else:
        (mod_num, tool_num, vendor_list, self_ref, mod_list, tool_list, go_mod_module,
         direct_repo_list) = get_msg_hero_go(file_name)
        # os.path.getmtime(file) 获取修改时间
        # [git_name, version, befor_name, siv_path, old]  old: 1 是重定向的repo的旧路径; 0 是新路径; 2 最新为web路径，当前是旧路径
        for dep in direct_repo_list:
            dep[0] = dep[0].replace('github.com/', '')
            if dep[0] == '0' and len(dep) >= 3 and dep[2]:
                dep[0] = dep[2]
                dep[2] = '0'

            if len(dep) < 3:
                siv_path = ''
                now_name = check_repo_red_del(dep[0])
                if now_name and now_name != '0':
                    old_name = dep[0]
                    dep[0] = now_name
                    dep.append(old_name)
                    dep.append(siv_path)
                    dep.append(1)
                elif now_name == '0':
                    dep.append(now_name)
                    dep.append(siv_path)
                    dep.append(1)
                else:
                    dep.append(now_name)
                    dep.append(siv_path)
                    dep.append(0)
                if dep[4] == 0:
                    # 看看是否更新了web地址
                    new_web_name = get_new_url('github.com/' + dep[0])
                    if new_web_name:
                        dep[2] = new_web_name
                        dep[3] = siv_path
                        dep[4] = 2
            elif len(dep) == 3:
                dep[2] = dep[2].replace('github.com/', '')
                if dep[2] and dep[2] != '0':
                    siv_path = ''
                    old_name = get_redirect_old_repo(dep[0])
                    if old_name and old_name != dep[2]:
                        # 看看是否更新了web地址
                        new_web_name = get_new_url('github.com/' + dep[0])
                        if new_web_name:
                            dep[2] = new_web_name
                            dep.append(siv_path)
                            dep.append(0)
                        else:
                            now_name = check_repo_red_del(dep[2])
                            if now_name and now_name != '0':
                                dep[0] = now_name
                                dep.append(siv_path)
                                dep.append(1)
                            elif now_name == '0':
                                dep[0] = dep[2]
                                dep[2] = '0'
                                dep.append(siv_path)
                                dep.append(1)
                            else:
                                dep[0] = dep[2]
                                dep[2] = ''
                                dep.append(siv_path)
                                dep.append(0)
                    elif old_name == dep[2]:
                        dep.append(siv_path)
                        dep.append(1)
                    else:
                        new_web_name = get_new_url('github.com/' + dep[0])
                        if new_web_name:
                            dep[2] = new_web_name
                            dep.append(siv_path)
                            dep.append(0)
                        else:
                            now_name = check_repo_red_del(dep[2])
                            if now_name and now_name != '0':
                                dep[0] = now_name
                                dep.append(siv_path)
                                dep.append(1)
                            elif now_name == '0':
                                dep[0] = dep[2]
                                dep[2] = '0'
                                dep.append(siv_path)
                                dep.append(1)
                            else:
                                dep[0] = dep[2]
                                dep[2] = ''
                                dep.append(siv_path)
                                dep.append(0)

                else:
                    siv_path = ''
                    now_name = check_repo_red_del(dep[0])
                    if now_name:
                        dep[2] = now_name
                        dep.append(siv_path)
                        dep.append(1)
                    else:
                        dep[2] = now_name
                        dep.append(siv_path)
                        dep.append(0)
            else:  # len(dep) >= 4
                dep[2] = dep[2].replace('github.com/', '')
                if dep[2] and dep[2] != '0':
                    old_name = get_redirect_old_repo(dep[0])
                    if old_name and old_name != dep[2]:
                        # 看看是否更新了web地址
                        new_web_name = get_new_url('github.com/' + dep[0])
                        if new_web_name:
                            dep[2] = new_web_name
                            dep[4] = 0
                        else:
                            now_name = check_repo_red_del(dep[2])
                            if now_name and now_name != '0':
                                dep[0] = now_name
                                dep[4] = 1
                            elif now_name == '0':
                                dep[0] = dep[2]
                                dep[2] = '0'
                                dep[4] = 1
                            else:
                                dep[0] = dep[2]
                                dep[2] = ''
                                dep[4] = 0
                    elif old_name == dep[2]:
                        dep[4] = 1
                    else:
                        new_web_name = get_new_url('github.com/' + dep[0])
                        if new_web_name:
                            dep[2] = new_web_name
                            dep[4] = 0
                        else:
                            now_name = check_repo_red_del(dep[2])
                            if now_name and now_name != '0':
                                dep[0] = now_name
                                dep[4] = 1
                            elif now_name == '0':
                                dep[0] = dep[2]
                                dep[2] = '0'
                                dep[4] = 1
                            else:
                                dep[0] = dep[2]
                                dep[2] = ''
                                dep[4] = 0
                else:
                    now_name = check_repo_red_del(dep[0])
                    if now_name:
                        dep[2] = now_name
                        dep[4] = 1
                    else:
                        dep[2] = now_name
                        dep[4] = 0
        if os.path.exists(repo_url):
            # nd_path = deal_path
            nd_path_2 = os.path.join(nd_path, '@').strip('@')
            if re.findall(r"^" + nd_path + "$", repo_url) \
                    or re.findall(r"^" + nd_path_2, repo_url):
                print('+++++++++++++++++++++++++++++++cannot delete: ', repo_url)
            else:
                shutil.rmtree(repo_url)
                # print('+++++++++++++++++++++++++++++++delete: ', repo_url, '++++++++++++++++++++++++++++++++++++++++')
    return mod_num, tool_num, vendor_list, self_ref, mod_list, tool_list, go_mod_module, direct_repo_list


# 通过api获取下游
def get_down_repo(repo_name, mod_path):
    e_mod_users_l = []
    e_tool_users_l = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0'
    }
    tool_str = ''
    tool_name_list = get_tool_name_list()
    for t in tool_name_list:
        tool_str = tool_str + '+filename:' + t
    if 'github.com/' + repo_name == mod_path:
        search_name_list = [repo_name]
    else:
        search_name_list = [repo_name, mod_path]
    for search_name in search_name_list:
        # url_mod = 'https://api.github.com/search/code?q=' + search_name + '+filename:go.mod'
        url_mod = 'https://github.com/search?q=' + search_name.replace('/', '%2F') + '+filename%3Ago.mod&type=Code'

        try:
            response = requests.get(url_mod, headers=headers)
            # print(url_mod)
            content = response.content.decode('utf-8')
            soup = BeautifulSoup(content, "lxml")
            # print(str(soup))
            # f6 link-gray text-mono ml-2 d-none d-lg-inline
            # div_msg = str(soup.find('div', class_='col-12 col-md-9 float-left px-2 pt-3 pt-md-0 codesearch-results'))
            # print(div_msg)
            # div_msg = str(soup.find('div', id_='code_search_results'))
            # div_msg = div_msg.strip('').replace('\n', '')
            # print(div_msg)
            repo_name_l = re.findall(r"<a class=\"link-gray\" [^>]+?>([^<]+?)</a>", str(soup))
            # print(repo_name_l)
        except Exception as exp:
            print("get down mod users error:", exp, "**************************************************")

        url_tool = 'https://github.com/search?q=' + \
                   search_name.replace('/', '%2F') + tool_str.replace(':', '%3A') + '&type=Code'
        # print('url_old', url_tool)
        try:
            response = requests.get(url_mod, headers=headers)
            content = response.content.decode('utf-8')
            soup = BeautifulSoup(content, "lxml")
            # f6 link-gray text-mono ml-2 d-none d-lg-inline
            div_msg = str(soup.find('div', id_='code_search_results'))
            div_msg = div_msg.strip('').replace('\n', '')
            # print(div_msg)
            repo_name_l = re.findall(r"<a class=\"link-gray\" [^>]+?>([^<]+?)</a>", div_msg)
            # print(repo_name_l)
        except Exception as exp:
            print("get down repo error:", exp, "**************************************************")


def get_dr_mod_api(search_name, page):
    url_mod = 'https://api.github.com/search/code?q=' + search_name + '+filename:go.mod&page='
    url_mod = url_mod + str(page) + '&per_page=100&access_token='
    headers = get_headers()
    token = headers['Authorization'].replace('token ', '').strip()
    url_mod = url_mod + token
    results_mod = {}
    try:
        results_mod = get_results(url_mod, headers)
    except Exception as exp:
        print("get mod users error", exp, '***********************************************')
        url_mod = 'https://api.github.com/search/code?q=' + search_name + '+filename:go.mod&page='
        url_mod = url_mod + str(page) + '&per_page=100&access_token='
        headers = get_headers()
        token = headers['Authorization'].replace('token ', '').strip()
        url_mod = url_mod + token
        try:
            results_mod = get_results(url_mod, headers)
        except Exception as exp:
            print("get mod users error2", exp, '***********************************************')
    return results_mod


def get_dr_tool_api(search_name, page, tool_str):
    url_tool = 'https://api.github.com/search/code?q=' + search_name + tool_str
    url_tool = url_tool + '&page=' + page + '&per_page=100&access_token='
    headers = get_headers()
    token = headers['Authorization'].replace('token ', '').strip()
    url_tool = url_tool + token
    results_tool = {}
    try:
        results_tool = get_results(url_tool, headers)
    except Exception as exp:
        print("get tool users error", exp, '***********************************************')
        url_tool = 'https://api.github.com/search/code?q=' + search_name + tool_str
        url_tool = url_tool + '&page=' + page + '&per_page=100&access_token='
        headers = get_headers()
        token = headers['Authorization'].replace('token ', '').strip()
        url_tool = url_tool + token
        try:
            results_tool = get_results(url_tool, headers)
        except Exception as exp:
            print("get tool users error2", exp, '***********************************************')
    return results_tool


def get_down_repo_msg(repo_name, mod_path, r_type):
    tool_name_list = get_tool_name_list()
    mod_down = 0
    mod_down_url = []
    tool_down = 0
    tool_down_url = []
    search_name_list = []
    repo_path = 'github.com/' + repo_name
    tool_str = ''
    mod_repo_list = downDep.get_dm_dr_from_db(repo_name, 1)
    tool_repo_list = downDep.get_dm_dr_from_db(repo_name, 0)
    for t in tool_name_list:
        tool_str = tool_str + '+filename:' + t
    if mod_path and (mod_path not in search_name_list) and r_type != 10:
        search_name_list.append(mod_path)
    if repo_path and (repo_path not in search_name_list):
        search_name_list.append(repo_path)
    # new_web_name = get_new_url(repo_name)
    # if new_web_name and (new_web_name not in search_name_list):
    #     search_name_list.append(new_web_name)
    for search_name in search_name_list:
        search_name = search_name.replace('github.com/', '')
        url_mod = 'https://api.github.com/search/code?q=' + search_name + '+filename:go.mod&page=1&per_page=100&access_token='
        headers = get_headers()
        token = headers['Authorization'].replace('token ', '').strip()
        url_mod = url_mod + token
        results_mod = {}
        down_mod_count = 0
        try:
            results_mod = get_results(url_mod, headers)
            down_mod_count = results_mod['total_count']
            # print('new users count:', down_mod_count)
            if down_mod_count > 0:
                mod_down = mod_down + down_mod_count
                # https://github.com/search?q=etcd-io%2Fetcd+filename%3Ago.mod&type=Code
                url = 'https://github.com/search?q=' + search_name.replace('/', '%2F') + '+filename%3Ago.mod&type=Code'
                mod_down_url.append(url)
        except Exception as exp:
            print("get mod users error", exp, '***********************************************')
            url_mod = 'https://api.github.com/search/code?q=' + search_name + '+filename:go.mod&page=1&per_page=100&access_token='
            headers = get_headers()
            token = headers['Authorization'].replace('token ', '').strip()
            url_mod = url_mod + token
            try:
                results_mod = get_results(url_mod, headers)
                down_mod_count = results_mod['total_count']
                if down_mod_count > 0:
                    mod_down = mod_down + down_mod_count
                    url = 'https://github.com/search?q=' + search_name.replace('/', '%2F') + '+filename%3Ago.mod&type=Code'
                    mod_down_url.append(url)
            except Exception as exp:
                print("get mod users error2", exp, '***********************************************')

        url_tool = 'https://api.github.com/search/code?q=' + search_name + tool_str + '&page=1&per_page=100&access_token='

        headers = get_headers()
        token = headers['Authorization'].replace('token ', '').strip()
        url_tool = url_tool + token
        # print('url_old', url_tool)
        results_tool = {}
        down_tool_count = 0
        try:
            results_tool = get_results(url_tool, headers)
            down_tool_count = results_tool['total_count']
            # print('old users count:', down_old_count)
            if down_tool_count > 0:
                tool_down = tool_down + down_tool_count
                url = 'https://github.com/search?q=' + search_name.replace('/', '%2F') + tool_str.replace(':', '%3A') + '&type=Code'
                tool_down_url.append(url)
                # tool_down_url.append(url_tool)
        except Exception as exp:
            print("get tool users error", exp, '***********************************************')
            url_tool = 'https://api.github.com/search/code?q=' + search_name + tool_str + '&page=1&per_page=100&access_token='
            headers = get_headers()
            token = headers['Authorization'].replace('token ', '').strip()
            url_tool = url_tool + token
            try:
                results_tool = get_results(url_tool, headers)
                down_tool_count = results_tool['total_count']
                if down_tool_count > 0:
                    tool_down = tool_down + down_tool_count
                    url = 'https://github.com/search?q=' + search_name.replace('/', '%2F') + tool_str.replace(':', '%3A') + '&type=Code'
                    tool_down_url.append(url)
            except Exception as exp:
                print("get tool users error2", exp, '***********************************************')

        if results_mod and down_mod_count > 0 and len(mod_repo_list) < 20:
            d_list = results_mod['items']
            for d in d_list:
                d_r = d['repository']
                d_r_name = d_r['full_name']
                if (d_r_name not in mod_repo_list) and d_r_name != repo_name:
                    mod_repo_list.append(d_r_name)
                    downDep.DownDep(d_r_name, 1, repo_name)
                if len(mod_repo_list) >= 20:
                    break
            if len(mod_repo_list) < 20 and down_mod_count >100:
                for p in range(2, down_mod_count/100 + 2):
                    results_mod = get_dr_mod_api(search_name, p)
                    d_list = results_mod['items']
                    for d in d_list:
                        d_r = d['repository']
                        d_r_name = d_r['full_name']
                        if (d_r_name not in mod_repo_list) and d_r_name != repo_name:
                            mod_repo_list.append(d_r_name)
                            downDep.DownDep(d_r_name, 1, repo_name)
                        if len(mod_repo_list) >= 20:
                            break
                    if len(mod_repo_list) >= 20:
                        break
        if results_tool and down_tool_count > 0 and len(tool_repo_list) < 20:
            d_list = results_tool['items']
            for d in d_list:
                d_r = d['repository']
                d_r_name = d_r['full_name']
                if (d_r_name not in tool_repo_list) and d_r_name != repo_name and (d_r_name not in mod_repo_list):
                    tool_repo_list.append(d_r_name)
                    downDep.DownDep(d_r_name, 0, repo_name)
                if len(tool_repo_list) >= 20:
                    break
            if len(tool_repo_list) < 20:
                for p in range(2, int(down_tool_count/100) + 2):
                    results_tool = get_dr_tool_api(search_name, p, tool_str)
                    d_list = results_tool['items']
                    for d in d_list:
                        d_r = d['repository']
                        d_r_name = d_r['full_name']
                        if (d_r_name not in tool_repo_list) and d_r_name != repo_name and (
                                d_r_name not in mod_repo_list):
                            tool_repo_list.append(d_r_name)
                            downDep.DownDep(d_r_name, 0, repo_name)
                        if len(tool_repo_list) >= 20:
                            break
                    if len(tool_repo_list) >= 20:
                        break
    return [mod_down, mod_down_url, tool_down, tool_down_url, mod_repo_list, tool_repo_list]
# 通过api获取下游


def judge_mod_or_tool(mod_num, tool_num, mod_url):
    if mod_num > 0 and (tool_num == 0 or mod_url[0] == '/'):
        # print('*module*')
        return 1
    else:
        # print('*non-module*')
        return 0


def check_report_bug_type_dr(r_id):
    (host, user, password, db_name) = get_db_insert()
    sql = "SELECT bug_type FROM report_bug_type_dr WHERE id='%s'" % r_id
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
            # result_num = int(check_result[0][0])
            return check_result[0][0]
        else:
            return ''
    except Exception as exp:
        print('check report_bug_type_dr error:',
              exp, '--------------------------------------------------------------------------------------------------')
        return ''


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
    # mod_req_list = []
    # mod_rep_list = []
    # mod_dep_list = []  # go.mod, [mod_name，version，type]  type: 1-direct dep; 2-indirect dep; 3-replace
    direct_dep_list = []
    # direct_repo_list = []
    not_exit_list = []  # dep tree
    all_dep_list = []  # no mod
    import_list = []
    self_ref = -1

    # mod_path = ''

    # only update repo_name, v_name, v_siv, v_hash
    def __init__(self, repo_name, insert_version):

        if isinstance(insert_version, str):  # 判断是否为字符串类型
            self.repo_name = repo_name
            self.check_version(insert_version)
            self.v_hash = self.v_hash[0:7]
        elif isinstance(insert_version, list):  # 判断是否为列表
            self.repo_name = repo_name
            self.v_name = insert_version[0]
            self.v_hash = insert_version[1]
            self.v_hash = self.v_hash[0:7]
            self.check_v_name()

        # if self.v_hash == '' and self.v_name:
        #     self.get_hash()

        if self.v_hash:
            self.id = self.repo_name.replace('/', '=') + '@' + self.v_hash
        else:
            self.id = self.repo_name.replace('/', '=') + '@' + self.v_name
        # v_name = self.v_name
        # v_hash = self.v_hash
        # self.init_from_repo_db()
        # if self.v_hash == '' and v_hash:
        #     self.v_hash = v_hash
        #     # self.id = self.repo_name.replace('/', '=') + '@' + self.v_hash
        # elif self.v_name == '' and v_name:
        #     self.v_name = v_name

    def init_repo_dep_db(self, repo_name, repo_version, repo_hash):
        # print(repo_name, repo_version, repo_hash)
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
        if self.v_name and self.v_num == '-2':
            self.get_v_num()  # v_num -- if have no version name, don't need update this
        # print('self.v_name: ', self.v_name)
        self.get_dm_local_new()

    def init_no_starts(self):
        self.mod_url = []
        self.mod_num = 0
        self.tool_num = 0
        self.tool_num = []
        if self.v_name and self.v_num == '-2':
            self.get_v_num()  # v_num -- if have no version name, don't need update this
        self.get_dm_local_new()

    def init_starts(self):
        if self.stars == -1:
            self.get_stars()  # stars, search_e

    def init_for_repo_dep(self):
        if self.stars == -1:
            self.get_stars()  # stars, search_e
        # if self.mod_num == -1 or self.tool_num == -1:
        #     self.mod_url = []
        #     self.mod_num = 0
        #     self.tool_num = 0
        #     self.tool_num = []
        self.get_dm_local_new()  # mod_num, mod_url, tool_num, tool_url

    def init_from_repo_db(self):
        (host, user, password, db_name) = get_db_insert()
        insert_db = get_repo_insert_db()
        sql = "SELECT stars,v_siv,mod_num,mod_siv,mod_name,tool_num,v_dir,v_num," \
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
                # mod_url_str = check_result[0][5].strip('&')
                # if re.findall(r"&", mod_url_str):
                #     self.mod_url = mod_url_str.split('&')
                # else:
                #     self.mod_url = [mod_url_str]
                self.tool_num = check_result[0][5]
                # self.tool_url = check_result[0][7].strip('&').split('&')
                # tool_url_str = check_result[0][7].strip('&')
                # if re.findall(r"&", tool_url_str):
                #     self.tool_url = tool_url_str.split('&')
                # else:
                #     self.tool_url = [tool_url_str]
                self.v_dir = check_result[0][6]
                self.v_num = str(check_result[0][7])
                self.path_match = check_result[0][8]
                self.r_type = check_result[0][9]
                self.v_name = check_result[0][10]
                self.v_hash = check_result[0][11]
                self.id = check_result[0][12]
        except Exception as exp:
            self.search_e = self.search_e + 1
            print("get repos ", self.repo_name, self.v_name, self.v_hash, " from ", insert_db, " error:", exp)

    def init_with_dep_tree(self):
        if not self.direct_dep_list:
            self.init_all()
        self.get_dep_tree_new()

    def download_repo(self):
        if self.v_hash:
            data = [self.repo_name, self.v_hash]
            self.id = self.repo_name.replace('/', '=') + '@' + self.v_hash
        else:
            data = [self.repo_name, self.v_name]
            self.id = self.repo_name.replace('/', '=') + '@' + self.v_name
        down = DOWNLOAD(data)
        down.down_load_unzip()
        if down.download_result == -1:
            # print('download failed:', down.download_result)
            if self.v_hash:
                d_version = self.v_hash
                r = check_insert_mes(self.repo_name, d_version)
                if r == -2 and self.v_name:
                    d_version = self.v_name
                    r = check_insert_mes(self.repo_name, self.v_name)
                if r == -2:
                    (v_name, v_hash, search_e) = get_last_version_or_hashi(self.repo_name, self.search_e)
                    if v_name:
                        self.v_name = v_name
                        self.v_hash = v_hash
                    elif v_hash:
                        self.v_hash = v_hash
                    d_version = self.v_hash
                    if d_version:
                        r = 0
                    # last_commit = get_last_hash(self.repo_name)
                    # if last_commit:
                    #     self.v_hash = last_commit
                    #     d_version = last_commit
                    # (r, page) = check_insert_mes(self.repo_name, last_commit)
                    # if r == 0:
                if r == 0:
                    data = [self.repo_name, d_version]
                    self.id = self.repo_name.replace('/', '=') + '@' + self.v_name
                    down = DOWNLOAD(data)
                    down.down_load_unzip()
        return down.download_result

    def get_dep_tree_new(self):
        layer = 1
        if not self.direct_dep_list:
            self.init_all()
        # print('now is ', layer, ' layer: ', self.repo_name)
        # 存在依赖树不完整的情况，暂时不从数据库读取 ~~~~~~
        # db_data = 0
        # up_list = []
        (db_data, up_list) = repoDep.get_dir_up_from_db(self.repo_name, self.v_name, self.v_hash)

        if db_data > 10 and up_list:
            # u_repo,u_mod,u_version,u_hash
            all_dep_name_l = []
            for dep in up_list:
                if dep[0] not in all_dep_name_l:
                    all_dep_name_l.append(dep[0])
                if dep[3] and [dep[0], dep[3]] not in self.all_dep_list:
                    self.all_dep_list.append([dep[0], dep[3]])
                elif [dep[0], dep[2]] not in self.all_dep_list:
                    self.all_dep_list.append([dep[0], dep[2]])
            for dep in up_list:
                (r_db_data, r_up_list) = repoDep.get_dir_up_from_db(dep[0], dep[2], dep[3])
                if r_db_data <= 0:
                    dep_repo = Repo(dep[0], dep[2])
                    # print('Repo1:', dep[0], dep[2])
                    dep_repo.init_repo_dep_db(dep[0], dep[2], dep[3])
                    dep_repo.init_all()
                    d_sql = dep_repo.insert_repo()
                    if self.mod_num <= 0:
                        self.not_exit_list = []
                        (self.not_exit_list, self.all_dep_list,
                         all_dep_name_l) = dep_repo.get_dep_tree_nomod_new(layer, self.not_exit_list, self.all_dep_list,
                                                                           all_dep_name_l)
                    else:
                        mod_dep_l = []
                        self.not_exit_list = []
                        self.not_exit_list = dep_repo.get_dep_tree_mod_new(layer, mod_dep_l, self.not_exit_list)
        else:

            mod_dep_l = []  # not use for now, to record all deps in go.mod
            all_dep_name_l = []
            # print(self.repo_name, 'go.mod count: ', self.mod_num)
            if self.mod_num == 0:
                # print('using tool')
                direct_list = self.direct_dep_list
                # print('nomod-direct-dep-list', direct_list)
                for dd in direct_list:
                    if dd[0] not in all_dep_name_l:
                        self.all_dep_list.append([dd[0], dd[1]])
                        all_dep_name_l.append(dd[0])
            elif self.mod_num > 0:
                # print('using mod')
                direct_list = self.direct_dep_list
                # print('mod-direct-dep-list', direct_list)
                # print('mod-dep-list-all', self.mod_dep_list)
            else:
                self.init_all()
                if self.mod_num <= 0:
                    # print('using tool')
                    direct_list = self.direct_dep_list
                    for dd in direct_list:
                        if dd[0] not in all_dep_name_l:
                            self.all_dep_list.append([dd[0], dd[1]])
                            all_dep_name_l.append(dd[0])
                else:
                    # print('using mod')
                    direct_list = self.direct_dep_list
                    # print('mod-direct-dep-list', direct_list)
                    # print('mod-dep-list-all', self.mod_dep_list)
            # direct_dep_list
            # print(self.repo_name, 'direct dep build number: ', len(direct_list))
            repo_list = []
            for dep in direct_list:
                # print('build tree: ', dep)
                dep_name = dep[0]
                # 'go.etcd.io/bbolt
                if re.findall(r"go.etcd.io/", dep_name):
                    dep_name = dep_name.replace('go.etcd.io/', 'etcd-io/')
                dep_version = dep[1]
                if dep_name and dep_name != '0':
                    (insert_error, repo_name, repo_version, repo_name_n) = deal_repo_name_version(dep_name, dep_version)
                    # print('get_dep_tree', insert_error)
                    if insert_error == 0:
                        # print('生成Repo对象：', repo_name)
                        dep_repo = Repo(repo_name, repo_version)
                        repo_list.append([repo_name, repo_version])
                        dep_repo.init_all()
                        d_sql = dep_repo.insert_repo()
                        # repoDep
                        d_list = [self.repo_name, self.v_name, self.v_hash]
                        u_list = [dep_repo.repo_name, dep_repo.v_name, dep_repo.v_hash]
                        # print('build repoDep class: ', d_list, u_list)
                        repo_dep_r = repoDep.RepoDep(d_list, u_list)
                        d_mod = judge_mod_or_tool(self.mod_num, self.tool_num, self.mod_url)
                        u_mod = judge_mod_or_tool(dep_repo.mod_num, dep_repo.tool_num, dep_repo.mod_url)
                        d_list = [d_mod, self.stars]
                        u_list = [u_mod, dep_repo.stars]
                        repo_dep_r.init_no_issue(d_list, u_list)
                        repo_dep_r.insert_repo()
                    elif insert_error == -1 and repo_name not in self.not_exit_list:
                        # print(self.not_exit_list, type(self.not_exit_list))
                        self.not_exit_list.append([repo_name, self.repo_name])
            for dep in repo_list:
                dep_repo = Repo(dep[0], dep[1])
                dep_repo.init_all()
                # d_sql = dep_repo.insert_repo()
                (r_db_data, r_up_list) = repoDep.get_dir_up_from_db(dep_repo.repo_name, dep_repo.v_name,
                                                                    dep_repo.v_hash)
                if r_db_data <= 0:
                    if self.mod_num <= 0:
                        (self.not_exit_list, self.all_dep_list,
                         all_dep_name_l) = dep_repo.get_dep_tree_nomod_new(layer, self.not_exit_list, self.all_dep_list,
                                                                           all_dep_name_l)
                    else:
                        self.not_exit_list = dep_repo.get_dep_tree_mod_new(layer, mod_dep_l, self.not_exit_list)

    def get_dep_tree_mod_new(self, layer, mod_dep_list, n_e_list):
        layer = layer - 1
        # print('mod-', layer, 'layer', self.repo_name)
        direct_list = self.direct_dep_list
        # print(self.repo_name, 'go.mod: ', self.mod_num)
        # direct_dep_list
        repo_list = []
        for dep in direct_list:
            dep_name = dep[0]
            dep_version = dep[1]
            if dep_name and dep_name != '0':
                (insert_error, repo_name, repo_version, repo_name_n) = deal_repo_name_version(dep_name, dep_version)
                # print('get_dep_tree', insert_error)
                if insert_error == 0:
                    # print('mod-', layer, 'layer: c-build-Repo object: ', self.repo_name)
                    dep_repo = Repo(repo_name, repo_version)
                    repo_list.append([repo_name, repo_version])
                    dep_repo.init_all()
                    d_sql = dep_repo.insert_repo()
                    # repoDep
                    d_list = [self.repo_name, self.v_name, self.v_hash]
                    u_list = [dep_repo.repo_name, dep_repo.v_name, dep_repo.v_hash]
                    # print('build repoDep class: ', d_list, u_list)
                    repo_dep_r = repoDep.RepoDep(d_list, u_list)
                    d_mod = judge_mod_or_tool(self.mod_num, self.tool_num, self.mod_url)
                    u_mod = judge_mod_or_tool(dep_repo.mod_num, dep_repo.tool_num, dep_repo.mod_url)
                    d_list = [d_mod, self.stars]
                    u_list = [u_mod, dep_repo.stars]
                    repo_dep_r.init_no_issue(d_list, u_list)
                    repo_dep_r.insert_repo()
                elif insert_error == -1 and repo_name not in n_e_list:
                    n_e_list.append(dep)
        if layer > 0:
            for dep in repo_list:
                dep_repo = Repo(dep[0], dep[1])
                dep_repo.init_all()
                d_sql = dep_repo.insert_repo()
                (r_db_data, r_up_list) = repoDep.get_dir_up_from_db(dep_repo.repo_name, dep_repo.v_name,
                                                                    dep_repo.v_hash)
                if r_db_data <= 0:
                    n_e_list = dep_repo.get_dep_tree_mod_new(layer, mod_dep_list, n_e_list)

        return n_e_list

    def get_dep_tree_nomod_new(self, layer, n_e_list, all_dep_list, all_dep_name_l):
        layer = layer - 1

        # 为了保证速度 暂时关闭，之后为了提高使用价值，请再次打开 ~~~~~
        # if self.mod_num <= 0:
        #     direct_list = self.direct_dep_list
        # else:
        #     direct_list = self.get_mdl_last_commit()
        direct_list = self.direct_dep_list

        repo_list = []
        for dep in direct_list:
            if dep[0] not in all_dep_name_l:
                all_dep_name_l.append(dep[0])
                all_dep_list.append([dep[0], dep[1]])
                dep_name = dep[0]
                dep_version = dep[1]
                if dep_name and dep_name != '0':
                    (insert_error, repo_name, repo_version, repo_name_n) = deal_repo_name_version(dep_name, dep_version)
                    # print('get_dep_tree', insert_error)
                    if insert_error == 0:
                        # print('nomod-', layer, 'layer: c-build-Repo object: ', self.repo_name)
                        dep_repo = Repo(repo_name, repo_version)
                        repo_list.append([repo_name, repo_version])
                        dep_repo.init_all()
                        d_sql = dep_repo.insert_repo()
                        # repoDep
                        d_list = [self.repo_name, self.v_name, self.v_hash]
                        u_list = [dep_repo.repo_name, dep_repo.v_name, dep_repo.v_hash]
                        # print('build repoDep class: ', d_list, u_list)
                        repo_dep_r = repoDep.RepoDep(d_list, u_list)
                        d_mod = judge_mod_or_tool(self.mod_num, self.tool_num, self.mod_url)
                        u_mod = judge_mod_or_tool(dep_repo.mod_num, dep_repo.tool_num, dep_repo.mod_url)
                        d_list = [d_mod, self.stars]
                        u_list = [u_mod, dep_repo.stars]
                        repo_dep_r.init_no_issue(d_list, u_list)
                        repo_dep_r.init_from_repo_db()
                    elif insert_error == -1 and repo_name not in n_e_list:
                        n_e_list.append(dep)
        if layer > 0:
            for dep in repo_list:
                dep_repo = Repo(dep[0], dep[1])
                dep_repo.init_all()
                d_sql = dep_repo.insert_repo()
                (r_db_data, r_up_list) = repoDep.get_dir_up_from_db(dep_repo.repo_name, dep_repo.v_name,
                                                                    dep_repo.v_hash)
                if r_db_data <= 0:
                    n_e_list = dep_repo.get_dep_tree_nomod_new(layer, n_e_list, all_dep_list, all_dep_name_l)
        # repo_local = self.get_local_url()
        # check_result = os.path.isdir(repo_local)
        # if check_result:
        #     shutil.rmtree(repo_local)
        return n_e_list, all_dep_list, all_dep_name_l

    # direct_repo_list = [git_name, version, befor_name, siv_path, old]  old: 1 是旧路径；0 是新路径
    def get_mdl_last_commit(self):
        if not self.direct_dep_list:
            self.init_all()
        mdl_lcl = []
        for dep in self.direct_dep_list:
            last_commit = get_last_hash(dep[0].replace('github.com/', ''))
            if last_commit:
                mdl_lcl.append([dep[0], last_commit, dep[2], dep[3], dep[4]])
            else:
                print('*******get last commit failed*********************')
        return mdl_lcl

    # direct_repo_list = [git_name, version, befor_name, siv_path, old]  old: 1 是旧路径；0 是新路径
    def get_mdl_last_version(self):
        if not self.direct_dep_list:
            self.init_all()
        mdl_lvl = []
        for dep in self.direct_dep_list:
            (last_version, semantic) = get_last_version(dep[0].replace('github.com/', ''))
            if last_version:
                mdl_lvl.append([dep[0], last_version, dep[2], dep[3], dep[4]])
            else:
                print('*******get last commit failed*********************')
                last_commit = get_last_hash(dep[0].replace('github.com/', ''))
                if last_commit:
                    mdl_lvl.append([dep[0], last_commit, dep[2], dep[3]])
                else:
                    print('*******get last commit failed*********************')
        return mdl_lvl

    def get_hash(self):
        url = "https://github.com/" + self.repo_name + '/tree/' + self.v_name
        (self.v_hash, self.search_e) = get_hash(url, self.search_e)

    def get_local_url(self):  # get local repo dir
        path_c = PATH()
        path = path_c.path
        repo_local_r = os.path.join('pkg', '2', self.id)  # pkg/kiali=kiali@v1.0.0
        repo_local = os.path.join(path, repo_local_r)
        return repo_local

    def get_dm_local_new(self):
        self.path_match = 3
        self.v_dir = 0
        self.mod_num = 0
        self.tool_num = 0
        self.mod_url = []
        self.tool_url = []
        self.go_list = []
        path_c = PATH()
        pkg_local = path_c.get_pkg_dir()  # pkg
        deal_path = path_c.get_deal_local_dir()  # pkg/2
        deal_repo_path = os.path.join(deal_path, self.id)  # pkg/2/id
        file_name = os.path.join(deal_repo_path, 'hero-go.txt')
        if not os.path.exists(file_name):
            # print('not exists:', file_name)
            d_result = self.download_repo()
        else:
            # print('exists:', file_name)
            d_result = 2
        if d_result != -1:
            root_url = self.get_local_url()
            # print('get_dm_local', root_url, repo_local)
            # mod_num, tool_num, vendor_list, self_ref, mod_list, tool_list, go_mod_module, direct_repo_list
            (self.mod_num, self.tool_num, self.vendor_list, self.self_ref, self.mod_url, self.tool_url,
             self.mod_full_path, self.direct_dep_list) = deal_local_repo_dir(self.id)
            # print('deal_local_repo_dir:', self.mod_num, self.tool_num, self.vendor_list, self.self_ref, self.mod_url,
            #       self.tool_url, self.mod_full_path, self.direct_dep_list)

            # print(self.go_list)
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
            elif self.mod_url:
                mod_cu = self.mod_url[0]
                mod_path = ('github.com/' + self.repo_name + mod_cu + sub_dir).strip('/')
                if sub_dir:
                    mod_path_ns = ('github.com/' + self.repo_name + mod_cu).strip('/')
                else:
                    mod_path_ns = mod_path
            else:
                mod_path = 'github.com/' + self.repo_name
                mod_path_ns = mod_path
            mod_siv_path = ''
            # print('self.mod_full_path:', self.mod_full_path, 'v_num:', self.v_num)
            if self.mod_full_path:
                if re.findall(r"^.+?/(v\d+?)$", self.mod_full_path):
                    mod_siv_path = re.findall(r"^.+?/(v\d+?)$", self.mod_full_path)[0]
                elif re.findall(r"^.+?\.(v\d+?)$", self.mod_full_path):
                    mod_siv_path = re.findall(r"^.+?\.(v\d+?)$", self.mod_full_path)[0]
                if not self.v_name:
                    if mod_siv_path:
                        self.mod_siv = 2
                        self.v_num = mod_siv_path.replace('v', '')
                        sub_dir = 'v' + self.v_num
                        mod_path = mod_path + '/' + sub_dir
                if sub_dir:
                    if re.findall(r"^.+?/" + sub_dir, self.mod_full_path) \
                            or re.findall(r"^.+?\." + sub_dir, self.mod_full_path):
                        self.mod_siv = 2
                        self.mod_name = self.mod_full_path.replace('/' + sub_dir, '').replace('.' + sub_dir, '')
                    else:
                        self.mod_siv = 1
                        self.mod_name = self.mod_full_path
                else:
                    self.mod_siv = 0
                    self.mod_name = self.mod_full_path
                if self.mod_full_path != mod_path and self.mod_full_path != mod_path_ns:
                    repo_name = get_repo_name(self.mod_full_path)
                    if repo_name and repo_name == self.repo_name and repo_name != self.mod_full_path:
                        # self.path_match = 0
                        if int(self.v_num) > 1 and self.mod_siv == 2:
                            self.path_match = 2
                        elif int(self.v_num) > 1 and self.mod_siv == 1:
                            self.path_match = 1
                        elif int(self.v_num) <= 1:
                            self.path_match = 2
                    else:
                        if re.findall(r"^(gopkg\.in/.+?)\.v\d", self.mod_full_path):
                            self.path_match = 2
                        elif re.findall(r"^(k8s\.com/.+?)$", self.mod_full_path):
                            if int(self.v_num) > 1 and self.mod_siv == 2:
                                self.path_match = 2
                            elif int(self.v_num) > 1 and self.mod_siv == 1:
                                self.path_match = 1
                            elif int(self.v_num) <= 1:
                                self.path_match = 2
                        else:
                            self.path_match = 0
                elif self.mod_full_path == mod_path:
                    self.path_match = 2
                elif self.mod_full_path == mod_path_ns and self.mod_full_path != mod_path:
                    self.path_match = 1

            self.r_type = 0
            # print('self.path_match:', self.path_match)
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

    def check_v_name(self):
        if re.findall(r"^v\d+?.\d+?.\d+?-[0-9a-zA-Z.]+?$", self.v_name) or re.findall(r"^v\d+?.\d+?.\d+?$",self.v_name):
            # siv version
            self.v_siv = 2
        else:
            self.v_siv = 1

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

    def get_stars(self):
        repo_name_url = 'https://api.github.com/repos/' + self.repo_name
        # print(repo_name_url)
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

    def check_repo_db(self):
        (host, user, password, db_name) = get_db_insert()
        insert_db = get_repo_insert_db()
        sql = "SELECT stars,v_siv,mod_num,mod_siv,mod_name,tool_num,v_dir,v_num," \
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
        # mod_url_str = ''
        # tool_url_str = ''
        sql = ''
        # for i in self.mod_url:
        #     mod_url_str_c = mod_url_str + i + '&'
        #     if len(mod_url_str_c) >= 480:
        #         break
        #     else:
        #         mod_url_str = mod_url_str + i + '&'
        # for i in self.tool_url:
        #     tool_url_str_c = tool_url_str + i + '&'
        #     if len(tool_url_str_c) >= 480:
        #         break
        #     else:
        #         tool_url_str = tool_url_str + i + '&'
        if check_result < 1:
            insert_sql = "INSERT INTO " + insert_db
            insert_sql = insert_sql + " (id,repo_name,stars,v_name,v_siv,v_hash,mod_num,mod_siv,mod_name," \
                                      "tool_num,v_dir,v_num,path_match,r_type) VALUES ('%s','%s','%d','%s'," \
                                      "'%d','%s','%d','%d','%s','%d','%d','%d','%d'," \
                                      "'%d')" % (self.id, self.repo_name, self.stars, self.v_name, self.v_siv,
                                                 self.v_hash, self.mod_num, self.mod_siv, self.mod_name, self.tool_num,
                                                 self.v_dir, int(self.v_num), self.path_match, self.r_type)
            db = pymysql.connect(host, user, password, db_name)
            # print(insert_sql)
            sql = insert_sql
            try:
                insert_cursor = db.cursor()
                insert_cursor.execute(insert_sql)
                db.commit()
                insert_cursor.close()
                # print('insert ', insert_db, ' successful', self.repo_name, self.v_name, self.v_hash)
                self.insert_s = self.insert_s + 1
            except Exception as exp:
                print('insert ', insert_db, ' error exception is:', exp)
                print('insert ', insert_db, ' error sql:', insert_sql)
                self.insert_e = self.insert_e + 1
                db.rollback()
            db.close()
        else:
            # stars,v_siv,mod_num,mod_siv,mod_name,mod_url,tool_num,tool_url,v_dir,v_num,path_match,r_type
            class_list = [self.stars, self.v_siv, self.mod_num, self.mod_siv, self.mod_name,
                          self.tool_num, self.v_dir, int(self.v_num), self.path_match, self.r_type,
                          self.v_name, self.v_hash, self.id]
            change = 0
            for i in range(0, len(class_list)):
                if result_list[i] != class_list[i] and class_list[i] != '' and class_list[i] != '-2' \
                        and class_list[i] != -1:
                    change = change + 1
            if change > 0:
                update_sql = "UPDATE " + insert_db
                update_sql = update_sql + " SET stars='%d',v_siv='%d',mod_num='%d',mod_siv='%d',mod_name='%s'," \
                                          "tool_num='%d',v_dir='%d',v_num='%d',path_match='%d',r_type='%d'," \
                                          "v_name='%s',v_hash='%s',id='%s' WHERE repo_name='%s' " \
                                          "AND id='%s'" % (self.stars, self.v_siv, self.mod_num, self.mod_siv,
                                                           self.mod_name, self.tool_num, self.v_dir, int(self.v_num),
                                                           self.path_match, self.r_type, self.v_name, self.v_hash,
                                                           self.id, self.repo_name, result_list[12])

                # print(update_sql)
                sql = update_sql
                db = pymysql.connect(host, user, password, db_name)
                try:
                    update_cursor = db.cursor()
                    update_cursor.execute(update_sql)
                    db.commit()
                    update_cursor.close()
                    # print('update ', insert_db, ' successful', self.repo_name, self.v_name, self.v_hash)
                    self.update_s = self.update_s + 1

                except Exception as exp:
                    # print('update ', insert_db, ' error exception is:', exp)
                    # print('update ', insert_db, ' error sql:', update_sql)
                    db.rollback()
                    update_sql = "UPDATE " + insert_db
                    update_sql = update_sql + " SET stars='%d',v_siv='%d',mod_num='%d',mod_siv='%d',mod_name='%s'," \
                                              "tool_num='%d',v_dir='%d',v_num='%d',path_match='%d',r_type='%d'," \
                                              "v_name='%s',v_hash='%s',id='%s' WHERE repo_name='%s' " \
                                              "AND id='%s'" % (self.stars, self.v_siv, self.mod_num, self.mod_siv,
                                                               self.mod_name, self.tool_num, self.v_dir,
                                                               int(self.v_num), self.path_match, self.r_type,
                                                               self.v_name, self.v_hash, result_list[12],
                                                               self.repo_name, result_list[12])
                    db_2 = pymysql.connect(host, user, password, db_name)
                    # print(update_sql)
                    sql = update_sql
                    try:
                        update_cursor = db_2.cursor()
                        update_cursor.execute(update_sql)
                        db_2.commit()
                        update_cursor.close()
                        # print('update ', insert_db, ' successful', self.repo_name, self.v_name, self.v_hash)
                        self.update_s = self.update_s + 1
                    except Exception as exp:
                        print('update ', insert_db, ' error exception is:', exp)
                        print('update ', insert_db, ' error sql:', update_sql)
                        self.update_e = self.update_e + 1
                        db_2.rollback()
                    db_2.close()
                db.close()
        return sql

    def diagnosis_issue_1(self):
        virtual_list = []
        repo_local = self.get_local_url()
        repo_mod_local = os.path.join(repo_local, 'mod')
        local_list = os.listdir(repo_mod_local)
        mod_path_list = []
        for f in local_list:
            mod_path = os.path.join(repo_mod_local, f)
            mod_path_list.append(mod_path)
        # print('mod_path_list: ', mod_path_list)
        requires_list = []
        mod_require_list = []
        for url in mod_path_list:
            (requires_list, mod_require_list) = get_requires_from_mod(url, requires_list, mod_require_list)
        for req in mod_require_list:
            if re.findall(r"/v\d+?$", req[0]):
                mod_path_siv = re.findall(r"/(v\d+?)$", req[0])[0]
                if re.findall(r"^" + mod_path_siv + r".\d+", req[1]):
                    (dep_name, siv_path) = get_repo_name(req[0])
                    # updated_name = get_new_url('github.com/' + dep_name)

                    if dep_name:
                        updated_name = get_redirect_repo(dep_name)
                        if not updated_name:
                            dep_c = Repo(dep_name, req[1])
                            dep_c.init_all()
                            d_sql = dep_c.insert_repo()
                            if dep_c.r_type == 2:
                                virtual_list.append(req[0])
                        elif updated_name:
                            dep_c = Repo(updated_name, req[1])
                            dep_c.init_all()
                            d_sql = dep_c.insert_repo()
                            if dep_c.r_type == 2:
                                virtual_list.append(req[0])
        return virtual_list

    def diagnosis_issue_2(self):
        issue_repo_list = []
        repo_local = self.get_local_url()
        repo_mod_local = os.path.join(repo_local, 'mod')
        local_list = os.listdir(repo_mod_local)
        mod_path_list = []
        for f in local_list:
            mod_path = os.path.join(repo_mod_local, f)
            mod_path_list.append(mod_path)
        # print('mod_path_list: ', mod_path_list)
        ir_list = []
        replace_l = []
        for url in mod_path_list:
            (ir_list, replaces_list) = get_req_from_mod(url, ir_list)
            for replace_r in replaces_list:
                b_name = replace_r[0].split(' ')[0]
                a_name = replace_r[1].split(' ')[0]
                b_siv = get_imp_siv_path(b_name)
                a_siv = get_imp_siv_path(a_name)
                replace_l.append(b_name)
                if not b_siv and a_siv:
                    issue_mes = b_name + '@' + replace_r[0].replace(b_name, '').strip('') + '='
                    issue_mes += a_name + '@' + replace_r[1].replace(a_name, '').replace(' ', '').strip('')
                    if issue_mes:
                        issue_repo_list.append([issue_mes, 2])

        r_id = self.repo_name + self.v_hash

        num_2_1 = 0
        list_2_1 = []
        for req in ir_list:
            print('d2:', req)
            if req[2] == 1:
                list_2_1.append([req[0], req[1]])
            if re.findall(r"github.com/", req[0]):
                if re.findall(r"github.com/([^/]+?/[^/]+?)/.+?$", req[0]):
                    dep_name = re.findall(r"github.com/([^/]+?/[^/]+?)/.+?$", req[0])[0]
                elif re.findall(r"github.com/([^/]+?/[^/]+?)$", req[0]):
                    dep_name = re.findall(r"github.com/([^/]+?/[^/]+?)$", req[0])[0]
                else:
                    dep_name = ''
                if dep_name:
                    new_url = get_new_url(dep_name)
                    re_name = check_repo_red_del(dep_name)
                    if new_url or re_name or re_name == '0':
                        # 有indirect是1，没有是0
                        if (re_name or re_name == '0') and not new_url:
                            if re_name == '0':
                                issue_mes = req[0] + '@0'
                            else:
                                issue_mes = req[0] + '@github.com/' + re_name
                        else:
                            issue_mes = req[0] + '@' + new_url
                        issue_repo_list.append([issue_mes, req[2]])
                        if req[2] == 1:
                            num_2_1 = num_2_1 + 1

        if num_2_1 == 0:
            # bug_type = check_report_bug_type_dr(r_id)
            bug_type = '2-1=2-1'
            if bug_type == '2-1=2-1':
                for req in list_2_1:
                    # 获取依赖项最新版本
                    req_siv = get_imp_siv_path(req[0])
                    if not req_siv and (req not in replace_l):
                        (repo_name, siv_path) = get_repo_name(req[0])
                        if repo_name:
                            l_search_e = 0
                            (v_name, v_hash, search_e) = get_last_version_or_hashi(repo_name, l_search_e)
                            print('d2 get new version:', v_name, v_hash)
                            if v_name or v_hash:
                                issue_mes = ''
                                if v_name:
                                    l_repo = Repo(repo_name, v_name)
                                    l_repo.init_no_starts()
                                    if l_repo.mod_full_path and req != l_repo.mod_full_path:
                                        issue_mes = req[0] + '@' + req[1] + '=' + l_repo.mod_full_path + '@' + v_name
                                else:
                                    l_repo = Repo(repo_name, v_hash)
                                    l_repo.init_no_starts()
                                    if l_repo.mod_full_path and req != l_repo.mod_full_path:
                                        issue_mes = req[0] + '@' + req[1] + '=' + l_repo.mod_full_path + '@' + v_hash
                                if issue_mes:
                                    issue_repo_list.append([issue_mes, 1])

        return issue_repo_list

    def get_e_s_param(self):
        return self.search_e, self.insert_e, self.insert_s, self.update_e, self.update_s



