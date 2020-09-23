from django.shortcuts import render
from django.http import JsonResponse
import os
import xlrd
from .tool.repo import check_insert_mes
from .tool.issue import ISSUE
from .tool.repoDep import get_all_up


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
    print('This is diagnosis')
    repo_name = request.GET.get("repo_name")
    repo_version = request.GET.get("repo_version")
    print('houtaiye: ', repo_name, repo_version)
    if repo_name and repo_version:
        insert_error = check_insert_mes(repo_name, repo_version)
        if insert_error == 0:
            repo_issue = ISSUE(repo_name, repo_version)
            repo_issue.init_with_dep_tree()
            repo_issue.check_issue()
            all_up_list = []
            all_up_list = get_all_up(repo_issue.repo_name, repo_issue.v_name, repo_issue.v_hash, all_up_list)
            (reslut, issues_list) = repo_issue.return_issues()
            if reslut <= 0:
                repo_issue.check_issue()
                (reslut, issues_list) = repo_issue.return_issues()
            down_msg = repo_issue.repo_c.get_down_repo_msg()

            # get repo's dependencies message

            if repo_issue.search_e == 0 and repo_issue.insert_e == 0 and repo_issue.update_e == 0:
                msg = 'Insert into db successfully!'
            else:
                msg = 'Insert into db error: ' + str(repo_issue.search_e) + ' ' + str(repo_issue.insert_e) + ' ' \
                      + str(repo_issue.update_e)
            # time.sleep(3)
            return JsonResponse({'result': insert_error, 'data': msg, 'dep_tree': all_up_list, 'issues': issues_list,
                                 'down_msg': down_msg})
        else:
            # time.sleep(3)
            msg = 'Please check the input!'
            return JsonResponse({'result': insert_error, 'data': msg})
    else:
        insert_error = -3
        msg = 'Please wait!'
        return JsonResponse({'result': insert_error, 'data': msg})





