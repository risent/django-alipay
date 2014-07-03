# -*- coding: utf-8 -*-
import re
import logging
import urlparse
import types
import requests
from urllib import urlencode
from hashlib import md5

from .config import settings
from .utils import params_filter, build_mysign

# 网关地址
_GATEWAY = 'https://mapi.alipay.com/gateway.do?'
WAP_PAY_GW = 'http://wappaygw.alipay.com/service/rest.htm?'
HTTPS_VERIFY_URL = "https://mapi.alipay.com/gateway.do?service=notify_verify&";

# 即时到账交易接口
def create_direct_pay_by_user(tn, subject, body, total_fee):
    params = {}
    params['service']       = 'create_direct_pay_by_user'
    params['payment_type']  = '1'
    
    # 获取配置文件
    params['partner']           = settings.ALIPAY_PARTNER
    params['seller_email']      = settings.ALIPAY_SELLER_EMAIL
    params['return_url']        = settings.ALIPAY_RETURN_URL
    params['notify_url']        = settings.ALIPAY_NOTIFY_URL
    params['_input_charset']    = settings.ALIPAY_INPUT_CHARSET
    params['show_url']          = settings.ALIPAY_SHOW_URL
    
    # 从订单数据中动态获取到的必填参数
    params['out_trade_no']  = tn        # 请与贵网站订单系统中的唯一订单号匹配
    params['subject']       = subject   # 订单名称，显示在支付宝收银台里的“商品名称”里，显示在支付宝的交易管理的“商品名称”的列表里。
    params['body']          = body      # 订单描述、订单详细、订单备注，显示在支付宝收银台里的“商品描述”里
    params['total_fee']     = total_fee # 订单总金额，显示在支付宝收银台里的“应付总额”里
    
    # 扩展功能参数——网银提前
    params['paymethod'] = 'directPay'   # 默认支付方式，四个值可选：bankPay(网银); cartoon(卡通); directPay(余额); CASH(网点支付)
    params['defaultbank'] = ''          # 默认网银代号，代号列表见http://club.alipay.com/read.php?tid=8681379
    
    # 扩展功能参数——防钓鱼
    params['anti_phishing_key'] = ''
    params['exter_invoke_ip'] = ''
    
    # 扩展功能参数——自定义参数
    params['buyer_email'] = ''
    params['extra_common_param'] = ''
    
    # 扩展功能参数——分润
    params['royalty_type'] = ''
    params['royalty_parameters'] = ''
    
    params = params_filter(params)
    sign = build_mysign(params, settings.ALIPAY_KEY)
    
    params['sign'] = sign
    params['sign_type'] = settings.ALIPAY_SIGN_TYPE
    
    return _GATEWAY + urlencode(params)


# 纯担保交易接口
def create_partner_trade_by_buyer (tn, subject, body, price):
    params = {}
    # 基本参数
    params['service']       = 'create_partner_trade_by_buyer'
    params['partner']           = settings.ALIPAY_PARTNER
    params['_input_charset']    = settings.ALIPAY_INPUT_CHARSET
    params['notify_url']        = settings.ALIPAY_NOTIFY_URL
    params['return_url']        = settings.ALIPAY_RETURN_URL

    # 业务参数
    params['out_trade_no']  = tn        # 请与贵网站订单系统中的唯一订单号匹配
    params['subject']       = subject   # 订单名称，显示在支付宝收银台里的“商品名称”里，显示在支付宝的交易管理的“商品名称”的列表里。
    params['payment_type']  = '1'
    params['logistics_type'] = 'POST'   # 第一组物流类型
    params['logistics_fee'] = '0.00'
    params['logistics_payment'] = 'BUYER_PAY'
    params['price'] = price             # 订单总金额，显示在支付宝收银台里的“应付总额”里
    params['quantity'] = 1              # 商品的数量
    params['seller_email']      = settings.ALIPAY_SELLER_EMAIL
    params['body']          = body      # 订单描述、订单详细、订单备注，显示在支付宝收银台里的“商品描述”里
    params['show_url'] = settings.ALIPAY_SHOW_URL
    
    params = params_filter(params)
    sign = build_mysign(params, settings.ALIPAY_KEY)
    
    params['sign'] = sign
    params['sign_type'] = settings.ALIPAY_SIGN_TYPE
    
    return _GATEWAY + urlencode(params)

