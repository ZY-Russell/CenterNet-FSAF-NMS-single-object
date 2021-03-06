# import _init_paths
#
# import os
# import cv2
#
# from src.lib.opts import opts
# from src.lib.detectors.detector_factory import detector_factory
# from src.lib.detectors.ctdet import CtdetDetector
#
# import numpy as np
# from progress.bar import Bar
# import time
# import torch
#
# from src.lib.external.nms import soft_nms
# from src.lib.models.decode import ctdet_decode
# from src.lib.models.utils import flip_tensor
# from src.lib.utils.image import get_affine_transform
# from src.lib.utils.post_process import ctdet_post_process
# from src.lib.utils.debugger import Debugger
#
# from src.lib.detectors.base_detector import BaseDetector



from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import _init_paths

import os
import cv2

import argparse
import sys

from opts import opts
from detectors.detector_factory import detector_factory

import collections

from src.calssify_dropper_line.test_for_ring import *
from src.calssify_dropper_line.models.model import *
from src.calssify_dropper_line.utils import *
from src.calssify_dropper_line.dataset.dataloader import *

import multiprocessing
import shutil

# bbox[ltx,lty,rbx,rby] ---> bbox[cx,cy,w,h]
def tansfer_bbox(ring_bbox):
    list_for_match = []
    for item in ring_bbox: # item[ltx,lty,rbx,rby]
        item_w = round((item[2] - item[0]), 3)
        item_h = round((item[3] - item[1]), 3)
        item_cx = round((item[2] + item[0]) / 2, 3)
        item_cy = round((item[3] + item[1]) / 2, 3)
        item_bbox = [item_cx, item_cy, item_w, item_h]
        list_for_match.append(item_bbox)
    return list_for_match

def tansfer_bbox2(ring_bbox):
    list_for_match = []
    for i in range(4): # item[ltx,lty,rbx,rby]
        item_w = ring_bbox[2] - ring_bbox[0]
        item_h = ring_bbox[3] - ring_bbox[1]
        item_cx = (ring_bbox[2] + ring_bbox[0]) / 2
        item_cy = (ring_bbox[3] + ring_bbox[1]) / 2
        item_bbox = [item_cx, item_cy, item_w, item_h]
        list_for_match = item_bbox
    return list_for_match
