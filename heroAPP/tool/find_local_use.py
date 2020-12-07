# 通过GitHub的api获取某一repo的下游
import base64
import time
from concurrent.futures.thread import ThreadPoolExecutor
import re
from . import repo


def check_file_detail(upname, i_fileurl, headers, issue):
    try:
        file_detail = repo.get_results(i_fileurl, headers)
        go_mod_content = base64.b64decode(file_detail['content'])
        # 检查import语句中是否有该repo
        file_import = re.findall(r"import\s*\(\n*(.+?)\n*\)", go_mod_content.decode(), re.S)
        repo_count = 0
        if file_import:
            imports = file_import[0]  # 所有依赖项
            file_import = re.findall(r"^[^/]*" + upname, imports, re.M)
            if file_import:
                # print('检测', upname, '被import的次数', len(file_import))
                repo_count = repo_count + len(file_import)
            # imports_list = imports.split('\n')
            # for imp in imports_list:
            #     # print(imp)
            #     if re.findall(r"\"(.+?)\"", imp):
            #         import_path = re.findall(r"\"(.+?)\"", imp)[0].replace(' ', '') + ' '
            #         imp_mod = re.findall(r"(github\.com/[^/]+?/[^/]+?)/.+?", import_path)
            #         if imp_mod:
            #             imp_mod_name = imp_mod[0].replace('github.com/', '').replace(' ', '')
            #         else:
            #             imp_mod_name = import_path.replace('github.com/', '').replace(' ', '')
            #         if imp_mod_name == upname:
            #             repo_count = repo_count + 1
        file_import = re.findall(r"^import\s+[a-z.]*" + upname, go_mod_content.decode().replace('"', ''), re.M)
        if file_import:
            repo_count = repo_count + 1
        if repo_count:
            return 1, issue
        else:
            return 0, issue
    except Exception as exp:
        print("When find detail page: get search error", exp, '*******************************************************'
                                                              '*******************************************************')
        issue = issue + '<' + 'get_file_detail:' + upname + '@' + i_fileurl + '>'
        return -1, issue


# 输入repo名，以获得下游信息 [后期也可以改成本地]
def get_local_use(reponame, upname, b_type, time_w, issue):
    headers = {'User-Agent': 'Mozilla/5.0',
               'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    # 查询数据库是否有
    # (check_result, down_list) = check_down_repo(repo_name, check_time)
    # url = 'https://api.github.com/' + reponame + '/search/code?q=' + upname + \
    #       '+extension:go&page=1&per_page=10'
    url = 'https://api.github.com/search/code?q="' + upname + \
          '"+repo:' + reponame + '+language:go+extension:go&page=1&per_page=10'
    # print(url)
    try:
        results = repo.get_results(url, headers)
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
                time.sleep(time_w)
                (r_check, issue) = check_file_detail(upname, i_fileurl, headers, issue)
                if r_check == 1:
                    r = r + 1
            if r:
                return r, issue
            else:
                return 0, issue
        else:
            return 0, issue
    except Exception as exp:
        print("get search repo local use error", exp)
        issue = issue + '<' + 'get_local_use:' + reponame + '~' + upname + '>'
        return -1, issue


# 输入repo名以及版本名以获得


def main():
    issue_l = ''
    # check_date = int(time.strftime('%Y%m%d', time.localtime(time.time())))
    time_w = 1
    time_s = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    # headers = {'User-Agent': 'Mozilla/5.0',
    #            'Content-Type': 'application/json',
    #            'Accept': 'application/json',
    #            'Authorization': 'token ad418c5441a67ad8b2c95188e131876c6a1187fe'}
    reponame = 'containous/traefik'
    upname = 'Masterminds/sprig'
    b_type = '2-1'
    # reponame, upname, b_type, check_time, time_w, search_e, issue
    (result, issue_l) = get_local_use(reponame, upname, b_type, time_w, issue_l)
    print(result)
    print('other problem: ', issue_l)
    time_e = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    print(time_s, '->', time_e)


if __name__ == '__main__':

    # host = 'localhost'
    # password = 'ella1996'
    # db_name = 'github_go_repos'
    user = 'root'
    host = '47.254.86.255'
    password = 'Ella1996'
    db_name = 'githubspider'
    # 声明线程池
    executor = ThreadPoolExecutor(6)
    main()
