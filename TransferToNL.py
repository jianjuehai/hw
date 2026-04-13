import pandas as pd
from datetime import datetime
import json
import csv
import gc
from tqdm import tqdm
import math
import numpy as np
import re

inputfile = "单框架5d去重_0328_history_merge.csv"
outputfile = "单框架5d去重_0328_语义化.csv"

# 读取 Excel 文件获得poi字典和包名对应app
poi_df = pd.read_excel("poi和包名/Huawei_POI_Chinese.xlsx",  dtype={'types': str})
pcg_df_single = pd.read_csv("poi和包名/单框架应用包名与分类_合并.csv")
pcg_df_double = pd.read_csv("poi和包名/应用类型TopN_更新.csv")

# 创建类型映射字典
poi_mapping = {}
for _, row in poi_df.iterrows():
    types_code = row["types"]
    
    # 按优先级获取分类名称
    category_name = next(
    (row[level] for level in ["第二级", "第一级"] if pd.notna(row[level])),
    "未分类"
    )
    poi_mapping[types_code] = category_name
# 单框架包名转换字典
pkg_mapping_single = {}
for _, row in pcg_df_single.iterrows():
    package_name = row["bundleName"]
    describ = next(
        (row[level] for level in ["tag_new", "type3", "type2", "分类名字2", "分类名字"] if pd.notna(row[level])),
        ''
    )
    describ_list = describ.split("#")
    # 构建嵌套字典
    nested_dict = {
        "app_cn_name": row["appName"],
        "category": ("、").join(describ_list[:3]) ,  # 如休闲益智游戏
    }
    pkg_mapping_single[package_name] = nested_dict
    
# 双框架包名转换字典
pkg_mapping_double = {}
for _, row in pcg_df_double.iterrows():
    package_name = row["package_name"]
    describ = next(
    (row[level] for level in ["tags_new", "tags", "type3", "type2"] if pd.notna(row[level]))
    )
    describ_list = describ.split("#")
    # 构建嵌套字典
    nested_dict = {
        "app_cn_name": row["app_cn_name"]if pd.notna(row["app_cn_name"]) else row["package_name"],
        "category": ("、").join(describ_list[:3]) ,  # 如休闲益智游戏
    }
    pkg_mapping_double[package_name] = nested_dict

def convert_unix_timestamp(ts):
    """将13位Unix时间戳转换为可读格式"""
    dt = datetime.fromtimestamp(int(ts)/1000)
    time = dt.strftime('%Y/%m/%d %H:%M')

     # 获取星期几（0=周一, 6=周日）
    day_of_week = dt.weekday()
    
    # 获取小时
    hour = dt.hour
    
    # 定义星期几的中文名称
    days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    
    # 定义时间段
    if 6 <= hour < 12:
        period = "上午"
    elif 12 <= hour < 18:
        period = "下午"
    elif 18 <= hour < 24:
        period = "晚上"
    else:
        period = "凌晨"
    
    time_text = f"{days[day_of_week]}{period}"
    # 返回结果
    return time_text, time


# 计算距离变化
def haversine(lat1, lon1, lat2, lon2):
    # 地球半径，单位为公里
    R = 6371.0
    # 将经纬度从度转换为弧度
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # 计算经纬度的差值
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine 公式
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # 计算距离
    distance = R * c
    return distance


def process_service_records(records):
    """解析服务使用记录并排序"""
    parsed = []
    # 预处理：将字符串转换为合法JSON格式
    try:
        records_list = json.loads(records)
        # 检查是否为列表类型
        if not isinstance(records_list, list):
            raise ValueError("records_list 应该是一个列表，但接收到的类型是: " + str(type(records_list)) + "，内容: " + str(records_list))
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}")
        return parsed
    except Exception as e:
        print(f"其他错误: {e}")
        return parsed

    # 解析每条记录
    for record_str in records_list:
        if not record_str.strip():
            continue

        # 分割字段并处理空值
        try:
            parts = [p.strip() for p in record_str.split(",")]
            parts = ["null" if p == "" else p for p in parts]  # 统一空值标记
        except Exception as e:
            print(f"字段分割错误: {e} | 原始数据: {record_str}")
            continue

        # 防御式索引检查（关键字段索引根据实际数据结构调整）
        required_indices = [2, 8, 9]
        if len(parts) < max(required_indices) + 1:
            print(f"字段缺失，跳过记录: {record_str}")
            continue
            
        # 只保留click服务
        if parts[0] != "click":
            continue

        # 检查时间戳是否有效
        try:
            if int(parts[8]) <= 0:
                continue
        except ValueError as e:
            print(f"时间戳转换错误: {e} | 原始数据: {record_str}")
            continue

        # 解析记录数据
        def get_pkg_info(pkg_name: str):
            if pkg_name in pkg_mapping_single:
                return pkg_mapping_single[pkg_name]
            if pkg_name in pkg_mapping_double:
                return pkg_mapping_double[pkg_name]
            return {}
        info = get_pkg_info(parts[2])
        
        try:
            package = info.get("app_cn_name", parts[2])
            category_name = info.get("category", "")
            duration = int(parts[9]) if parts[9] not in ["null", ""] else 0
            timestamp = convert_unix_timestamp(parts[8])

            record_data = {
                "package": package,
                "category_name": category_name,
                "duration": duration,
                "timestamp": timestamp
            }
            parsed.append(record_data)
        except Exception as e:
            print(f"记录解析异常: {e} | 原始数据: {record_str}")
            continue

    return parsed
    # 按时间排序（处理可能的无效时间）
    # return sorted(
    #     parsed,
    #     key=lambda x: x["timestamp"] if x["timestamp"] != "未知时间" else "0000-00-00 00:00:00"
    # )


