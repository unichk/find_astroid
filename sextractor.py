# !/usr/bin/python
# coding:utf-8

import csv
import os

root=r'/home/unicorn/文件/vscode/科展'
date = '2023_5_4'

for rootpath, subdirsinroot, filesintroot in os.walk("data-" + date):
    for subdirinroot in subdirsinroot:
        if subdirinroot.startswith("ps2"):
            path=os.path.join(root, rootpath)
            path=os.path.join(path, subdirinroot)
            path = [x[0] for x in os.walk(path)][1]
            os.chdir("/home/unicorn/文件/vscode/科展/log-" + date)
            os.system("mkdir " + subdirinroot)
            
            os.chdir("/home/unicorn/文件/vscode/科展")
            files = []
            for file in os.listdir(path):
                files.append(file)
            files=sorted(files)

            for file in files:
                if file.endswith(".fits"):
                    filepath=os.path.join(path, file)
                    os.chdir("/usr/share/sextractor")
                    os.system("sudo sextractor " + filepath + " -c custom_config.sex")
                    os.system("cp test.cat /home/unicorn/文件/vscode/科展/log-" + date + "/" + subdirinroot)
                    os.chdir("/home/unicorn/文件/vscode/科展/log-" + date + "/" + subdirinroot)
                    os.system("rename -v 's/test.cat/" + file[:-5] + ".csv/' test.cat")

            # cd /usr/share/sextractor
            # sextractor /home/unicorn/桌面/科展/XY14_p11/o9312g0484o.1762969.ch.2434992.XY14.p11.fits
            # cp test.cat /home/unicorn/桌面/科展/log
            # rename -v 's/test.cat/1.txt/' test.cat

            print(path)