# 确认发货接口
def send_goods_confirm_by_platform (tn):
    params = {}

    # 基本参数
    params['service']       = 'send_goods_confirm_by_platform'
    params['partner']           = settings.ALIPAY_PARTNER
    params['_input_charset']    = settings.ALIPAY_INPUT_CHARSET

    # 业务参数
    params['trade_no']  = tn
    params['logistics_name'] = u'银河列车'   # 物流公司名称
    params['transport_type'] = u'POST'
    
    params = params_filter(params)
    sign = build_mysign(params, settings.ALIPAY_KEY)
    
    params['sign'] = sign
    params['sign_type'] = settings.ALIPAY_SIGN_TYPE
    
    return _GATEWAY + urlencode(params)

def notify_verify(post):
    # 初级验证--签名
    _,prestr = params_filter(post)
    mysign = build_mysign(prestr, settings.ALIPAY_KEY, settings.ALIPAY_SIGN_TYPE)
    if mysign != post.get('sign'):
        return False
    
    # 二级验证--查询支付宝服务器此条信息是否有效
    verify_url = HTTPS_VERIFY_URL + "partner=" + partner + "&notify_id=" + notify_id
    req = requests.get(verify_url)
    
    if req.text == 'true':
        return True
    return False


def wap_trade_create(tn, subject, total_fee):
    """
    支付宝手机网站支付授权接口
    """
    params = {}
    params['service'] = 'alipay.wap.trade.create.direct'
    params['format'] = 'xml'
    params['v'] = '2.0'
    params['partner'] = settings.ALIPAY_PARTNER
    params['req_id'] = tn
    params['sec_id'] = settings.ALIPAY_SIGN_TYPE

    return_url = settings.ALIPAY_RETURN_URL
    notify_url = settings.ALIPAY_NOTIFY_URL
    merchant_url = settings.ALIPAY_MERCHANT_URL
    seller_email = settings.ALIPAY_SELLER_EMAIL
    
    req_data_tpl = '''<direct_trade_create_req><subject>%s</subject><out_trade_no>%s</out_trade_no><total_fee>%s</total_fee><seller_account_name>%s</seller_account_name><call_back_url>%s</call_back_url><notify_url>%s</notify_url><merchant_url>%s</merchant_url><pay_expire>3600</pay_expire></direct_trade_create_req>'''

    req_data = req_data_tpl % (subject, tn, total_fee, seller_email, return_url, notify_url, merchant_url)
    
    params['req_data'] = req_data
    params = params_filter(params)
    sign = build_mysign(params, settings.ALIPAY_KEY)
    params['sign'] = sign

    req = requests.post(WAP_PAY_GW, data=params)
    qs = urlparse.parse_qs(req.text)
    if qs.has_key('res_error'):
        return qs
    res_data = qs['res_data'][0]
    token = re.search(r'<request_token>(.*)</request_token', res_data).group(1)
    return token


def wap_auth_execute(tn, subject, token):
    """
    支付宝手机网站支付交易接口
    """
    params = {}
    params['service'] = 'alipay.wap.auth.authAndExecute'
    params['format'] = 'xml'
    params['v'] = '2.0'
    params['partner'] = settings.ALIPAY_PARTNER
    params['req_id'] = tn
    params['sec_id'] = settings.ALIPAY_SIGN_TYPE

    req_data_tpl = '''<auth_and_execute_req><request_token>%s</request_token></auth_and_execute_req>'''
    req_data = req_data_tpl % token
    params['req_data'] = req_data
    params = params_filter(params)
    sign = build_mysign(params, settings.ALIPAY_KEY)
    params['sign'] = sign
    return WAP_PAY_GW + urlencode(params)


def order_wap_pay(tn, subject, total_fee):
    """
    支付宝手机网站支付生成接口
    """
    token = wap_trade_create(tn, subject, total_fee)
    url = wap_auth_execute(tn, subject, token)
    return url

    
def wap_notify_verify(request, **kwargs):
    # 初级验证--签名
    from pyquery import PyQuery as PQ
    data = request.POST

    params = params_filter(data)
    mysign = build_mysign(params, settings.ALIPAY_KEY)
    
    if mysign != data.get('sign'):
        return False
    
    # 二级验证--查询支付宝服务器此条信息是否有效
    partner = settings.ALIPAY_PARTNER
    
    d = PQ(data)
    notify_id = d('notify_id').text()

    verify_url = HTTPS_VERIFY_URL + "partner=" + partner + "&notify_id=" + notify_id

    req = requests.get(verify_url)
    if req.text == 'true':
        return True
    else:
        return False
