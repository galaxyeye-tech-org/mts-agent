# -*- coding: utf-8 -*-

__author__ = r'wsb310@gmail.com'

import os

from script.config.setting import chosen_vector
from script.config.setting import DOC_CONF
from script.wrap.VecWrap import VecWrap

import pickle
import numpy as np

from service import ServiceBase

class TreeNodeHelper(ServiceBase):

    """
    对外提供服务的类
    """

    def __init__(self):
        
        super().__init__()

        self.vec_wrap = VecWrap(chosen_vector)

    def load_obj(self, file_obj):

        if not os.path.exists(file_obj):
            return None

        # 一个doc的obj文件
        with open(file_obj, 'rb') as f:
            node = pickle.load(f)  # 将二进制文件对象转换成 Python 对象
            return node

    def load_vec(self, file_npy):
        return np.load(file_npy)

    def travel(self, node_):
        raise NotImplementedError()

    def do_merge(self, this_node, final_nodes):

        # 自己本身已经有足够多的文本，不需要融合

        merged = False
        merged_node = this_node
        merged_idx = -1

        this_len = len(this_node.to_str())
        if this_len > DOC_CONF.merge_self_threshold:
            return merged, merged_node, merged_idx

        for idx, node in enumerate(final_nodes):

            try:
                if this_len + len(node.to_str()) > DOC_CONF.merge_concate_threshold:
                    continue
            except Exception as e:
                print(e)

            if this_node.is_brother(node):

                merged_node = this_node.find_father()

            elif this_node.is_ancestors(node):

                merged_node = this_node

            elif node.is_ancestors(this_node):

                merged_node = node

            if merged_node and merged_node != this_node:
                merged_idx = idx
                merged = True
                break

        return merged, merged_node, merged_idx

    def merge(self, topk_nodes):

        final_nodes = []

        for node in topk_nodes:
            this_node = self.travel(node)

            merged, merged_node, merged_idx = self.do_merge(this_node, final_nodes)

            if merged:
                del final_nodes[merged_idx]

            if merged_node is None:
                merged_node = this_node

            if merged_node not in final_nodes:
                final_nodes.append(merged_node)

        return final_nodes
