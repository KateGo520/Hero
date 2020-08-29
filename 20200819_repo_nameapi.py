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


# 获取主页的项目信息
def get_mainpage_info(url, headers, host, user, password, db_name, search_e, insert_e, check_e, update_e, insert_s,
                      update_s, time_w, issue, insert_db):
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
            c = c + 1
            print(c, ": ", item_fullname, item_stars, item_forks, item_size)
            (insert_e, check_e, update_e, insert_s,
             update_s) = insert_info(item_fullname, item_stars, item_forks, item_size, item_created,
                                     host, user, password, db_name, insert_e, check_e, update_e,
                                     insert_s, update_s, insert_db)
    except Exception as exp:
        print("get search error", exp)
        search_e = search_e + 1
    print('--------------------------------------------------------------')
    return search_e, insert_e, check_e, update_e, insert_s, update_s, issue


def get_onepage_info(name, host, user, password, db_name, search_e, insert_e, check_e, update_e, insert_s,
                     update_s, time_w, issue, insert_db):
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    one_page_url = 'https://api.github.com/repos/' + name
    try:
        i = get_results(one_page_url, headers)
        item_fullname = i['full_name']  # 存：存储库完整名字
        item_stars = i['stargazers_count']  # 存：标星数量
        item_forks = i['forks_count']  # 存：forks数量
        item_size = i['size']  # 存：存储库大小
        item_created = i['created_at']  # 存：存储创建时间
        print(item_fullname, ": ", item_stars, item_forks, item_size)
        (insert_e, check_e, update_e, insert_s,
         update_s) = insert_info(item_fullname, item_stars, item_forks, item_size, item_created,
                                 host, user, password, db_name, insert_e, check_e, update_e,
                                 insert_s, update_s, insert_db)

    except Exception as exp:
        print("get search ", insert_db, " error", name, ':', exp)
        search_e = search_e + 1
    return search_e, insert_e, check_e, update_e, insert_s, update_s, issue


# 获取搜索主页，使用API
def get_mainpage(part, host, user, password, db_name, search_e, insert_e, check_e, update_e, insert_s, update_s,
                 time_w, issue, insert_db):
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    # item_commit = 'https://api.github.com/repos/moby/moby/commits'
    # item_issues = 'https://api.github.com/repos/moby/moby/issues'
    # item_updated = get_commit_time(item_commit, headers)
    # item_issues_count = get_issue_count(item_issues, headers)
    if part == 1:
        # 141..204
        list_1 = ['1700..68000', '1000..1699', '630..999', '520..629', '408..519', '290..407', '255..289', '200..254',
                  '155..199', '130..154', '113..129', '98..112', '86..97', '76..85', '67..75', '60..66', '56..59',
                  '51..55', '46..50', '42..45', '39..41', '36..38', '34..36', '32..33', '30..31', '28..29', '26..27',
                  '25', '24', '23', '22', '21', '20', '19', '18', '17']
        # 获取star数为16--67200
        # 0,28  12  xiayige '36..38'
        for l1_num in range(1, 21):
            # (0, 11) 1-10
            # (6, 7)  1   (7, 8) 1-10  (10, 11)  1-10 (12, 13) 1-10  (14..15) 1-10 (16..22)
            # 1,11  100
            # list_e = [3, 10]
            for page_num in range(1, 101):
                # url_1 = 'https://api.github.com/search/repositories?q=language:go+stars:1559..68000&sort=stars&' \
                #         'page=1&per_page=10'
                url_1 = 'https://api.github.com/search/repositories?q=language:go+stars:%s&' \
                        'sort=stars&page=%s&per_page=10' % (list_1[l1_num], page_num)
                print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
                      '+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                print(list_1[l1_num], page_num)
                # print(list_1[l1_num], page_num)
                try:
                    print(url_1)
                    results = get_results(url_1, headers)
                    if page_num == 1:
                        items_count = results['total_count']
                        print(list_1[l1_num], ':', items_count)
                    items = results['items']
                    if items:
                        c = 0  # 计数器
                        for i in items:
                            item_fullname = i['full_name']  # 存：存储库完整名字
                            item_stars = i['stargazers_count']  # 存：标星数量
                            item_forks = i['forks_count']  # 存：forks数量
                            item_size = i['size']  # 存：存储库大小
                            item_created = i['created_at']  # 存：存储创建时间
                            c = c + 1

                            print(c, ": ", item_fullname, item_stars, item_forks, item_size)
                            (insert_e, check_e, update_e, insert_s,
                             update_s) = insert_info(item_fullname, item_stars, item_forks, item_size, item_created,
                                                     host, user, password, db_name, insert_e, check_e, update_e,
                                                     insert_s, update_s, insert_db)
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
    if part == 0:
        (need_check_list, issue) = get_need_check_list(host, user, password, db_name, headers, issue)
        for new_name in need_check_list:
            (search_e, insert_e, check_e, update_e, insert_s, update_s,
             issue) = get_onepage_info(new_name, host, user, password, db_name, search_e, insert_e, check_e, update_e,
                                       insert_s, update_s, time_w, issue, insert_db)

    return search_e, insert_e, check_e, update_e, insert_s, update_s, issue


