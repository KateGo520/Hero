# 部分更新 新机制的bug 的表
import base64
import json
import re
import time
from concurrent.futures.thread import ThreadPoolExecutor
from urllib.request import Request, urlopen
import pymysql
from findbug_onenewcheck_api import get_results, get_detail_page, update_new_bug
from findchange_api import get_version


# 获取主页的项目信息
def get_main_page_info(url, headers, host, user, password, db_name, check_date, search_e, insert_e, check_e, update_e,
                       insert_s, update_s, issue, time_w):
    try:
        results = get_results(url, headers)
        items = results['items']
        c = 0  # 计数器
        for i in items:
            item_fullname = i['full_name']  # 存：存储库完整名字
            item_stars = i['stargazers_count']  # 存：标星数量
            item_forks = i['forks_count']  # 存：forks数量
            item_updated = i['updated_at']  # 存：数据库更新时间
            releases_url = i['releases_url']  # 获取版本信息api
            c = c + 1
            (v_name, semantic) = get_version(releases_url, headers)
            print(c, ':', item_fullname, "【V】", v_name, '#################################################'
                                                        '############################################')

            (insert_e, check_e, update_e, insert_s, update_s,
             issue) = get_detail_page(item_fullname, v_name, semantic, headers, item_stars, item_forks, item_updated,
                                      host, user, password, db_name, check_date, insert_e, check_e, update_e,
                                      insert_s, update_s, issue, time_w)

    except Exception as exp:
        print("get search error", exp)
        search_e = search_e + 1
    print('-----------------------------------------------------------------------------------------------------------')
    return search_e, insert_e, check_e, update_e, insert_s, update_s, issue


# 【从github上】获取搜索主页，使用API
def get_main_page(host, user, password, db_name, check_date, search_e, insert_e, check_e, update_e, insert_s, update_s,
                  issue, time_w):
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    part = 1
    if part == 1:
        # 141..204
        list_1 = ['1420..67200', '800..1419', '430..800', '280..429', '205..279', '155..204', '141..154', '113..140',
                  '92..112', '78..91', '67..77', '58..66', '51..57', '45..50', '41..44', '37..40', '34..36', '31..33',
                  '29..30', '27..28', '25..26', '23..24', '22', '21', '20', '19', '18', '17', '16']
        # 获取star数为16--67200
        # 0,28  14
        for l1_num in range(0, 1):
            # 1,11  100
            # list_e = [3, 10]
            for page_num in range(21, 101):
                url_1 = 'https://api.github.com/search/repositories?q=language:go+stars:%s&' \
                        'sort=stars&page=%s&per_page=10' \
                        % (list_1[l1_num], page_num)
                print(list_1[l1_num], page_num)
                (search_e, insert_e, check_e, update_e, insert_s, update_s,
                 issue) = get_main_page_info(url_1, headers, host, user, password, db_name, check_date, search_e,
                                             insert_e, check_e, update_e, insert_s, update_s, issue, time_w)
    return search_e, insert_e, check_e, update_e, insert_s, update_s, issue


# 更新存储库中已经检测过的repo
def get_impact_db_repo_number(check_date, host, user, password, db_name, insert_e, search_e, check_e, update_e,
                              insert_s, update_s, issue, time_w):
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    # 查询repo_impact存储库，返回所有有问题的且为新机制用户的repo列表
    sql = "SELECT id,full_name FROM repo_impact " \
          "WHERE id<20200323000000 AND gomod=1 order by id DESC"
    # id>20200301000000 AND
    # 已更新的新机制有bug：WHERE id>20200301000000 AND gomod=1 AND (old_impact=1 OR new_impact=1)
    # 已更新的新机制无bug：WHERE id>20200301000000 AND gomod=1 AND (old_impact=0 AND new_impact=0)
    try:
        # 执行sql语句
        db_check = pymysql.connect(host, user, password, db_name)
        check_cursor = db_check.cursor()
        check_cursor.execute(sql)
        check_result = check_cursor.fetchall()
        check_cursor.close()
        db_check.close()
        count = 0
        for check_repo in check_result:
            print(check_repo[0], check_repo[1])
            # update_new_bug(check_repo[1])
            (insert_er, search_er, check_er, update_er, insert_s, update_s,
             issue) = update_new_bug(check_repo[1], check_date, host, user, password, db_name, insert_e, search_e,
                                     check_e, update_e, insert_s, update_s, issue, time_w)
            count = count + 1
        print(count)
    except Exception as exp:
        print("check repo_impact error:", exp)
    return insert_e, search_e, check_e, update_e, insert_s, update_s, issue


def main():
    insert_e = 0
    search_e = 0
    check_e = 0
    update_e = 0
    insert_s = 0
    update_s = 0
    issue_l = ''
    time_w = 3
    user = 'root'
    host = '47.254.86.255'
    password = 'Ella1996'
    db_name = 'githubspider'
    time_s = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    check_date = int(time.strftime('%Y%m%d', time.localtime(time.time())))
    # (insert_e, search_e, check_e, update_e, insert_s, update_s,
    #  issue_l) = get_impact_db_repo_number(check_date, host, user, password, db_name, insert_e, search_e, check_e,
    #                                       update_e, insert_s, update_s, issue_l, time_w)
    (search_e, insert_e, check_e, update_e, insert_s, update_s,
     issue) = get_main_page(host, user, password, db_name, check_date, search_e, insert_e, check_e, update_e, insert_s,
                            update_s, issue_l, time_w)
    print('searchError', search_e, 'insertError', insert_e, 'checkError', check_e,
          'updateError', update_e)
    print('insert successfully:', insert_s)
    print('update successfully:', update_s)
    print('other issues:', issue_l)
    time_e = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    print(time_s, '->', time_e)


if __name__ == '__main__':
    # 声明线程池
    executor = ThreadPoolExecutor(6)
    main()
