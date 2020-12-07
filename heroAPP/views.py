from django.shortcuts import render
from django.http import JsonResponse
import os
import xlrd
import json
from .tool.repo import check_insert_mes, get_down_repo_msg, get_repo_now_name
from .tool.issue import ISSUE
from .tool.repoDep import get_all_up, get_all_down

# Create your views here.
BASE_URL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE = 'data_issues_report.xlsx'
FILE_Study = 'EmpiricalStudy.xlsx'
FILE_GT = 'BenchmarkDataset.xlsx'


def index(request):
    return render(request, "index.html")


def data(request):
    data = []
    filename = os.path.join(BASE_URL, 'static', 'files', FILE)
    temp_excel = xlrd.open_workbook(filename)
    temp_sheet = temp_excel.sheet_by_index(0)
    row = 1  # 开始的行
    col = 7  # 结束的列
    for i in range(row, temp_sheet.nrows):
        temp = []
        for j in range(0, col):
            val = temp_sheet.cell(i, j).value
            if i != 1 and j == 4:
                number = str(val).split('(')[0].strip("").strip("\n")
                address = str(val).split('(')[1].split(')')[0].strip("").strip("\n")
                temp.append(number)
                temp.append(address)
            else:
                if type(val) == float:
                    value = int(val)
                else:
                    value = str(val).strip("").strip("\n")
                temp.append(value)
        data.append(temp)
    return JsonResponse({'data': data})


def study(request):
    data = []
    filename = os.path.join(BASE_URL, 'static', 'files', FILE_Study)
    temp_excel = xlrd.open_workbook(filename)
    temp_sheet = temp_excel.sheet_by_index(1)
    row = 0  # 开始的行
    col = 6  # 结束的列
    for i in range(row, temp_sheet.nrows):
        temp = []
        for j in range(0, col):
            val = temp_sheet.cell(i, j).value
            if val == "":
                value = '——'
            elif type(val) == float:
                value = int(val)
            else:
                value = str(val).strip("").strip("\n")
            temp.append(value)
        data.append(temp)
    return JsonResponse({'data': data})


def GT(request):
    data = []
    filename = os.path.join(BASE_URL, 'static', 'files', FILE_GT)
    temp_excel = xlrd.open_workbook(filename)
    temp_sheet = temp_excel.sheet_by_index(0)
    row = 0  # 开始的行
    col = 6  # 结束的列
    for i in range(row, temp_sheet.nrows):
        temp = []
        for j in range(0, col):
            val = temp_sheet.cell(i, j).value
            if val == "":
                value = '——'
            elif type(val) == float:
                value = int(val)
            else:
                value = str(val).strip("").strip("\n")
            temp.append(value)
        data.append(temp)
    return JsonResponse({'data': data})


