import re
import time
import shutil
from django.shortcuts import render
from django.http import JsonResponse
import os
import xlrd
import json
from .repo import check_insert_mes, get_last_version, get_last_hash, deal_local_repo, get_mod_require, deal_dep_version, \
    get_requires_from_file, get_repo_name, get_new_url, get_all_repo_dir_list, deal_local_repo_dir
from .issue import ISSUE
from .repoDep import get_all_up
from .download import PATH


# def get_all_repo_dir_list(local_url):
#     local_list = os.listdir(local_url)
#     repo_dir_list = []
#     for d in local_list:
#         d_path = os.path.join(local_url, d)
#         r_path = d_path.replace(local_url, '')
#         if os.path.isdir(d_path) and d != '1' and (r_path not in repo_dir_list):
#             repo_dir_list.append(r_path)
#     return repo_dir_list
#
#
# def l_deal_mod(mod_list, repo_url, mod_dir_name, repo_name):
#     mod_dep_list = []
#     mod_req_list = []
#     mod_rep_list = []
#     l_mod_list = []
#     count = 0
#     mod_cu = ''
#     for p in mod_list:
#         if re.findall(r"/v\d+?/$", p):
#             path_v = re.findall(r"/v(\d+?)/$", p)[0]
#             if int(path_v) >= 2:
#                 # self.v_num = path_v
#                 mod_cu = p  # have v_dir
#                 break
#     if not mod_cu:
#         mod_cu = mod_list[0]
#     m_url = repo_url + mod_cu + 'go.mod'
#     go_mod_module = ''
#     if os.path.isfile(m_url):
#         f = open(m_url)
#         go_mod_content = f.read()
#         module = re.findall(r"^module\s*(.+?)$", go_mod_content, re.M)
#         if module:
#             go_mod_module = module[0].replace('"', '').strip()
#         else:
#             go_mod_module = ''
#         f.close()
#     if not go_mod_module and repo_name:
#         go_mod_module = 'github.com/' + repo_name
#     for m_url in mod_list:
#         count = count + 1
#         url = repo_url + m_url + 'go.mod'
#         cd_url = os.path.join(mod_dir_name, str(count) + '_go.mod')
#         l_mod_list.append(str(count) + '_' + m_url)
#         (mod_req_list, mod_rep_list) = get_mod_require(url, mod_req_list, mod_rep_list)
#         shutil.copyfile(url, cd_url)
#         # print('dependencies from go.mod files :', self.mod_req_list, self.mod_rep_list)
#     # mod_dep_list
#     for m in mod_req_list:
#         dep = m.replace('+replace', '').replace('// indirect', '').strip().split(' ')
#         if len(dep) > 1:
#             dep_version = deal_dep_version(dep[1])
#             if re.findall(r"\+replace", m) and dep:
#                 mod_dep_list.append([dep[0], dep_version, 3])  # replace
#             elif re.findall(r"// indirect", m) and dep:
#                 mod_dep_list.append([dep[0], dep_version, 2])  # dep from old repo
#             elif dep:
#                 mod_dep_list.append([dep[0], dep_version, 1])  # normal
#     return mod_dep_list, l_mod_list, go_mod_module
#
#
# def l_deal_tool(tool_list, repo_url, tool_dir_name):
#     l_tool_list = []
#     count = 0
#     for t_url in tool_list:
#         count = count + 1
#         url = repo_url + t_url
#         t_file_name = ''
#         if re.findall(r"/([^/]+?)$", t_url):
#             t_file_name = re.findall(r"/([^/]+?)$", t_url)[0]
#         elif re.findall(r"\\([^\\]+?)$", t_url):
#             t_file_name = re.findall(r"\\([^\\]+?)$", t_url)[0]
#         else:
#             t_file_name = 'tool.txt'
#         cd_url = os.path.join(tool_dir_name, str(count) + '_' + t_file_name)
#         l_tool_list.append(str(count) + '_' + t_url)
#         shutil.copyfile(url, cd_url)
#     return l_tool_list
#
#
# def deal_go_files(go_list, repo_url, go_mod_module):
#     import_list = []
#     for f_url in go_list:
#         file_url = repo_url + f_url
#         import_list = get_requires_from_file(file_url, import_list)
#     delete_list = []
#     for i in import_list:
#         # if go_mod_module:
#         #     delete_list.append(go_mod_module)
#         if go_mod_module and re.findall(r"^" + go_mod_module, i):
#             delete_list.append(i)
#     self_ref = len(delete_list)
#     for d in delete_list:
#         import_list.remove(d)
#     return import_list, self_ref
#
#
# def get_all_direct_dep(import_list):
#     repo_list = []
#     dep_list = []
#     delet_list = []
#     direct_repo_list = []
#     for imp in import_list:
#         if not re.findall(r"^github\.com/", imp):
#             repo_name = get_repo_name(imp)
#             if repo_name:
#                 if (not re.findall(r"^" + repo_name, imp.replace('github.com/', ''))) \
#                         and (not re.findall(r"^github\.com/", imp)):
#                     now_name = get_new_url('github.com/' + repo_name)
#                     if [repo_name, now_name] not in repo_list:
#                         repo_list.append([repo_name, now_name])
#                     if now_name:
#                         if now_name not in dep_list:
#                             dep_list.append(now_name)
#                     else:
#                         dep_list.append(repo_name)
#         else:
#             if re.findall(r"^github\.com/([^/]+?/[^/]+?)$", imp):
#                 repo_name = re.findall(r"^github\.com/([^/]+?/[^/]+?)$", imp)[0]
#             elif re.findall(r"^github\.com/[^/]+?/([^/]+?)/", imp):
#                 repo_name = re.findall(r"^github\.com/([^/]+?/[^/]+?)/", imp)[0]
#             else:
#                 repo_name = ''
#             if repo_name and ([repo_name, ''] not in repo_list):
#                 repo_list.append([repo_name, ''])
#                 # print('get_all_direct_dep方法:', [repo_name, ''])
#             if repo_name and (repo_name not in dep_list):
#                 dep_list.append(repo_name)
#     for d in delet_list:
#         import_list.remove(d)
#     for dep in repo_list:
#         # print('deal, need add last commit', dep)
#         last_commit = get_last_hash(dep[0].replace('github.com/', ''))
#         if last_commit:
#             # print('add version：', [dep[0], last_commit, dep[1]])
#             direct_repo_list.append([dep[0], last_commit, dep[1]])
#         else:
#             print('*******get last commit failed*********************')
#             # self.direct_repo_list.append([dep[0], '', dep[1]])
#     print('direct_repo_list:', direct_repo_list)
#     return direct_repo_list
#
#
# def get_all_direct_depmod(import_list, mod_dep_list):
#     direct_dep_list = []
#     for m_d in mod_dep_list:
#         if m_d[2] == 1:
#             for i in import_list:
#                 if re.findall(r"^" + m_d[0], i) and ([m_d[0], m_d[1]] not in direct_dep_list):
#                     direct_dep_list.append([m_d[0], m_d[1]])
#                     break
#     return direct_dep_list
#
#
# def get_msg_hero_go(file_name):
#     f = open(file_name)
#     file_content = f.read()
#     # 写入文件：
#     # $mod_num=2$   $tool_num=3$
#     # vendor_list
#     # l_mod_list  l_tool_list
#     # self_ref
#     # go_mod_module
#     # direct_repo_list
#     mod_num = 0
#     tool_num = 0
#     self_ref = 0
#     go_mod_module = ''
#     vendor_list = []
#     mod_list = []
#     tool_list = []
#     direct_repo_list = []
#     if re.findall(r"\$mod_num=(\d+?)\$", file_content):
#         mod_num = int(re.findall(r"\$mod_num=(\d+?)\$", file_content)[0])
#     if re.findall(r"\$tool_num=(\d+?)\$", file_content):
#         tool_num = int(re.findall(r"\$tool_num=(\d+?)\$", file_content)[0])
#     if re.findall(r"\$self_ref=(\d+?)\$", file_content):
#         self_ref = int(re.findall(r"\$self_ref=(\d+?)\$", file_content)[0])
#     if re.findall(r"\*go_mod_module=.+?\*", file_content):
#         go_mod_module = re.findall(r"\*go_mod_module=.+?\*", file_content)[0]
#     if re.findall(r"\$vendor:[^\$]+?\$", file_content):
#         vendor_list = re.findall(r"\$vendor:[^\$]+?\$", file_content)[0].split(';')
#     if re.findall(r"\$go.mod:[^\$]+?\$", file_content):
#         l_mod_list = re.findall(r"\$go.mod:[^\$]+?\$", file_content)[0].split(';')
#         for l in l_mod_list:
#             if re.findall(r"^\d+?_(.+?)$", l):
#                 l_mod = re.findall(r"^\d+?_(.+?)$", l)[0]
#                 if l_mod not in mod_list:
#                     mod_list.append(l_mod)
#     if re.findall(r"\$tool:[^\$]+?\$", file_content):
#         l_tool_list = re.findall(r"\$tool:[^\$]+?\$", file_content)[0].split(';')
#         for l in l_tool_list:
#             if re.findall(r"^\d+?_(.+?)$", l):
#                 l_tool = re.findall(r"^\d+?_(.+?)$", l)[0]
#                 if l_tool not in tool_list:
#                     tool_list.append(l_tool)
#     if re.findall(r"\$direct_dep:[^\$]+?\$", file_content):
#         dd_list = re.findall(r"\$direct_dep:[^\$]+?\$", file_content)[0].split(';')
#         for d in dd_list:
#             d_i = d.replace('[', '').replace(']', '')
#             d_l = d_i.split(',')
#             if d_l not in direct_repo_list:
#                 direct_repo_list.append(d_l)
#     # print(file_import)
#     f.close()
#     return mod_num, tool_num, vendor_list, self_ref, mod_list, tool_list, go_mod_module, direct_repo_list
#
#
# def deal_local_repo_dir(repo_id):
#     path_c = PATH()
#     pkg_local = path_c.get_pkg_dir()  # pkg
#     deal_path = path_c.get_deal_local_dir()  # pkg/2
#     deal_repo_path = os.path.join(deal_path, repo_id)  # pkg/2/id
#     repo_url = os.path.join(pkg_local, repo_id)  # repo download dir  pkg/id
#     file_name = os.path.join(deal_repo_path, 'hero-go.txt')
#     mod_dir_name = os.path.join(deal_repo_path, 'mod')
#     tool_dir_name = os.path.join(deal_repo_path, 'tool')
#     go_list = []
#     mod_list = []
#     tool_list = []
#     vendor_list = []
#     if not os.path.exists(file_name):
#         if not os.path.exists(deal_repo_path):
#             os.makedirs(deal_repo_path)
#             os.makedirs(mod_dir_name)
#             os.makedirs(tool_dir_name)
#
#         (go_list, mod_list, tool_list, vendor_list) = deal_local_repo(repo_url, repo_url, go_list, mod_list, tool_list,
#                                                                       vendor_list)
#         mod_num = len(mod_list)  # $mod_num=2$
#         tool_num = len(tool_list)  # $tool_num=3$
#         if mod_num > 0:
#             mod_list.sort(key=lambda m: len(m), reverse=False)
#         if tool_num > 0:
#             tool_list.sort(key=lambda t: len(t), reverse=False)
#         repo_name = ''
#         if re.findall(r"/([^/]+?)@+?$", repo_url):
#             repo_name = re.findall(r"/([^/]+?)@+?$", repo_url)[0].replace('=', '/')
#         elif re.findall(r"\\([^\\]+?)@.+?$", repo_url):
#             repo_name = re.findall(r"\\([^\\]+?)@.+?$", repo_url)[0].replace('=', '/')
#         go_mod_module = ''
#         mod_dep_list = []
#         l_mod_list = []
#         l_tool_list = []
#         if mod_list:
#             (mod_dep_list, l_mod_list, go_mod_module) = l_deal_mod(mod_list, repo_url, mod_dir_name, repo_name)
#         if tool_list:
#             l_tool_list = l_deal_tool(tool_list, repo_url, tool_dir_name)
#         (import_list, self_ref) = deal_go_files(go_list, repo_url, go_mod_module)
#         if not go_mod_module and repo_name:
#             go_mod_module = 'github.com/' + repo_name
#         if mod_dep_list:
#             direct_repo_list = get_all_direct_depmod(import_list, mod_dep_list)
#         else:
#             direct_repo_list = get_all_direct_dep(import_list)
#         # 写入文件：
#         # $mod_num=2$   $tool_num=3$
#         # vendor_list
#         # l_mod_list  l_tool_list
#         # self_ref
#         # go_mod_module
#         # direct_repo_list
#         if not mod_list:
#             go_mod_module = ''
#         file_str = '$mod_num=' + str(mod_num) + '$tool_num=' + str(tool_num) + '$self_ref=' + str(self_ref) + '$'
#         if go_mod_module:
#             file_str = file_str + '*go_mod_module=' + go_mod_module + '*'
#         vendor_str = '$vendor:'
#         for v in vendor_list:
#             vendor_str = vendor_str + v + ';'
#         file_str = file_str + vendor_str + '$'
#         mod_str = '$go.mod:'
#         for lm in l_mod_list:
#             mod_str = mod_str + lm + ';'
#         file_str = file_str + mod_str + '$'
#         tool_str = '$tool:'
#         for lt in l_tool_list:
#             tool_str = tool_str + lt + ';'
#         file_str = file_str + tool_str + '$'
#         direct_dep_str = '$direct_dep:'
#         for d in direct_repo_list:
#             d_str = '['
#             for d_s in d:
#                 d_str = d_str + d_s + ','
#             d_str = d_str.strip(',') + ']'
#             direct_dep_str = direct_dep_str + d_str + ';'
#         file_str = file_str + direct_dep_str + '$'
#
#         file = open(file_name, 'w')
#         file.write(file_str)  # msg也就是下面的Hello world!
#         file.close()
#         shutil.rmtree(repo_url)
#     else:
#         (mod_num, tool_num, vendor_list, self_ref, mod_list, tool_list, go_mod_module,
#          direct_repo_list) = get_msg_hero_go(file_name)
#     return mod_num, tool_num, vendor_list, self_ref, mod_list, tool_list, go_mod_module, direct_repo_list


def main():
    # check_e = 0
    # search_e = 0
    # insert_e = 0
    # insert_s = 0
    # update_e = 0
    # update_s = 0
    # 遍历获取目录中所有目录
    path_c = PATH()
    pkg_local = path_c.get_pkg_dir()  # pkg
    # 获取所有现有的项目的路径列表
    repo_dir_list = get_all_repo_dir_list(pkg_local)
    print(repo_dir_list)
    count = 0
    for repo_dir in repo_dir_list:
        count = count + 1
        repo_dir = repo_dir.replace('/', '').replace('\\', '')
        time_s = int(time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())))
        deal_local_repo_dir(repo_dir)
        time_e = int(time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())))
        print(str(count), repo_dir, ':', time_s, '->', time_e, ' : ',
              time_e - time_s, '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')

    # print('searchError', search_e, 'insertError', insert_e, 'checkError', check_e, 'updateError', update_e)
    # print('insert successfully:', insert_s)
    # print('update successfully:', update_s)
    # time_e = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))


if __name__ == '__main__':
    main()