#
# def draw_img(dropper_bbox, bad_ring_bbox, img):  # 可视化dropper的函数
#     im_data = cv2.imread(img)
#     h, w, _ = im_data.shape
#     font = cv2.FONT_HERSHEY_SIMPLEX
#     # print(dropper_list)
#     for item in dropper_bbox:
#         # objName = item[0]
#         objName = "dropper"
#         scores = item[-1]
#         # box = item[2]
#         show_tlx = int(item[0])  # tlx
#         show_tly = int(item[1])  # tly
#         show_brx = int(item[2])  # brx
#         show_bry = int(item[3])  # bry
#         thick = int((h + w) / 700)
#         # cv2.rectangle(im_data,
#         #               (box[0], box[1]), (box[2], box[3]),
#         #               colors, thick)
#         # cv2.rectangle(im_data, (show_x - show_w // 2, show_y - show_h // 2),
#         #               (show_x + show_w // 2, show_y + show_h // 2), (0, 255, 0), thick)
#         cv2.rectangle(im_data, (show_tlx, show_tly),
#                       (show_brx, show_bry), (0, 255, 0), thick)
#         # mess = '%s: %.3f' % (objName, scores)
#         txt = '%s' % (objName)
#         # cv2.putText(im_data, mess, (show_x - show_w // 2, show_y - show_h // 2 - 12),
#         #             0, 1e-3 * h, (0, 0, 255), thick // 2)
#         cv2.putText(im_data, txt, (show_tlx, show_tly - 8),
#                     font, 0.5, (0, 0, 255), thickness=1, lineType=cv2.LINE_AA)
#     '''
#     for item in bad_ring_bbox:
#         # objName = item[0]
#         objName = "bad_ring"
#         scores = item[-1]
#         # box = item[2]
#         show_tlx = int(item[0])  # tlx
#         show_tly = int(item[1])  # tly
#         show_brx = int(item[2])  # brx
#         show_bry = int(item[3])  # bry
#         thick = int((h + w) / 700)
#         # cv2.rectangle(im_data,
#         #               (box[0], box[1]), (box[2], box[3]),
#         #               colors, thick)
#         # cv2.rectangle(im_data, (show_x - show_w // 2, show_y - show_h // 2),
#         #               (show_x + show_w // 2, show_y + show_h // 2), (0, 255, 0), thick)
#         cv2.rectangle(im_data, (show_tlx, show_tly),
#                       (show_brx, show_bry), (255, 0, 0), thick)
#         # mess = '%s: %.3f' % (objName, scores)
#         txt = '%s' % (objName)
#         # cv2.putText(im_data, mess, (show_x - show_w // 2, show_y - show_h // 2 - 12),
#         #             0, 1e-3 * h, (0, 0, 255), thick // 2)
#         cv2.putText(im_data, txt, (show_tlx, show_tly - 8),
#                     font, 0.5, (0, 0, 255), thickness=1, lineType=cv2.LINE_AA)
#
#     '''
#     # cv2.imshow("test", im_data)
#     # cv2.waitKey(0)
#     return im_data
def draw_img(res, img):
    im_data = cv2.imread(img)
    #print(img)
    h, w, _ = im_data.shape
    colors = (255, 255, 255)
    wd = os.getcwd()
    savedir = '%s/output'%(wd)
    savedir_broken = '%s/broken_output'%(wd)
    if not os.path.exists(savedir):
        os.makedirs(savedir)
    if not os.path.exists(savedir_broken):
        os.makedirs(savedir_broken)

    global flag
    flag = 0

    for item in res:
        flag = 0
        objName = item[0]
        scores = item[1]
        box = item[1]
        show_x = int(box[0])  # ltx
        show_y = int(box[1])  # lty
        show_w = int(box[2])  # w
        show_h = int(box[3])  # h
        thick = int((h + w) / 300)

        if objName == 'dropper':
        #cv2.rectangle(im_data,(box[0], box[1]), (box[2], box[3]),colors, thick)
            cv2.rectangle(im_data, (show_x - show_w // 2, show_y - show_h // 2),
                          (show_x + show_w // 2, show_y + show_h // 2), (0, 255, 0), thick//2)
            #mess = '%s: %.3f' % (objName, scores)
            #cv2.putText(im_data, mess, (show_x - show_w // 2, show_y - show_h // 2 - 6), 0, 5e-4 * h, (0, 0, 255), thick // 4)

        elif objName == 'bad':
            flag = 1
            cv2.rectangle(im_data, (show_x - show_w // 2, show_y - show_h // 2),
                          (show_x + show_w // 2, show_y + show_h // 2), (0, 0, 255), thick//2)

            #mess = '%s: %.3f' % (objName, scores)
            #cv2.putText(im_data, mess, (show_x - show_w // 2, show_y - show_h // 2 - 6), 0, 5e-4 * h, (0, 0, 255), thick // 4)
    img_name = img.split('/')[-1]
    # if flag == 1:
    #     cv2.imwrite(os.path.join(savedir_broken, '%s' % (img_name)), im_data)
    cv2.imwrite(os.path.join(savedir, '%s' % (img_name)), im_data)
    #cv2.imshow("test", im_data)
    #cv2.waitKey(0)
    return im_data

#　在之前的限制条件下，top_ring会选择纵向和自己更近的bottom_ring（主要是根据数据的规律的到的，不一定准确）
def fix_match_pair(match_pair, list_for_match):  # 用来精修match_pair，针对test2017/00000079.jpg这种情况
    fixed_match_pair = match_pair.copy() # 复制一份list，不然直接赋值两个list是共用内存的
    num_match_pair = len(match_pair)

    for i in range(num_match_pair):
        pair1 = match_pair[i]
        # print('i,pair1:', i, pair1)
        top_ring_idx1 = pair1[0]
        bottom_ring_idx1 = pair1[1]

        for j in range(num_match_pair-i):
            pair2 = match_pair[j+i] #   这里的j+i可以让算法不比较已经比较过的pair
            # print('     j,pair2:', i, pair2)
            top_ring_idx2 = pair2[0]
            bottom_ring_idx2 = pair2[1]
            if pair1 == pair2:
                pass
            else:
                if (top_ring_idx1==top_ring_idx2): # 如果两对匹配的pair有相同的top_ring
                    # 如果bottom_ring_idx1离top_ring_idx1在纵向上更近，那就删掉pair2；否则删掉pair1
                    if list_for_match[bottom_ring_idx1][1] <= list_for_match[bottom_ring_idx2][1]:
                        fixed_match_pair.remove(pair2)
                    else:
                        fixed_match_pair.remove(pair1)
                else:
                    pass
                # if (bottom_ring_idx1==bottom_ring_idx2): # 如果两对匹配的pair有相同的top_ring
                #     # 如果bottom_ring_idx1离top_ring_idx1在纵向上更近，那就删掉pair2；否则删掉pair1
                #     if list_for_match[bottom_ring_idx1][1] <= list_for_match[bottom_ring_idx2][1]:
                #         fixed_match_pair.remove(pair2)
                #     else:
                #         fixed_match_pair.remove(pair1)
                # else:
                #     pass
    # print("fixed_match_pair:", fixed_match_pair)
    return fixed_match_pair

def match_rings(ring_key_dict, list_for_match): # 将无序的ring_key_dict变为有序字典，再将ring_key_dict中的正确匹配pair挑选出来
    match_pair = []
    tmp_ring_list = sorted(zip(ring_key_dict.values(), ring_key_dict.keys())) # ring_key_dict按距离大小进行排序
    ring_key_dict = collections.OrderedDict() # 定义有序字典
    for item in tmp_ring_list:
        ring_key_dict[item[1]] = item[0]
    print("     ring_key_dict(ordered dict):" , ring_key_dict)
    print("\n     len(list_for_match): ", len(list_for_match))

    lonely_pairs = []   # 保存未匹配的pair，用于二次匹配
    matched_idx = []  # 为了杜绝重复匹配
    for i in range(len(list_for_match)):                       #这里的搜索次数不好确定 ！！！！！！！！
        for ring_key in ring_key_dict.keys():
            if ring_key[0] in matched_idx or ring_key[1] in matched_idx:
                continue    # 为了避免重复匹配(虽然是不能重复匹配，但是有些情况必须重复匹配之后再根据实际情况来筛选，例如test第79张
            if (i in ring_key):
                # print("matching 1 :", ring_key)
                x1 = list_for_match[ring_key[0]][0]
                y1 = list_for_match[ring_key[0]][1]
                w1 = list_for_match[ring_key[0]][2]
                h1 = list_for_match[ring_key[0]][3]
                x2 = list_for_match[ring_key[1]][0]
                y2 = list_for_match[ring_key[1]][1]
                w2 = list_for_match[ring_key[1]][2]
                h2 = list_for_match[ring_key[1]][3]
                y1y2_distance = abs(y1-y2)          # |top_ring_y - bottom_ring_y|
                x1x2_distance = x1 - x2             # top_ring_x - bottom_ring_x (这个值应当小于0，因为一般top_ring在bottom_ring左侧)
                #  以下的限制条件是根据数据总结的规律，不一定准确
                # print("y1y2_distance", y1y2_distance)
                #   两个ring要匹配，纵向上不能离的太远也不能离的太近,横向上就算x1x2_distance不小于0也不应该太大(阈值设为1/3个Bbox)
                if (y1y2_distance <=  12*((h1+h2)/2)) and (y1y2_distance >=  2*((h1+h2)/2)) and (x1x2_distance <= w1/3):
                    # if (x1x2_distance <= w1/3):
                    # print("successful match 1 :", ring_key)
                    match_pair.append(ring_key)

                    matched_idx.append(ring_key[0])
                    matched_idx.append(ring_key[1])
                    # elif (x1x2_distance >= w1/3) and (x1x2_distance <= w1):
                    #     print("successful match 2 :", ring_key)
                    #     match_pair.append(ring_key)
                    #
                    #     matched_idx.append(ring_key[0])
                    #     matched_idx.append(ring_key[1])
                    break
                else:
                    lonely_pairs.append(ring_key)
                    if (ring_key[0] not in matched_idx) and (ring_key[0] not in lonely_idx):
                        lonely_idx.append(ring_key[0])
                    if (ring_key[1] not in matched_idx) and (ring_key[1] not in lonely_idx):
                        lonely_idx.append(ring_key[1])
                    # print("!!!cannot match 1 :", ring_key)
                    pass
            else:
                pass
    for lonely_ring_key in lonely_pairs:  # 放宽搜索条件二次匹配
        if lonely_ring_key[0] in matched_idx or lonely_ring_key[1] in matched_idx:
            continue
        # print("matching 2 :", lonely_ring_key)
        x1 = list_for_match[lonely_ring_key[0]][0]
        y1 = list_for_match[lonely_ring_key[0]][1]
        w1 = list_for_match[lonely_ring_key[0]][2]
        h1 = list_for_match[lonely_ring_key[0]][3]
        x2 = list_for_match[lonely_ring_key[1]][0]
        y2 = list_for_match[lonely_ring_key[1]][1]
        w2 = list_for_match[lonely_ring_key[1]][2]
        h2 = list_for_match[lonely_ring_key[1]][3]
        y1y2_distance = abs(y1 - y2)
        x1x2_distance = x1 - x2
        # 放宽配对条件
        if (y1y2_distance <= 14 * ((h1+h2)/2)) and (y1y2_distance >= 2 * ((h1+h2)/2)) and (x1x2_distance <= w1):
            # print("successful match 2 :", lonely_ring_key)
            match_pair.append(lonely_ring_key)

            matched_idx.append(lonely_ring_key[0])
            matched_idx.append(lonely_ring_key[1])
            lonely_idx.remove(lonely_ring_key[0])
            lonely_idx.remove(lonely_ring_key[1])
            break
        else:
            # print("!!!cannot match 2 :", lonely_ring_key,  matched_idx)
            pass

    match_pair = set(match_pair) # 去除重复pair
    match_pair = list(match_pair)
    # print("\nmatch_pair:", match_pair)
    return match_pair

def merge_ring_bbox(ring_bbox):  # merge ring_bboxs to dropper_bbox
    list_for_match = [] # [cx,cy,w,h]
    list_for_match = tansfer_bbox(ring_bbox) # bbox[ltx,lty,rbx,rby] ---> bbox[cx,cy,w,h]
    print("     list_for_match:", list_for_match)
    x_distance = 0
    y_distance = 0
    ring_key_dict = {}  # {(key1,key2) : x_distance}
    global lonely_idx
    lonely_idx = []
    matched_keys = []
    for key1,item1 in enumerate(list_for_match): # 得到ring_key_dict，存放的是横坐标在合理范围内的pair
        for key2,item2 in enumerate(list_for_match):
            if key1 != key2 and (item1[1] <= item2[1]): # only top_ring can match bottom_ring
                x_distance = round(abs(item1[0] - item2[0]),3) # Euclidean Distance of x
                if x_distance > 0 and x_distance < (item1[2]*2.5): # make lonely ring out of match process
                    ring_key_dict[(key1,key2)] = round(x_distance, 3)
                else:
                    pass
    # 得到lonely_keys，存放未匹配的ring 的索引
    for key in ring_key_dict.keys(): # 得到已经匹配的ring的索引
        key1 = key[0]
        key2 = key[1]
        matched_keys.append(key1)
        matched_keys.append(key2)
    # 去除重复元素
    matched_keys = set(matched_keys)
    matched_keys = list(matched_keys)
    for i in range(len(list_for_match)):# 得到未匹配的ring的索引
        if i in matched_keys:
            pass
        else:
            lonely_idx.append(i)

    match_pair = match_rings(ring_key_dict, list_for_match) # match_pair: [(3, 0),(4, 1),(topring_idx,bottomring_idx)]
    # match_pair = fix_match_pair(match_pair, list_for_match) # 用来精修match_pair，针对test2017/00000079.jpg这种情况
    print("\n     match_pair:", match_pair)
    print("     lonely_idx:", lonely_idx)
    dropper_bbox = [] # 存放dropper的坐标([ltx,lty,rbx,rby])
    for pair in match_pair:
        top_ring_idx = pair[0]
        dropper_tlx = max(0,ring_bbox[top_ring_idx][0])
        dropper_tly = max(0,ring_bbox[top_ring_idx][1])
        bottom_ring_idx = pair[1]
        dropper_brx = max(0,ring_bbox[bottom_ring_idx][2])
        dropper_bry = max(0,ring_bbox[bottom_ring_idx][3])
        dropper_bbox.append([dropper_tlx, dropper_tly, dropper_brx, dropper_bry])
    print("     dropper_bbox:", dropper_bbox)
    # print(ring_key_dict,matched_keys,lonely_keys)
    return dropper_bbox


def demo(opt, img, detector):
    os.environ['CUDA_VISIBLE_DEVICES'] = opt.gpus_str
    # opt.debug = max(opt.debug, 1)
    # Detector = detector_factory[opt.task]
    # detector = Detector(opt)
    ret = detector.run(img)
    res_dict = ret['results']
    global res                             # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 最终结果字典
    res = []
    # print('ret:', ret)
    # print('res_dict:', res_dict)
    #　=================
    res_list = res_dict[1].tolist()  # array数据转换成列表  # res_dict的键为1，所以是res_dict[1]
    ring_bbox = []
    for bbox in res_list:
        aspect_ratio = (bbox[3] - bbox[1]) / (bbox[2] - bbox[0])  # 得到检测框的横纵比(h/w)
        if bbox[-1]>0.1 and (aspect_ratio < 5): # 检测框的h/w不能大于5，也就是检测框不能太细
            for i in range(len(bbox)-1): # this for-loop transfer coord of bbox from float to int
                bbox[i] = round(bbox[i],3)  # 保留3位小数
            ring_bbox.append(bbox)
    print("     ring_bbox:", ring_bbox, len(ring_bbox))
    dropper_bbox = merge_ring_bbox(ring_bbox)  # dropper_bbox = [[ltx,lty,rbx,rby],...]各个匹配后的dropper坐标
    # im_data = draw_img(dropper_bbox, img)
    #=====================

    #=====================
    res_list = res_dict[2].tolist()  # array数据转换成列表  # res_dict的键为2，所以是res_dict[1]
    bad_ring_bbox = []
    for bbox in res_list:
        aspect_ratio = (bbox[3] - bbox[1]) / (bbox[2] - bbox[0])  # 得到检测框的横纵比(h/w)
        if bbox[-1] > 0.1 and (aspect_ratio < 5):  # 检测框的h/w不能大于5，也就是检测框不能太细
            for i in range(len(bbox) - 1):  # this for-loop transfer coord of bbox from float to int
                bbox[i] = round(bbox[i], 3)  # 保留3位小数
                bad_ring_bbox.append(bbox)
    print("     bad_ring_bbox:", bad_ring_bbox, len(bad_ring_bbox))
    #=====================
    # im_data = draw_img(dropper_bbox, bad_ring_bbox, img)

    for i in range(len(bad_ring_bbox)):  #   直接把 bad_ring的坐标加入res中
        tmp_list = []
        tmp_list.append("bad")
        tmp_bbox_list = [int(bad_ring_bbox[i][0]), int(bad_ring_bbox[i][1]), int(bad_ring_bbox[i][2]), int(bad_ring_bbox[i][3])]
        tmp_bbox_list = tansfer_bbox2(tmp_bbox_list)
        tmp_list.append(tuple(tmp_bbox_list))
        res.append(tmp_list)


    return ring_bbox, dropper_bbox # ring_bbox is a 2d list contains bbox of all rings

    #ret = {'results': results, 'tot': tot_time, 'load': load_time,
            # 'pre': pre_time, 'net': net_time, 'dec': dec_time,
            # 'post': post_time, 'merge': merge_time}

def get_dropper_line(ring_bbox, dropper_bbox): # 得到两个匹配的ring中间加的直线区域
    line_bbox = []
    for item in dropper_bbox:
        line = []
        for i in range(len(ring_bbox)):
            if item[0] == ring_bbox[i][0]:
                line_tlx = ring_bbox[i][0]
                line_tly = ring_bbox[i][3]
            if item[2] == ring_bbox[i][2]:
                line_brx = ring_bbox[i][2]
                line_bry = ring_bbox[i][1]
        line_bbox.append([line_tlx,line_tly,line_brx,line_bry])
    print('     line_bbox: ', line_bbox)
    return line_bbox

def make_list_int(float_list):
    for i in range(len(float_list)):
        float_list[i] = int(float_list[i])
    return float_list

# model = generate_model()
# model.cuda()

def classify_line(img, line_bbox, dropper_bbox, model):  # 两个匹配的ring中间加的直线区域进行分类
    dir_for_classify = './calssify_dropper_line/dir_for_classify'
    shutil.rmtree(dir_for_classify)  # 清除文件夹中图片
    if not os.path.exists(dir_for_classify):
        os.makedirs(dir_for_classify)
    full_img = cv2.imread(img)
    for key,item in enumerate(line_bbox):
        line = full_img[int(item[1]):int(item[3]), int(item[0]-5):int(item[2]+5)]   # y0:y1,x0:x1
        line_img_path = os.path.join(dir_for_classify,'tmp_'+str(key)+'.jpg')
        cv2.imwrite(line_img_path, line)
    dir_for_classify_path = './calssify_dropper_line/dir_for_classify/'
    label_list = calssify(model, dir_for_classify_path)
    # shutil.rmtree(dir_for_classify)  # 清除文件夹中图片
    # if not os.path.exists(dir_for_classify):
    #     os.makedirs(dir_for_classify)
    print('     label_list:', label_list)
    bad_line_crood = []
    line_bbox2 = tansfer_bbox(line_bbox)  # bbox[ltx, lty, rbx, rby] - --> bbox[cx, cy, w, h]
    for key1,label in enumerate(label_list):
        tmp_list = []
        if label == 1:  # # bad!!!!!!
            tmp_list.append("bad")
            tmp_list.append(tuple(make_list_int(line_bbox2[key1])))
            res.append(tmp_list)
            # cnt = 0
            # for item in dropper_bbox:
            #     for i in range(4):
            #         if item[i] in line_bbox[key1]: # 遇见有问题的line，就把相关的dropper加入res['bad']
            #             res["bad"] = item
            #             break
            #         else:
            #             cnt += 1
            #         if cnt == 3:
            #             res["dropper"] = item
        if label == 0:  # good !!!
            tmp_list.append("dropper")
            tmp_list.append(tuple(make_list_int(line_bbox2[key1])))
            res.append(tmp_list)
    # print("res:", res)
    return res

class DetectDropper(object):
    def __init__(self):
        self.opt = opts().init()
        self.Detector = detector_factory[self.opt.task]
        self.detector = self.Detector(self.opt)
        # self.model = generate_model()
        self.model = get_net()
        self.model.cuda()

    def runMain(self, img):
        ring_bbox, dropper_bbox = demo(self.opt, img, self.detector)
        line_bbox = get_dropper_line(ring_bbox, dropper_bbox)
        result = classify_line(img, line_bbox, dropper_bbox, self.model)
        # print("result", result)
        im_data = draw_img(result, img)
        flag1 = 0
        flag2 = 0
        detection_label = []
        if len(result) != 0:
            for i in range(len(result)):
                detection_label.append(result[i][0])
                if 'bad' in detection_label and 'dropper' in detection_label:
                    flag1, flag2 = 1, 1
                elif 'bad' not in detection_label and 'dropper' in detection_label:
                    flag1, flag2 = 1, 0
                elif 'bad' in detection_label and 'dropper' not in detection_label:
                    flag1, flag2 = 0, 1
            return flag1, flag2, res, im_data
            # for item in res:
            #     #print(res)
            #     if item[0] == 'dropper': # 吊弦的置信度较高
            #         flag1 = 1
            #     if item[0] == 'bad':
            #         flag2 = 2
            #     #elif item[0] == 'somkehand':
            #         #flag = False
            #     return flag1,flag2,im_data
        else:
            return flag1, flag2, result, im_data

    def run(self, img):
        flag1, flag2, result, im_data = self.runMain(img)
        # print(multiprocessing.current_process().name)
        # print(os.getgid())
        return flag1, flag2, result, im_data

# def det_img(opt, img):
#     ring_bbox, dropper_bbox = demo(opt, img)
#     return ring_bbox, dropper_bbox

# def det_imgdir(opt, imgdir, savedir):
#     os.environ['CUDA_VISIBLE_DEVICES'] = opt.gpus_str
#     # opt.debug = max(opt.debug, 1)
#     Detector = detector_factory[opt.task]
#     detector = Detector(opt)  # 这些语句提出来就只用初始化一次模型
#
#     for key, img in enumerate(os.listdir(imgdir)):
#         try:
#             imgpath = os.path.join(imgdir, img)
#             saveptah = os.path.join(savedir, img)
#             print("processing %d img : %s" % (key + 1, imgpath))
#             # main process
#             ret = detector.run(imgpath)
#             res_dict = ret['results']
#             # print('ret:', ret)
#             # print('res_dict:', res_dict)
#             res_list = res_dict[1].tolist()  # array数据转换成列表
#             ring_bbox = []
#             for bbox in res_list:
#                 aspect_ratio = (bbox[3] - bbox[1]) / (bbox[2] - bbox[0])  # 得到检测框的横纵比(h/w)
#                 if bbox[-1] > 0.1 and (aspect_ratio < 5):  # 检测框的h/w不能大于5，也就是检测框不能太细
#                     for i in range(len(bbox) - 1):  # this for-loop transfer coord of bbox from float to int
#                         bbox[i] = int(bbox[i])
#                     ring_bbox.append(bbox)
#             # print("ring_bbox:", ring_bbox, len(ring_bbox))
#             # draw_img(tansfer_bbox(ring_bbox),img)
#             dropper_bbox = merge_ring_bbox(ring_bbox)
#             im_data = draw_img(dropper_bbox, imgpath)
#             cv2.imwrite(saveptah, im_data)
#         except Exception as e:
#             print("!!!error:",e)

if __name__ == '__main__':
    detector = DetectDropper()
    # flag1, flag2, res, im_data = detector.run('/home/xidian/zy/3railway/dropper1/C0006_804_12060_b.jpg')
    # print(res)
    # cv2.imshow('test', im_data)
    # cv2.cv2.waitKey(0)


    img_dir = '/home/xidian/zy/3railway/broken_dropper'
    # img_dir = '/home/xidian/zy/CenterNet-master/data/coco/images/test2017'
    for item in os.listdir(img_dir):
        img_path = os.path.join(img_dir, item)
        print('\nimg_path:', img_path)
        flag1, flag2, res, im_data = detector.run(img_path)
        print(flag1, flag2, res)
        cv2.imshow('test', im_data)
        cv2.cv2.waitKey(0)

    # opt = opts().init()
    # img = '/home/zy/zy/CenterNet-master/data_cls1/coco/images/test2017/00000026.jpg'
    # ring_bbox, dropper_bbox = det_img(opt, img)
    # line_bbox = get_dropper_line(ring_bbox, dropper_bbox)
    # result = classify_line(img, line_bbox, dropper_bbox)
    #
    # imgdir = '/home/zy/zy/CenterNet-master/data_cls1/coco/images/test2017'
    # savedir = '/home/zy/zy/CenterNet-master/testimg_dropper_result'
    # det_imgdir(opt, imgdir, savedir)


    #==========================
    #检测单张
    # opt = opts().init()
    # img = '/home/zy/zy/CenterNet-master/data/coco/images/test2017/00000051.jpg'
    # ring_bbox, dropper_bbox = demo(opt, img)
    #==========================

    #==========================
    #检测文件夹
    # opt = opts().init()
    # imgdir = '/home/zy/zy/CenterNet-master/data/coco/images/test2017'
    # savedir = '/home/zy/zy/CenterNet-master/testimg_dropper_result'
    # os.environ['CUDA_VISIBLE_DEVICES'] = opt.gpus_str
    # # opt.debug = max(opt.debug, 1)
    # Detector = detector_factory[opt.task]
    # detector = Detector(opt)  # 这些语句提出来就只用初始化一次模型
    #
    # for key,img in enumerate(os.listdir(imgdir)):
    #     print("processing %d img..."%(key+1))
    #     imgpath = os.path.join(imgdir, img)
    #     print(imgpath)
    #     saveptah = os.path.join(savedir, img)
    #     # main process
    #     ret = detector.run(imgpath)
    #     res_dict = ret['results']
    #     res_list = res_dict[1].tolist()  # array数据转换成列表
    #     ring_bbox = []
    #     for bbox in res_list:
    #         aspect_ratio = (bbox[3] - bbox[1]) / (bbox[2] - bbox[0])  # 得到检测框的横纵比(h/w)
    #         if bbox[-1] > 0.1 and (aspect_ratio < 5):  # 检测框的h/w不能大于5，也就是检测框不能太细
    #             for i in range(len(bbox) - 1):  # this for-loop transfer coord of bbox from float to int
    #                 bbox[i] = int(bbox[i])
    #             ring_bbox.append(bbox)
    #     # print("ring_bbox:", ring_bbox, len(ring_bbox))
    #     # draw_img(tansfer_bbox(ring_bbox),img)
    #     dropper_bbox = merge_ring_bbox(ring_bbox)
    #     im_data = draw_img(dropper_bbox, imgpath)
    #     cv2.imwrite(saveptah, im_data)
























