import pandas as pd
from datetime import datetime
import json

# 读取 Excel 文件获得poi字典
# df = pd.read_excel("data.xlsx", engine="openpyxl")




# 示例数据映射（需根据实际数据补充）
poi_mapping = {
    "1101000000": "加油站",
    "0601000000": "医院",
    # 补充其他POI编码映射...
}

def convert_unix_timestamp(ts):
    """将13位Unix时间戳转换为可读格式"""
    return datetime.fromtimestamp(int(ts)/1000).strftime('%Y-%m-%d %H:%M:%S')

def get_serviceusage_info(record):
    # 分割字段并处理空值
    parts = [p.strip() for p in record.split(",")]
    parts = ["null" if p == "" else p for p in parts]  # 统一空值标识
        
    # 防御式索引检查（关键字段索引根据实际数据结构调整）
    required_indices = [0, 11, 15]
    if len(parts) < max(required_indices)+1:
         print(f"字段缺失，跳过记录: {record}")
            
    try:
        record_data = {
            "package": parts[0],  # 包名在第一个字段
            "duration": int(parts[11]) if parts[11] not in ["null", ""] else 0,
            "timestamp": convert_unix_timestamp(parts[15])
        }
    except Exception as e:
        print(f"记录解析异常: {str(e)} | 原始数据: {record}")
    return record_data["timestamp"], record_data["package"], record_data["duration"]


def process_service_records(records):
    """解析服务使用记录并排序"""
    parsed = []
    # 预处理：将字符串转换为合法JSON格式
    
    records_list = json.loads(records)

    
    # 解析每条记录
    for record_str in records_list:
        if not record_str.strip():
            continue
            
        # 分割字段并处理空值
        parts = [p.strip() for p in record_str.split(",")]
        parts = ["null" if p == "" else p for p in parts]  # 统一空值标识
        
        # 防御式索引检查（关键字段索引根据实际数据结构调整）
        required_indices = [0, 11, 15]
        if len(parts) < max(required_indices)+1:
            print(f"字段缺失，跳过记录: {record_str}")
            continue
            
        try:
            record_data = {
                "package": parts[0],  # 包名在第一个字段
                "duration": int(parts[11]) if parts[11] not in ["null", ""] else 0,
                "timestamp": convert_unix_timestamp(parts[15])
            }
            parsed.append(record_data)
        except Exception as e:
            print(f"记录解析异常: {str(e)} | 原始数据: {record_str}")
            continue
    
    # 按时间排序（处理可能的无效时间）
    return sorted(
        parsed,
        key=lambda x: x["timestamp"] if x["timestamp"] != "未知时间" else "0000-00-00 00:00:00"
    )



# 读取CSV数据
df = pd.read_csv("样例.csv")
# 结果存储
output = []

# 逐行遍历 DataFrame 的循环结构将 DataFrame 的每一行拆解为索引和行数据
for index, row in df.iterrows():
    # 基本信息解析
    timestamp, pkg, dur = get_serviceusage_info(row["serviceusage"])
    
    # row["hwpoiinfo"] = '[["0801000000","",""]]'
    if pd.isna(row["hwpoiinfo"]):  # 检查字段是否存在
        poi = "未知位置"
    else:  
        try:
            data = json.loads(row["hwpoiinfo"])  # 解析成 Python 列表
            poi_code = data[0][0] if data and data[0] else ""  # 提取第一个值
        except json.JSONDecodeError:
            poi_code = ""  # 解析失败时返回空
        poi = poi_mapping.get(poi_code, "未知位置")

    
    # 设备状态解析
    wifi_status = "已连接" if row["wificonnectedstate"] == 1 else ("未连接" if row["wificonnectedstate"] == 0 else "未知状态")
    bt_status = "已连接" if row["bluetoothconnectedstate"] == 1 else ("未连接" if row["bluetoothconnectedstate"] == 0 else "未知状态")
    motion_state = row["motionstate"]
    
    # 合并所有服务使用记录
    all_services = []
    for field in ["unionpreserviceusages", "unionpostserviceusages", "unionfutureserviceusages"]:
        if pd.isna(row[field]):  # 检查字段是否存在
            continue
        all_services.extend(process_service_records(row[field]))
 
    # 生成使用记录文本
    usage_segments = []
    stats = {}
    for service in all_services:
        usage_segments.append(
            f"在{service['timestamp']}时使用{service['package']}持续{service['duration']/1000}秒"
        )
        if service['package'] not in stats:
            stats[service['package']] = {
                'total_duration': 0,
                'count': 0
            }
        stats[service['package']]['total_duration'] += service['duration']
        stats[service['package']]['count'] += 1
    
    # 生成统计文本
    stats_text = []
    for pkg, data in stats.items():
        stats_text.append(
            f"使用{pkg}共{data['total_duration']/1000}秒，期间交互{data['count']}次"
        )
    
    # 组装完整段落
    output.append(f"""
用户在{timestamp}正在使用{pkg}，持续时间{dur/1000}秒，此时POI信息是：{poi}。
Wifi{wifi_status}，蓝牙{bt_status}，运动状态：{motion_state}。在该时刻前后的服务使用记录如下：
{"，".join(usage_segments)}。
{"；".join(stats_text)}。
=====================================================
""")
print(output)

# 写入结果文件
with open("语义化.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("转换完成，生成 semantic_output.txt")