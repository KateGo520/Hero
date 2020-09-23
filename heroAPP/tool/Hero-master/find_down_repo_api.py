# 通过GitHub的api获取某一repo的下游
import base64
import json
import time
from concurrent.futures.thread import ThreadPoolExecutor
from urllib.request import Request, urlopen
import re
import pymysql
from find_local_use import check_file_detail

from one_check_api.findchange_20200529_api import get_go_mod_detail
from one_check_api.findchange_api import get_version


def get_results(url, headers):
    request = Request(url, headers=headers)
    response = urlopen(request).read()
    result = json.loads(response.decode())
    return result


# 输入repo名，以获得下游信息, 【1】
def get_down_repo(repo_name, host, user, password, db_name, check_date, time_w, insert_e, search_e, check_e, update_e,
                  insert_s, update_s, issue):
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    # 查询数据库是否有
    check_result = 0
    # (check_result, down_list) = check_down_repo(repo_name, check_date, host, user, password, db_name)
    size_list = ['0..99', '100..800', '801..1000', '1001..1200', '1201..1400', '1401..1600', '1601..1800',
                 '1801..2000', '2001..2200', '2201..2400', '2401..2600', '2601..2800', '2801..3000', '3001..3400',
                 '3401..3800', '3801..4200', '4201..4600', '4601..5000', '5001..5600', '5600..6200', '6201..6800',
                 '6801..7400', '7401..8000', '8001..8800', '8801..9600', '9601..14000', '14001..15000', '15001..16000',
                 '16001..18000', '18001..20000', '20001..22000', '22001..26000', '26001..30000', '30001..34000',
                 '34001..40000', '40001..48000', '48001..58000', '58001..70000', '70001..90000', '90001..110000',
                 '110001..140000', '140001..180000', '180001..220000', '220001..260000', '260001..300000',
                 '300001..350000']
    if check_result == 0 or check_result == 1:
        # for l_num in range(2, 3)
        for size in size_list:
            # 41,101
            for page_num in range(1, 11):
                url = 'https://api.github.com/search/code?q=' + repo_name + '+language:go+size:%s+extension:go&' \
                      'page=%s&per_page=100' % (size, page_num)  # size_list[l_num]
                print(url)
                print('size: ', size, page_num)  # size_list[l_num]
                try:
                    results = get_results(url, headers)
                    items = results['items']
                    if items:
                        c = 0  # 计数器
                        for i in items:
                            # i_filename = i['name']  # 存：文件名字
                            i_path = i['path']  # 存：文件相对路径
                            i_repo = i['repository']  # 存：forks数量
                            i_reponame = i_repo['full_name']  # 存：存储库大小
                            i_fileurl = i['git_url']  # 获取版本信息api
                            c = c + 1
                            print('---------------------------------------------------------------------------------')
                            print('【', c, '】: ', i_reponame, i_path)
                            print('---------------------------------------------------------------------------------')
                            time.sleep(time_w)
                            (r_check, issue) = check_file_detail(repo_name, i_fileurl, headers, issue)
                            if r_check == 1:
                                (check_e, insert_e, update_e, insert_s,
                                 update_s) = insert_repo_depend(check_date, repo_name, i_reponame, i_path, i_fileurl,
                                                                host, user, password, db_name, check_e, insert_e,
                                                                update_e, insert_s, update_s)
                    else:
                        break
                except Exception as exp:
                    print("get search code main page error", exp)
                    search_e = search_e + 1
                print('----------------------------------------------------------------------------------------------'
                      '--------------------------------------------------------------------------------------------')
        # (r_down, down_list) = get_down_list(repo_name)
        # if r_down == 0:
        #     print('暂时没有找到下游repos')
        # elif r_down == -1:
        #     print('读取repo_depend失败')
        print('*******************************************************************************************************'
              '***********************************************************************************************')
        # return down_list
    # elif check_result == 2:
    #     print('********************************************')
    #     return down_list
    else:
        print('please check the problem！')
        print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
        # return []
    return insert_e, search_e, check_e, update_e, insert_s, update_s, issue


# 输入repo名查重，数据库repo_depend
def check_down_repo(repo_name, check_time, host, user, password, db_name):
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
        print("check repo_depend error:", exp)
        return -1, []


