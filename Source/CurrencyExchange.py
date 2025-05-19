#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import urllib.parse
from urllib import request
import json
import os
import time


class CurrencyExchange:
    # 更新API地址
    currency_list_api = "http://op.juhe.cn/onebox/exchange/list"
    exchange_rate_api = "http://op.juhe.cn/onebox/exchange/currency"
    
    # 缓存文件路径
    cache_dir = os.path.expanduser("~/.alfred_currency_cache")
    currency_list_cache = os.path.join(cache_dir, "currency_list.json")
    exchange_rate_cache = os.path.join(cache_dir, "exchange_rate_cache.json")
    timestamp_cache = os.path.join(cache_dir, "timestamp.json")
    
    # 缓存过期时间（秒）
    CACHE_EXPIRY = 4 * 60 * 60  # 4小时

    def __init__(self, app_key):
        self.app_key = app_key
        # 确保缓存目录存在
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir )
        
        # 初始化缓存
        self._init_cache()

    def _init_cache(self):
        """初始化缓存文件"""
        if not os.path.exists(self.currency_list_cache):
            self._save_json(self.currency_list_cache, {"list": []})
        
        if not os.path.exists(self.exchange_rate_cache):
            self._save_json(self.exchange_rate_cache, {})
        
        if not os.path.exists(self.timestamp_cache):
            self._save_json(self.timestamp_cache, {"timestamps": {}})

    def _load_json(self, file_path):
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_json(self, file_path, data):
        """保存JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _is_cache_expired(self, cache_key=None):
        """检查缓存是否过期"""
        timestamp_data = self._load_json(self.timestamp_cache)
        timestamps = timestamp_data.get("timestamps", {})
        
        if cache_key is None:
            # 检查货币列表缓存
            last_update = timestamp_data.get("last_update", 0)
        else:
            # 检查特定货币对的缓存
            last_update = timestamps.get(cache_key, 0)
            
        current_time = int(time.time())
        return (current_time - last_update) > self.CACHE_EXPIRY

    def _update_timestamp(self, cache_key=None):
        """更新时间戳"""
        timestamp_data = self._load_json(self.timestamp_cache)
        current_time = int(time.time())
        
        if cache_key is None:
            # 更新货币列表时间戳
            timestamp_data["last_update"] = current_time
        else:
            # 更新特定货币对的时间戳
            if "timestamps" not in timestamp_data:
                timestamp_data["timestamps"] = {}
            timestamp_data["timestamps"][cache_key] = current_time
            
        self._save_json(self.timestamp_cache, timestamp_data)

    def get_currency_list(self):
        """获取货币列表并缓存"""
        # 如果缓存未过期，直接返回缓存数据
        if not self._is_cache_expired() and os.path.exists(self.currency_list_cache):
            cache_data = self._load_json(self.currency_list_cache)
            if cache_data.get("list"):
                return cache_data["list"]
        
        # 缓存过期或不存在，请求新数据
        param = {'key': self.app_key}
        param_string = urllib.parse.urlencode(param)
        url = self.currency_list_api + "?" + param_string
        
        try:
            with request.urlopen(url) as f:
                data = f.read()
                if f.status == 200:
                    content = data.decode('utf-8')
                    result = json.loads(content)
                    if result.get('error_code') == 0 and result.get('result', {}).get('list'):
                        # 更新缓存
                        self._save_json(self.currency_list_cache, result['result'])
                        self._update_timestamp()
                        return result['result']['list']
                    else:
                        print(f"获取货币列表失败: {result.get('reason', '未知错误')}")
                else:
                    print('请求失败')
        except Exception as e:
            print(f"获取货币列表异常: {str(e)}")
        
        # 如果请求失败，尝试使用缓存数据
        cache_data = self._load_json(self.currency_list_cache)
        return cache_data.get("list", [])

    def get_exchange_rate(self, from_currency, to_currency):
        """获取汇率并缓存"""
        cache_key = f"{from_currency}_{to_currency}"
        cache_data = self._load_json(self.exchange_rate_cache)
        
        # 如果缓存未过期，直接返回缓存数据
        if not self._is_cache_expired(cache_key) and cache_data.get(cache_key):
            return cache_data[cache_key]
        
        # 缓存过期或不存在，请求新数据
        param = {
            'key': self.app_key,
            'from': from_currency,
            'to': to_currency
        }
        param_string = urllib.parse.urlencode(param)
        url = self.exchange_rate_api + "?" + param_string
        
        try:
            with request.urlopen(url) as f:
                data = f.read()
                if f.status == 200:
                    content = data.decode('utf-8')
                    result = json.loads(content)
                    if result.get('error_code') == 0 and result.get('result'):
                        # 更新缓存
                        cache_data[cache_key] = result['result']
                        self._save_json(self.exchange_rate_cache, cache_data)
                        self._update_timestamp(cache_key)
                        return result['result']
                    else:
                        print(f"获取汇率失败: {result.get('reason', '未知错误')}")
                else:
                    print('请求失败')
        except Exception as e:
            print(f"获取汇率异常: {str(e)}")
        
        # 如果请求失败，尝试使用缓存数据
        return cache_data.get(cache_key, [])

    def calculate(self, original_currency, destination_currency, input_amount):
        """计算汇率转换结果"""
        # 获取汇率数据
        exchange_data = self.get_exchange_rate(original_currency, destination_currency)
        
        if not exchange_data:
            print(f"无法获取 {original_currency} 到 {destination_currency} 的汇率数据")
            return
        
        # 查找匹配的汇率
        for rate_info in exchange_data:
            if rate_info.get('currencyF') == original_currency and rate_info.get('currencyT') == destination_currency:
                exchange_rate = float(rate_info.get('exchange', 0))
                output_amount = input_amount * exchange_rate
                
                # 格式化输出
                subtitle = f"{input_amount} {original_currency} 转换为 {destination_currency}，汇率 {exchange_rate} = {output_amount}"
                output_dict = {'items': [{'title': f"{output_amount:.2f}", 'subtitle': subtitle, 'arg': f"{output_amount:.2f}"}]}
                print(json.dumps(output_dict))
                return
        
        print(f"未找到 {original_currency} 到 {destination_currency} 的汇率数据")
