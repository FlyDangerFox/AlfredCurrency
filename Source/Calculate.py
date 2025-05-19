#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-

import sys
import os
import json
from CurrencyExchange import CurrencyExchange

# 从环境变量获取API密钥
app_key = os.getenv('app_key')
if not app_key:
    print(json.dumps({
        'items': [{
            'title': '错误',
            'subtitle': '请在Alfred工作流环境变量中设置app_key',
            'arg': ''
        }]
    }))
    sys.exit(1)

# 获取参数
if len(sys.argv) < 4:
    print(json.dumps({
        'items': [{
            'title': '参数不足',
            'subtitle': '请提供源货币、目标货币和金额',
            'arg': ''
        }]
    }))
    sys.exit(1)

# 源货币
original_currency = sys.argv[1]
# 目标货币
destination_currency = sys.argv[2]
# 输入金额
try:
    input_amount = float(sys.argv[3].replace(",", ""))
except ValueError:
    print(json.dumps({
        'items': [{
            'title': '无效金额',
            'subtitle': '请提供有效的数字金额',
            'arg': ''
        }]
    }))
    sys.exit(1)

# 创建CurrencyExchange实例并计算
try:
    currency_exchange = CurrencyExchange(app_key)
    currency_exchange.calculate(original_currency, destination_currency, input_amount)
except Exception as e:
    print(json.dumps({
        'items': [{
            'title': '计算错误',
            'subtitle': f'发生错误: {str(e)}',
            'arg': ''
        }]
    }))