def diagnosis(request):
    # print('This is diagnosis:')
    repo_name = request.GET.get("repo_name")
    repo_version = request.GET.get("repo_version")
    now_repo = get_repo_now_name(repo_name)
    report_update = 0
    old_repo_name = ''
    if now_repo != '0' and now_repo != '-1' and now_repo:
        old_repo_name = repo_name
        repo_name = now_repo
        report_update = 1
    print('houtaiye: ', repo_name, repo_version)
    if repo_name and repo_version:
        insert_error = 0
        insert_error = check_insert_mes(repo_name, repo_version)
        # print('check result:', insert_error)
        if insert_error == 0:
            # issues_list = []
            down_msg = []
            msg = 'testing 1'
            repo_issue = ISSUE(repo_name, repo_version)
            repo_issue.init_with_dep_tree()
            # print('issue de repo version:', repo_issue.v_name, repo_issue.v_hash)
            # 如果，有更改检测方法，这里需要更改
            print('views dep list :', repo_issue.repo_c.direct_dep_list)

            if repo_issue.new_impact == -1 or repo_issue.old_impact == -1:
                print('** Need to check again **')
                # repo_issue.repo_c.init_all()
                if not repo_issue.repo_c.direct_dep_list:
                    repo_issue.repo_c.init_all()
                repo_issue.check_issue()
            else:
                # 是否重新检测：是
                print('** Check issues again **')
                # repo_issue.repo_c.init_all()
                if not repo_issue.repo_c.direct_dep_list:
                    repo_issue.repo_c.init_all()
                repo_issue.check_issue()
            if repo_issue.v_name:
                r_name = repo_issue.repo_name + '(' + repo_issue.v_name + ')'
            else:
                r_name = repo_issue.repo_name + '(' + repo_issue.v_hash + ')'
            all_up_list = []
            # print('get all up', repo_issue.repo_name, repo_issue.v_name, repo_issue.v_hash, all_up_list)
            all_up_list = get_all_up(repo_issue.repo_name, repo_issue.v_name, repo_issue.v_hash, all_up_list)
            # print('up:', all_up_list)

            # (reslut, issues_list) = repo_issue.return_issues()
            # if reslut <= 0:
            #     print('** Need to check again **')
            #     repo_issue.repo_c.init_all()
            #     repo_issue.check_issue()
            #     (reslut, issues_list) = repo_issue.return_issues()

            all_down_list = []
            all_down_list = get_all_down(repo_issue.repo_name, repo_issue.v_name, repo_issue.v_hash, all_down_list)
            # print('down:', all_down_list)
            # down_msg = repo_issue.repo_c.get_down_repo_msg()
            # # get repo's dependencies message
            # if repo_issue.search_e == 0 and repo_issue.insert_e == 0 and repo_issue.update_e == 0:
            #     msg = 'Insert into db successfully!'
            # else:
            #     msg = 'Insert into db error: ' + str(repo_issue.search_e) + ' ' + str(repo_issue.insert_e) + ' ' \
            #           + str(repo_issue.update_e)

            # d_repo, d_mod, u_repo, u_mod
            dep_tree = []  # json.dumps(data)
            c_d = [r_name, 4]
            r_id = repo_issue.repo_name + '(' + repo_issue.v_name + ')'
            r_id_hash = repo_issue.repo_name + '(' + repo_issue.v_hash + ')'
            for r in all_up_list:
                # r_name_part = r[0].split('(')[0]
                # u_name_part = r[2].split('(')[0]
                # d_mod = 0
                if r[1] > 0 and (r[0] == repo_issue.repo_name or r[0] == r_id or r[0] == r_id_hash):
                    d_mod = 3
                    if c_d[1] == 4:
                        c_d[1] = d_mod
                elif r[1] <= 0 and (r[0] == repo_issue.repo_name or r[0] == r_id or r[0] == r_id_hash):
                    d_mod = 2
                    if c_d[1] == 4:
                        c_d[1] = d_mod
                elif r[1] > 0 and (r[0] != repo_issue.repo_name and r[0] != r_id and r[0] != r_id_hash):
                    d_mod = 1
                else:
                    d_mod = 0
                if r[3] > 0 and (r[2] == repo_issue.repo_name or r[2] == r_id or r[2] == r_id_hash):
                    u_mod = 3
                    if c_d[1] == 4:
                        c_d[1] = d_mod
                elif r[3] <= 0 and (r[2] == repo_issue.repo_name or r[2] == r_id or r[2] == r_id_hash):
                    u_mod = 2
                    if c_d[1] == 4:
                        c_d[1] = d_mod
                elif r[3] > 0 and (r[2] != repo_issue.repo_name and r[2] != r_id and r[2] != r_id_hash):
                    u_mod = 1
                else:
                    u_mod = 0
                test_json = {}
                if [r[0], d_mod, r[2], u_mod] not in dep_tree:
                    data_dir = {'d_r' : r[0], 'd_m' : d_mod, 'u_r' : r[2], 'u_m' : u_mod}
                    dep_tree.append(json.dumps(data_dir))
            for r in all_down_list:
                # d_mod = 0
                # r_name_part = r[0].split('(')[0]
                # u_name_part = r[2].split('(')[0]
                if r[1] > 0 and (r[0] == repo_issue.repo_name or r[0] == r_id or r[0] == r_id_hash):
                    d_mod = 3  # client mod
                    if c_d[1] == 4:
                        c_d[1] = d_mod
                elif r[1] <= 0 and (r[0] == repo_issue.repo_name or r[0] == r_id or r[0] == r_id_hash):
                    d_mod = 2  # client no-mod
                    if c_d[1] == 4:
                        c_d[1] = d_mod
                elif r[1] > 0 and (r[0] != repo_issue.repo_name and r[0] != r_id and r[0] != r_id_hash):
                    d_mod = 1  # mod
                else:
                    d_mod = 0  # no-mod
                if r[3] > 0 and (r[2] == repo_issue.repo_name or r[2] == r_id or r[2] == r_id_hash):
                    u_mod = 3
                elif r[3] <= 0 and (r[2] == repo_issue.repo_name or r[2] == r_id or r[2] == r_id_hash):
                    u_mod = 2
                elif r[3] > 0 and (r[2] != repo_issue.repo_name and r[2] != r_id and r[2] != r_id_hash):
                    u_mod = 1
                else:
                    u_mod = 0
                if [r[0], d_mod, r[2], u_mod] not in dep_tree:
                    data_dir = {'d_r' : r[0], 'd_m' : d_mod, 'u_r' : r[2], 'u_m' : u_mod}
                    dep_tree.append(json.dumps(data_dir))

            # [mod_down, mod_down_url, tool_down, tool_down_url, mod_repo_list, tool_repo_list]
            d_msg_list = get_down_repo_msg(repo_name, repo_issue.repo_c.mod_name, repo_issue.repo_c.r_type)
            if repo_issue.repo_c.mod_num > 0:
                c_d[1] = 3
            else:
                c_d[1] = 2
            for d in d_msg_list[4]:
                # mod
                if [d, 1, c_d[0], c_d[1]] not in dep_tree:
                    data_dir = {'d_r': d, 'd_m': 1, 'u_r': c_d[0], 'u_m': c_d[1]}
                    dep_tree.append(json.dumps(data_dir))
            for d in d_msg_list[5]:
                # mod
                if [d, 0, c_d[0], c_d[1]] not in dep_tree:
                    data_dir = {'d_r': d, 'd_m': 0, 'u_r': c_d[0], 'u_m': c_d[1]}
                    dep_tree.append(json.dumps(data_dir))

            if not dep_tree:
                data_dir = {'d_r': repo_issue.repo_name, 'd_m': c_d[1], 'u_r': repo_issue.repo_name,
                            'u_m': c_d[1]}
                dep_tree.append(json.dumps(data_dir))
            # print(dep_tree)
            dep_tree_json = json.dumps(dep_tree)

            report_l = repo_issue.get_bug_report_with_dmsg(d_msg_list)
            if report_update == 1:
                updated_report = repo_issue.get_updated_report(old_repo_name, d_msg_list)
                report_list = [report_l, updated_report]
                report_list = sorted(report_list, key=lambda x: x[2])
                report_l = report_list[0]
            # print(report_l)
            # dep_tree_json = dep_tree
            # print(dep_tree_json)
            # issues_list.append('test1')
            # issues_list_json = json.dumps(issues_list)
            down_msg_json = json.dumps(down_msg)
            return JsonResponse({'result': insert_error, 'data': msg, 'dep_tree': dep_tree_json,
                                 'root_cause': report_l[0], 'solution': report_l[1]})
        else:
            # time.sleep(3)
            msg = 'Please check the input!'
            return JsonResponse({'result': insert_error, 'data': msg})
    else:
        insert_error = -3
        msg = 'Please wait!'
        return JsonResponse({'result': insert_error, 'data': msg})