def get_need_check_list(host, user, password, db_name, headers, issue):
    check_db_name = 'repo_name_update'
    need_check_list = []
    sql = "SELECT now_repo_name FROM " + check_db_name \
          + " WHERE now_repo_name!='0'"
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


# 插入数据库的方法
def insert_info(name, stars, forks, size, c_time, host, user, password, db_name, insert_e, check_e, update_e,
                insert_s, update_s, insert_db):
    check_result = check_name(name, host, user, password, db_name, insert_db)
    if check_result == 0:
        # check_result == 0 , 未插入
        insert_sql = "INSERT INTO " + insert_db + " (full_name,stars,forks,r_size,created_time) VALUES ('%s','%d'," \
                                                  "'%d','%d','%s')" % (name, stars, forks, size, c_time)
        db = pymysql.connect(host, user, password, db_name)
        try:
            insert_cursor = db.cursor()
            # 执行sql语句
            insert_cursor.execute(insert_sql)
            db.commit()
            insert_cursor.close()
            print('insert ', insert_db, ' successful', name)
            insert_s = insert_s + 1
        except Exception as exp:
            print('insert ', insert_db, ' error exception is:', exp)
            print('insert ', insert_db, ' error sql:', insert_sql)
            insert_e = insert_e + 1
            # 发生错误时回滚
            db.rollback()
        db.close()
    # elif check_result == 1:
    #     # 已经有了该信息
    #     print('already insert in ', insert_db)
    elif check_result >= 1:
        # 有该存储库但信息不同
        # if check_result == 3:
        #     result_list
        #     time_num = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        #     time_num = int(time_num)
        #     change_list = [time_num, name, result_list[0], result_list[1], up_time, v_name, result_list[3], r_type]
        #     (insert_e, insert_s) = insert_repo_change(change_list, insert_e, insert_s, host, user, password, db_name)

        update_sql = "UPDATE " + insert_db + " SET stars='%d',forks='%d',r_size='%d',created_time='%s' " \
                                             "WHERE full_name='%s'" % (stars, forks, size, c_time, name)
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
        print('check ', insert_db, ' error', name)
        check_e = check_e + 1
    return insert_e, check_e, update_e, insert_s, update_s


# 查重
def check_name(r_name, host, user, password, db_name, insert_db):
    check_num = -1
    # 查询该存储库是否存在于数据库中，返回查询数量
    sql = "SELECT count(*) FROM " + insert_db + " WHERE full_name = '%s'" % r_name
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
        print("check " + insert_db + " result:", check_result)
        return check_num
    except Exception as exp:
        print("check repos name", r_name, " from ", insert_db, " error:", exp)
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

    (search_e, insert_e, check_e, update_e, insert_s, update_s,
     issue_l) = get_mainpage(part, host, user, password, db_name, search_e, insert_e, check_e, update_e, insert_s,
                             update_s, time_w, issue_l, insert_db)
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