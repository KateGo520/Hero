import random

import requests
import os
import zipfile


class PATH:
    path = ''

    def __init__(self):
        self.path = os.getcwd()  # /root/www/hero-v2.0
        self.path = self.path.replace('hero-v11.0', 'run-tool')

        # self.path = os.path.join('root', 'www', 'run-tool')
        # print('path', self.path)
        # /heroAPP/tool
        # self.path = os.path.join(self.path, 'heroAPP', 'tool')

    def get_deal_local_dir(self):
        deal_path = os.path.join(self.path, 'pkg', '2')
        return deal_path

    def get_pkg_dir(self):
        pkg_path = os.path.join(self.path, 'pkg')
        return pkg_path


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


class DOWNLOAD:
    def __init__(self, repo_msg):
        # token = get_token()
        # token_str = 'token ' + token
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0'
        }
        self.repo = repo_msg
        self.download_result = 0

    def down_load_unzip(self):
        # path_d = os.getcwd()
        # # /heroAPP/tool
        # path = os.path.join(path_d, 'heroAPP', 'tool')
        path_c = PATH()
        path = path_c.path
        save_name = os.path.join(path, 'pkg')
        repo_name = self.repo[0]
        repo_version = self.repo[1]
        filename = os.path.join('pkg', repo_name.replace('/', '=') + '@' + repo_version)  # kiali=kiali@v1.0.0
        # judge dir exit or not
        # check_result = os.path.exists(os.path.join(path, filename))
        check_result = os.path.isdir(os.path.join(path, filename))
        # print(os.path.join(path, filename))
        # print(check_result)
        if not check_result:
            # create url
            url = 'https://github.com/{}/archive/{}.zip'.format(repo_name, repo_version)
            try:
                r = requests.get(url=url, headers=self.headers, stream=True)
                with open(f'{os.path.join(path, filename)}.zip', 'wb') as f:
                    # write into content
                    for chunk in r.iter_content(chunk_size=512):
                        if chunk:
                            f.write(chunk)
                    f.flush()
                    f.close()
                    tip = 'Repo {} download successfully'.format(filename)
                # print(tip)

                # UNZIP
                unzip_name = filename + '.zip'
                # print(os.path.join(path, unzip_name))
                unzip = zipfile.ZipFile(os.path.join(path, unzip_name), 'r')
                unzip.extractall(os.path.join(save_name, '1'))
                unzip.close()
                # print('Unzip successfully')
                old_name = os.listdir(os.path.join(save_name, '1'))[0]
                os.remove(os.path.join(path, unzip_name))  # delete the zip
                os.rename(os.path.join(os.path.join(save_name, '1'), old_name), os.path.join(path, filename))
                self.download_result = 1
            except Exception as exp:
                self.download_result = -1
                print("download", filename, "failed:", exp, '---------------------------------------------------------')