def process_chunk(chunk):
    last_udid = None
    global last_record_dict
    output = []
    i = 0
    for _, row in chunk.iterrows():
        udid = row["udid"]
        
        # 生成原始数据列
        original_row = []
        for col_name, col in row.items():
            if col_name in ["actions", "unionPreActions0_5", "unionPreActions5_20", "pre_candi"]:
                continue  # 跳过指定列
            val = str(col) if pd.notna(col) else ''
            original_row.append(val)
        original_data = '|'.join(original_row)
        
        action = row["actions"]
        
        # 处理POI信息
        if pd.isna(row["poiTypeCode"]):
            poi_code_list = []
        else:
            try:
                data = json.loads(row["poiTypeCode"])
                poi_code_list = data if data and len(data) > 0 else []
            except json.JSONDecodeError:
                poi_code_list = []

        seen_poi = set()
        poi_list = []
        for poi_code in poi_code_list:
            poi = poi_mapping.get(poi_code, "")
            if poi and poi not in seen_poi:
                poi_list.append(poi)
                seen_poi.add(poi)

        poi_text = "POI：" + "、".join(poi_list) + "，" if poi_list else ""
                

        # 城市信息
        city_info = row["city"] if pd.notna(row["city"]) else ""
        # region_info = row["district"] if pd.notna(row["district"]) else ""

        # 设备状态解析
        wifi_status = "已连接" if row["wifiConnectState"] == "CONNECTED" else "未连接"

        workday = "工作日" if row["personaWorkDay"] == 1 else "休息日"

        # 计算经纬度距离
        distance = 0
        distance_text = ""
        if udid in last_record_dict and last_record_dict[udid] is not None:
            last_row = last_record_dict[udid]
            last_longla_info = (last_row["longitude"], last_row["latitude"])
            last_city = last_row["city"]
            distance = haversine(last_longla_info[1], last_longla_info[0], row["latitude"], row["longitude"])
            time_diff = abs(row["timeStamp"] - last_row["timeStamp"])/1000/60
            if distance > 1:
                if last_city == city_info:
                    city_text = "市内"
                else:
                    city_text = "跨城市"

                speed = distance / (time_diff / 60) if time_diff > 0 else 0
                
                if speed <= 30:
                    speed_text = "低速"
                else:
                    speed_text = "高速"
                
                distance_text = f"前{time_diff:.0f}分钟从{last_city}{city_text}{speed_text}移动，"

        # 合并所有服务使用记录
        all_services = []
        for field in ["unionPreActions0_5", "unionPreActions5_20"]:
            if pd.isna(row[field]):
                continue
            all_services.extend(process_service_records(row[field]))
       
        if row["timeStamp"] == 0:
            continue
        else:
            time_text, time = convert_unix_timestamp(row["timeStamp"])
            
        # 生成使用记录文本
        stats = {}
        if all_services != []:
            for service in all_services:
                if service['package'] not in stats:
                    stats[service['package']] = {'total_duration': 0, 'count': 0, 'category': service['category_name']}
                stats[service['package']]['total_duration'] += service['duration']
                stats[service['package']]['count'] += 1
            # 生成统计文本
            stats_text = []
            for pkg, data in stats.items():
                if data['category'] != "":
                    if data['total_duration'] > 60000:
                        stats_text.append(f"{pkg}共{data['total_duration']/1000/60:.0f}秒，交互{data['count']}次")
                    elif data['total_duration'] > 1000:
                        stats_text.append(f"{pkg}({data['category']})共{data['total_duration']/1000:.0f}秒，交互{data['count']}次")
        else:
            stats_text = "无"

       # 组装完整段落
        text = f"""
时间：{time}{time_text}，{workday}，城市：{city_info}，{poi_text}{distance_text}Wifi{wifi_status}，应用记录：{"；".join(stats_text)}
"""
        # 将udid和生成的文本一起存入output
        output.append({
            "time": time, "udid": udid, "text": text.strip(), "context": original_data, "history_usage":row['pre_candi'] ,"actions": action
        })
        
        # 处理
        if last_udid is not None and last_udid != udid and last_udid in last_record_dict:
            # 只保留当前udid
            del last_record_dict[last_udid]
        # 更新dict
        last_record_dict[udid] = {
            'longitude': row['longitude'],
            'latitude': row['latitude'],
            'timeStamp': row['timeStamp'],
            'city': row['city']
        }
        last_udid = udid

        i += 1

    # 写入当前chunk的结果
    write_to_csv(output)
    # 释放内存
    del output
    gc.collect()


def write_to_csv(data):
    with open(outputfile, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in data:
            writer.writerow([row["time"], row["text"], row['udid'], row['context'], row['history_usage'], row['actions']])

# 主程序
if __name__ == "__main__":
    # 写入CSV标题
    with open(outputfile, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(['time', 'text', 'udid', 'context', 'history_usage', 'service_click'])
    
    # 分块处理CSV
    chunk_size = 100000  # 根据内存调整
    
    # 设置起始块数（从0开始计数）
    start_chunk = 0  # 可修改为想要开始的块数
    
    # 维护一个字典来存储每个udid的上一条记录
    last_record_dict = {}
    
    # 添加进度条
    with tqdm(unit="块", desc="处理进度") as pbar:
        for chunk_num, chunk in enumerate(pd.read_csv(inputfile, chunksize=chunk_size)):
            # 跳过起始块之前的块
            if chunk_num < start_chunk:
                pbar.update(1)
                continue
                
            process_chunk(chunk)
            pbar.update(1)
            del chunk
            gc.collect()
            
    
    print("转换完成，生成 语义化_new.csv")
