#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2017/11/30 下午2:35
# @Author : Matrix
# @Github : https://github.com/blackmatrix7/
# @Blog : http://www.cnblogs.com/blackmatrix/
# @File : methods.py
# @Software: PyCharm
import requests
from .configs import *
from datetime import datetime
from .exceptions import DingTalkExceptions

__author__ = 'blackmatrix'


def get_timestamp():
    """
    生成时间戳
    :return:
    """

    now = datetime.now()
    timestamp = datetime.timestamp(now)
    timestamp = int(round(timestamp))
    return timestamp


def get_request_url(access_token, method=None, format_='json', v='2.0', simplify='false', partner_id=None, url=None):
    """
    通用的获取请求地址的方法
    :param access_token:
    :param method:
    :param format_:
    :param v:
    :param simplify:
    :param partner_id:
    :param url:
    :return:
    """
    timestamp = get_timestamp()
    base_url = url or DING_METHODS_URL
    request_url = '{0}?method={1}&session={2}&timestamp={3}&format={4}&v={5}'.format(base_url, method, access_token,
                                                                                     timestamp, format_, v)
    if format_ == 'json':
        request_url = '{0}&simplify={1}'.format(request_url, simplify)
    if partner_id:
        request_url = '{0}&partner_id={1}'.format(request_url, partner_id)
    return request_url


def dingtalk_unpack_result(result):
    """
    统一钉钉的返回格式
    :param result:
    :return:
    """
    try:
        for k1, v1 in result.items():
            for k2, v2 in v1.items():
                if k2 == 'result' and isinstance(v2, dict):
                    return v2
            else:
                return result
        else:
            return result
    except AttributeError:
        return result


def dingtalk_resp(func):
    def wrapper(*args, **kwargs):
        resp = func(*args, **kwargs)
        data = resp.json()
        if resp.status_code == 200:
            # 针对钉钉几种有明确返回错误信息的情况进行处理
            if 'errcode' in data and data['errcode'] != 0:
                raise DingTalkExceptions.dingtalk_resp_err(http_code=resp.status_code,
                                                           err_code=data['errcode'],
                                                           err_msg=data.get('errmsg') or data['errcode'])
            elif 'error_response' in data and data['error_response']['code'] != 0:
                err_code = data['error_response'].get('sub_code') or data['error_response']['code']
                err_msg = data['error_response'].get('sub_msg') or data['error_response']['msg']
                raise DingTalkExceptions.dingtalk_resp_err(http_code=resp.status_code, err_code=err_code, err_msg=err_msg)
            else:
                # 对于一些返回格式不统一的接口，需要对返回的数据做拆解，再判断是否存在异常
                result = dingtalk_unpack_result(data)
                if result.get('is_success', True) is False or result.get('success', True) is False:
                    if 'error_response' in result:
                        err_code = result['error_response'].get('ding_open_errcode')
                        err_msg = result['error_response'].get('err_msg')
                    else:
                        err_code = result.get('ding_open_errcode')
                        err_msg = result.get('error_msg')
                    raise DingTalkExceptions.dingtalk_resp_err(http_code=resp.status_code, err_code=err_code, err_msg=err_msg)
                # 其他暂时无法明确返回错误的，直接返回接口调用结果
                else:
                    return data
        else:
            raise DingTalkExceptions.dingtalk_resp_err(http_code=resp.status_code,
                                                       err_code=data['errcode'],
                                                       err_msg=data['errmsg'])
    return wrapper


def call_dingtalk_webapi(access_token, method_name, http_method='POST', **kwargs):
    url = get_request_url(access_token, method_name)
    if http_method.upper() == 'POST':
        resp = requests.post(url, data=kwargs)
    else:
        resp = requests.get(url, params=kwargs)
    return resp
