#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from astropy.io import fits
from itertools import combinations
from kapteyn import wcs
from PIL import Image, ImageDraw
from typing import List

data_root = r"D:\Iasc data\2023_5_4"
log_root = r"C:\Users\User\Documents\dev\new_astroid\log-2023_5_4"
hough_out_pic_root = r"output-5_4"

difference = 0.01
theata_step = 0.1

def read_log(folder_name: str) -> List[pd.DataFrame]:
    dfs = []
    for file_name in sorted(os.listdir(os.path.join(log_root, folder_name))):
        df_in = pd.read_csv(os.path.join(log_root, folder_name, file_name), skiprows = 7, header = None)
        df_split = [list(filter(None, row)) for row in df_in[0].str.split(" ")]
        df = pd.DataFrame(df_split, columns = ['idx', 'FLUXERR_ISO', 'FLUX_AUTO', 'FLUXERR_AUTO', 'X_image', 'Y_image', 'flags'])
        df['X_image'] = pd.to_numeric(df['X_image'])
        df['Y_image'] = pd.to_numeric(df['Y_image'])
        dfs.append(df[['X_image', 'Y_image']].copy())
    return dfs

def to_wcs(folder_name: str, df_with_image_coord: List[pd.DataFrame]) -> List[pd.DataFrame]:
    folder_path = os.path.join(data_root, folder_name, folder_name.split('_', 2)[2])
    for idx, file_name in enumerate(sorted(os.listdir(folder_path))):
        file = fits.open(os.path.join(folder_path, file_name))
        header = file[0].header
        print(header['DATE-OBS'])
        proj = wcs.Projection(header, skyout = "DYNJ2000")
        df_with_image_coord[idx]['wcs'] = df_with_image_coord[idx].apply(lambda x: proj.toworld((x['X_image'], x['Y_image'])), axis = 1)
    return df_with_image_coord

def delete_duplicate(dfs: List[pd.DataFrame]) -> pd.DataFrame:
    for idx, df in enumerate(dfs):
        df['idx'] = [idx for _ in range(len(df))]
    df_combine = pd.concat(dfs, ignore_index = True)
    df_combine['wcs_rounded'] = df_combine['wcs'].apply(lambda x: (round(4 * x[0], 2), round(4 * x[1], 2)))
    df_combine = df_combine[df_combine.duplicated(['wcs_rounded'], keep = False).groupby(df_combine['wcs_rounded']).transform('sum').le(2)]
    return df_combine.drop(columns = ['wcs_rounded']).copy().reset_index(drop = True)

def create_r_table(df: pd.DataFrame, theata_step = theata_step) -> pd.DataFrame:
    r_tables = []
    for idx, row in df.iterrows():
        row_r_table = pd.DataFrame(df.iloc[[idx] * len(np.arange(0.0, 180.0, theata_step))])
        r_theata = []
        for theta in np.arange(0.0, 180.0, theata_step):
            x = row['wcs'][0]
            y = row['wcs'][1]
            r_theata.append((round((x * math.cos(theta * math.pi / 180) + y * math.sin(theta * math.pi / 180)), 4), theta))
        row_r_table['r_theata'] = r_theata
        r_tables.append(row_r_table)
    r_table = pd.concat(r_tables)
    return r_table.reset_index(drop = True)

def equals(a, b, difference = difference):
    if(abs((a - b) / min(a, b)) <= difference):
        return True
    return False