# 从数据库读取某一repo的下游列表
def get_down_list(repo_name, repo_type, host, user, password, db_name, search_e, issue):
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT distinct d_repo FROM repo_depend WHERE u_repo='%s'" % repo_name
    result_list = []
    return_list = []
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
            print('数据库表repo_depend中读取结果：', result_list)
            if repo_type >= 0:
                # 获取下游旧机制存储库
                for repo in result_list:
                    time.sleep(1)
                    (repo_detail, search_e, issue) = get_onepage_info(repo, search_e, issue)
                    # 获取下游旧机制存储库
                    if repo_type == 0 and repo_detail[1] == 0:
                        return_list.append(repo_detail)
                    elif repo_type == 1 and repo_detail[1] > 0:
                        return_list.append(repo_detail)
                    elif repo_type == 2:
                        return_list.append(repo_detail)
            else:
                return_list = result_list
            return 1, return_list
        else:
            return 0, []
    except Exception as exp:
        print("read repo_depend error:", exp)
        return -1, []


def get_onepage_info(name, search_e, issue):
    repo_detail = []
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    one_page_url = 'https://api.github.com/repos/' + name
    try:
        one_page_results = get_results(one_page_url, headers)
        item_fullname = one_page_results['full_name']  # 存：存储库完整名字
        item_stars = one_page_results['stargazers_count']  # 存：标星数量
        item_forks = one_page_results['forks_count']  # 存：forks数量
        # item_size = one_page_results['size']  # 存：存储库大小
        item_created = one_page_results['created_at']  # 存：存储创建时间
        item_updated = one_page_results['updated_at']  # 存：数据库更新时间
        releases_url = one_page_results['releases_url']  # 获取版本信息api
        (v_name, semantic) = get_version(releases_url, headers)
        # (go_mod,version_dir,version_number,path_match) = get_detailpage(item_fullname, v_name, semantic, headers)
        (go_mod_module, version_number, path_match, go_mod, main_version, go_mod_url, version_dir,
         issue) = get_go_mod_detail(item_fullname, v_name, semantic, headers, issue)
        # repo_detail.append(name)
        repo_detail = [name, go_mod, item_stars, item_forks, item_created, item_updated]
        # print(item_fullname, ": ", item_stars, item_forks, "【V】", v_name, go_mod, go_mod_module,
        #       version_dir, version_number, path_match)
        # insert_db = 'github_go_repos_20200529'

    except Exception as exp:
        print("get search ", name, " error", ':', exp)
        search_e = search_e + 1
    return repo_detail, search_e, issue


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
        print("check repo_impact error:", exp)
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
            print('insert repo_depend error exception is:', exp)
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
            print('update repo_impact error exception is:', exp)
            print('update repo_impact error sql:', update_sql)
            update_e = update_e + 1
            # 发生错误时回滚
            db.rollback()
        db.close()
    else:
        print('check repo_depend error', u_repo, '->', d_repo, '@', i_path)
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
        print("check repo_impact error:", exp)
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
    check_date = int(time.strftime('%Y%m%d', time.localtime(time.time())))
    time_s = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    # headers = {'User-Agent': 'Mozilla/5.0',
    #            'Content-Type': 'application/json',
    #            'Accept': 'application/json',
    #            'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    fullname = 'gohugoio/hugo'
    (insert_error, search_error, check_error, update_error, insert_success, update_success,
     issue_l) = get_down_repo(fullname, host, user, password, db_name, check_date, time_w, insert_error, search_error,
                              check_error, update_error, insert_success, update_success, issue_l)
    repo_type = 0
    # repo_name, repo_type, host, user, password, db_name, search_e, issue
    (r_down, down_list) = get_down_list(fullname, repo_type, host, user, password, db_name, search_error, issue_l)
    # repo_type 0：旧机制；1：新机制 2：两个都要; -1:不获取详细信息
    if r_down == 0:
        print('暂时没有找到下游repos')
    elif r_down == -1:
        print('读取repo_depend失败')
    else:
        print(down_list)

    # # 直接依赖检测
    # # 已读取完毕，开始检测某一项是否在该repo的下游
    # d_list = ['istio/glog', 'istio/klog', 'istio/viper', 'docker/engine']
    # for d_repo in d_list:
    #     (r_check, check_list) = check_requre(fullname, d_repo, host, user, password, db_name)
    #     print(d_repo, '【', r_check, '】 ', check_list)

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