def dist(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

def find_all_line(r_table: pd.DataFrame):
    all_lines = []
    group = r_table.groupby(['r_theata'])
    group_dict = group.groups
    for key, val in list(group_dict.items()):
        if len(val) < 3:
            del group_dict[key]
        elif len(r_table.iloc[val]['idx'].value_counts()) < 3:
            del group_dict[key]
        else:
            for st in range(len(val) - 2):
                for end in range(st + 3, len(val) + 1):
                    data = r_table.iloc[val[st:end]].sort_values(by = ['wcs']).reset_index(drop = True)
                    if (data.iloc[0]['idx'] > data.iloc[1]['idx'] > data.iloc[2]['idx']) or (data.iloc[0]['idx'] < data.iloc[1]['idx'] < data.iloc[2]['idx']):
                        if equals(dist(data.iloc[0]['wcs'], data.iloc[1]['wcs']) / (data.iloc[1]['idx'] - data.iloc[0]['idx']),
                            dist(data.iloc[1]['wcs'], data.iloc[2]['wcs']) / (data.iloc[2]['idx'] - data.iloc[1]['idx']),):
                            add = True
                            for line in all_lines:
                                if data.drop(columns = ['r_theata']).equals(line):
                                    add = False
                                    break
                            if add:
                                all_lines.append(data.drop(columns = ['r_theata']))
    return list(all_lines)

def draw_all_lines(all_lines: pd.DataFrame, folder_name):
    folder_path = os.path.join(data_root, folder_name, folder_name.split('_', 2)[2])
    for _, folders, _ in os.walk(hough_out_pic_root):
        if folder_name not in folders:
            os.mkdir(os.path.join(hough_out_pic_root, folder_name))
            os.mkdir(os.path.join(hough_out_pic_root, folder_name, "jpg"))
            os.mkdir(os.path.join(hough_out_pic_root, folder_name, "png"))
        break
    for idx, file_name in enumerate(sorted(os.listdir(folder_path))):
        img = Image.new('RGB', (2423, 2434), color = 'white')
        img = Image.new('RGB', (2423, 2434), color = 'white')
        file = fits.open(os.path.join(folder_path, file_name))
        image = Image.fromarray(file[0].data)
        img.paste(image)
        draw = ImageDraw.Draw(img)
        color = [(255, 0, 0), (27, 118, 51), (29, 49, 176), (162, 29, 153)]
        size = 7
        for line in all_lines:
            for i in range(3):
                draw.ellipse(((line.iloc[i]['X_image'] - size, line.iloc[i]['Y_image'] - size), 
                              (line.iloc[i]['X_image'] + size, line.iloc[i]['Y_image'] + size)), 
                              outline = color[line.iloc[i]['idx']])
            draw.line(((line.iloc[0]['X_image'], line.iloc[0]['Y_image']), (line.iloc[2]['X_image'], line.iloc[2]['Y_image'])), 
                      fill = (0, 0, 0), width = 1)

        img.save(f'{hough_out_pic_root}/{folder_name}/png/{idx}.png', optimize=True, quality=10000)
        img.save(f'{hough_out_pic_root}/{folder_name}/jpg/{idx}.jpg', optimize=True, quality=10000)

def find(floder_name: str, plot_delete = True):
    dfs = read_log(floder_name)
    print("finish reading log...")
    if plot_delete:
        fig, axs = plt.subplots(1, 2)
        axs[0].set_box_aspect(1)
        axs[1].set_box_aspect(1)
        dfs[0].plot.scatter(x = 'X_image', y = 'Y_image', ax = axs[0], c = 'red')
        dfs[1].plot.scatter(x = 'X_image', y = 'Y_image', ax = axs[0], c = 'green')
        dfs[2].plot.scatter(x = 'X_image', y = 'Y_image', ax = axs[0], c = 'blue')
        dfs[3].plot.scatter(x = 'X_image', y = 'Y_image', ax = axs[0], c = 'purple')
    dfs = to_wcs(floder_name, dfs)
    print("finish converting to wcs...")
    df = delete_duplicate(dfs)
    print("finish deleting duplicate values...")
    if plot_delete:
        sns.scatterplot(data = df, x = 'X_image', y = 'Y_image', hue = 'idx', ax = axs[1], palette = ['red', 'green', 'blue', 'purple'], legend = False)
        plt.show()
    r_table = create_r_table(df)
    print("finish creating r table...")
    all_lines = find_all_line(r_table)
    print(f"found {len(all_lines)} astroids...")
    draw_all_lines(all_lines, floder_name)
    print("finish drawing")

def main():
    # for _, folders, _ in os.walk(log_root):
    #     for folder_name in folders:
    #         if folder_name.startswith("ps2"):
    #                 find(folder_name, True)
    # find("ps2-20230423_10_XY62_p10")
    find("ps2-20230424_14_XY12_p10")

if __name__ == '__main__':
    main()