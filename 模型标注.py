from collections import defaultdict
import json
import pandas as pd
from tqdm import tqdm
import csv
import argparse
import uuid
import time
import requests

url = "http://10.32.101.24:8090/llm/analyze"
headers = {
    'deviceId': 'deviceid12345',
    "content-type": "text/plain"
}
def create_batch_prompt(past_category_list, existing_standards, future_data_list, city_info):

    if existing_standards:
        standards_text = "\n".join([f"- {label}" for label in existing_standards[:50]])
    #     if len(existing_standards) > 100:
    #         standards_text += f"\n... 等共{len(existing_standards)}个标准标注"
    # else:
    #     standards_text = "暂无（这是第一批）"

    #上一批次的标注
    if past_category_list:
        past_category = "\n".join(past_category_list)
    else:
        past_category = "这是第一批"

    if future_data_list:
        future_data = "\n".join(future_data_list)
    else:
        future_data = "这是最后一批"
    print(city_info)
    if city_info:
        start_city = city_info[0]
        current_city = city_info[1]

    else: 
        start_city = "无"
        current_city = "无"


    prompt = f"""
    ### 角色定位
    你是一个具有高级常识推理与时空序列分析能力的用户行为分析 Agent。你的任务是综合用户的多维时序数据（时间、位置、运动状态、设备状态、应用交互），排除数据噪声，推断出用户当前正在进行的真实生活场景，并维持上下文的状态连贯性。

    ### 核心推断法则（最高优先级）
    1. **证据链优先级法则（解决POI漂移与噪声）**：
       - 判断用户真实行为的权重顺序为：**应用交互行为 = 停留时长/运动速度 > 设备状态(如充电) > POI标签**。
       - **POI交叉验证**：绝对不能仅凭POI下结论。例如，深夜在“医院”POI，如果在玩游戏/充电且长时静止，大概率是住院陪护或周边居民，而不是“就诊”；在“商场”POI持续8小时并使用办公软件，大概率是商场内的工作人员，而不是“购物”。
    2. **场景生命周期与接续法则（解决状态断裂）**：
       - 场景具有物理世界的连续性。任何状态的切换必须符合常理（例如：不能从“居家睡眠”瞬间突变为“商场购物”，中间必然存在“移动/通勤”的过渡场景）。
       - **状态继承**：如果当前时间点没有强有力的证据表明场景已切换（如位置没大变、没有新的特征App出现），则**默认继承**上一时间点的场景状态。
    3. **动态颗粒度法则**：
       - 当证据充分时（明确的地点+特定的App组合），输出高颗粒度场景（如 `静止#娱乐#在电影院看电影`）。
       - 当数据模糊或处于GPS漂移时，输出低颗粒度/兜底场景（如 `相对静止#日常驻留#室内活动` 或 `移动#位置转移#户外移动中`），绝不强行瞎猜。

    ### 上下文全局状态
    - 前序批次尾部场景（作为当前判断的逻辑起点，必须平滑接续）：
        {past_category}
    - 后续批次头部数据（用于反推当前所处状态的生命周期）：
        {future_data}
    - 始发城市：{start_city}
    - 当前城市：{current_city}

    ### 已用的标准类别参考
    请参考以下已存在的类别。如果当前推断与现有类别语义匹配度>80%，请优先复用，以控制标签数量膨胀；如果不匹配，请按照规范格式创造新类别：
    {standards_text}

    ### 通用场景分类学（Taxonomy）与命名规范
    请严格按照 `[物理状态]#[一级活动分类]#[具体场景描述]` 的三段式格式输出场景。
    - **物理状态**：仅限 `静止`、`移动` 两种。
    - **一级活动分类**（建议但不限于）：`生活起居`、`交通出行`、`工作学习`、`休闲娱乐`、`餐饮美食`、`购物消费`、`医疗保健`、`未知/模糊驻留`。
    - **具体场景描述**：简明扼要，体现具体行为（如 `夜间睡眠`、`市内乘车`、`餐厅就餐`、`办公室内工作`）。

    ### 推理与打分逻辑 (置信度 0-100)
    1. **长时静止状态判定**：在同一区域（考虑GPS小幅漂移）停留 > 2小时。结合时段推断：夜间多为睡眠/驻留，白天多为工作/长时活动。置信度较高（80-95）。
    2. **显著移动状态判定**：移动速度 > 10km/h 或 距离产生公里级跳变。判定为交通状态。结合App（打车软件、地图、视频消遣）推断具体交通方式或状态。置信度较高（80-95）。
    3. **碎片化状态判定**：短时停留（<30分钟），常伴随外卖、扫码、拍照等零散App交互，通常为过渡性生活事务。
    4. **矛盾数据处理**：当应用数据与POI严重不符，或连续几条数据在相距甚远的POI横跳时，打低置信度（50-60），并降级归类为 `静止#未知驻留#室内活动` 或保留上一状态。

    ### 格式与输出要求
    你必须先输出“推理思考”（reasoning），运用常识对证据链进行交叉验证，再输出最终场景（scene）。
    严格按照以下 JSON 格式输出，不包含任何外部文本：

    ```json
    {{
        "responses": [
            {{
                "reasoning": "上一个状态是'办公'，当前时间为18:30，产生显著移动距离，且打开了地铁/公交乘车码及听歌App，推测进入下班通勤状态。",
                "scene": "移动#交通出行#下班通勤乘车#90"
            }},
            {{
                "reasoning": "凌晨03:00，当前POI显示为'三甲医院'，但处于持续静止和充电状态，应用仅有系统闹钟，结合前序状态，推断为在医院陪护或周边住宿休息，而非就诊。",
                "scene": "静止#生活起居#夜间驻留休息#85"
            }}
        ],
        "startCity": "XXX",
        "currentCity": "YYY"
    }}
    ```

    ### 致命错误红线（严禁触发）
    - 严禁在场景描述中包含具体的城市、行政区或地名！
    - 严禁在没有产生有效“移动距离/速度”的情况下，仅凭外卖App或购物App判定用户正在“外出购物/取餐”（可能只是在室内用手机下单）。
    - 严禁违背物理连续性（如：连续两条数据间隔仅1分钟，上一秒在“家中睡眠”，下一秒变成“商场购物”）。
    

    ### 正确示例
    下为正确示例可作为内容参考，格式请严格按照以下示例采用JSON输出：
    输入：
    日期：05-30，时间：14:22，工作日，城市：和田地区，行政区：和田市，移动6.2公里，移动速度5公里/小时，机场，静止，通话界面(系统)共51秒，交互7次；微信(聊天)共12秒，交互1次
    日期：05-30，时间：15:19，工作日，城市：和田地区，行政区：和田市，机场，相对静止，航旅纵横(飞机、选座、航班)共7秒，交互1次；微信(聊天)共449秒，交互3次；天天象棋(游戏)共344秒，交互2次
    日期：05-30，时间：16:30,工作日，城市：和田地区，行政区：和田市，静止，时钟(闹钟)共10秒，交互2次；今日头条(资讯、新闻、视频)共41秒，交互1次；音频管家(工具)共2秒，交互1次；酷狗音乐(音乐播放器)共23秒，交互1次
    日期：05-30，时间：19:37,工作日，城市：乌鲁木齐市，行政区：天山区，移动996.6公里，移动速度331公里/小时，静止，今日头条(资讯、新闻、视频)共120秒，交互3次；微信(聊天)共739秒，交互5次；南方航空(酒店、机票、旅游)共34秒，交互1次
    日期：05-30，时间：20:34,工作日，城市：乌鲁木齐市，行政区：天山区，已连接，正在充电，相对静止，华为信息(通讯)共56秒，交互1次；微信(聊天)共256秒，交互3次
    输出：
    ```json
    {{
    "responses": [
        "出行#抵达始发机场#90",
        "出行#机场内活动#90",
        "出行#机场内活动#90",
        "出行#抵达终点机场#90",
        "出行#离开终点机场#90"
  ]
    "startCity": "和田地区",
    "currentCity": "乌鲁木齐市"
    }}
    ```

    以下是当前批次的用户数据，请开始通用场景推断：
    """

    return prompt


def send_to_api(session, content, session_id,prompt):
    data = {
        "session": {"sessionId": session_id},
        "body": {
             "apiKey": "AccessService",
    "modelName": "AGENT-DEEPSEEK-V3",
    "modelName1": "AGENT-DEEPSEEK-V3-BASE",
    "modelName2": "AGENT-ARKTS-DEEPSEEK-V3-SFT",
            "messages": [
                {"content": prompt, "role": "system"},
                {"content": content, "role": "user"}
            ]
        }
    }
    try:
        response = session.post(url, headers=headers, json=data, timeout=5000)
        response.raise_for_status()
        text_response = response.text
        data_str = json.loads(text_response)
        data_dict = json.loads(data_str)
        text = data_dict["modelRequestInfo"]["contentBean"]["text"]
        start = text.find("json")
        end = text.find("```", start)
        print(text[start+4:end])
        return text[start+4:end]
    except Exception as e:
        raise RuntimeError(f"API请求失败: {str(e)}")

def split_into_batches(data, batch_size):
    return [data[i:i+batch_size] for i in range(0, len(data), batch_size)]

def get_future_data(next_batch):
    if not next_batch:
        return None
    num_15_percent = max(1, int(len(next_batch) * 0.15))
    return next_batch[:num_15_percent]

def process_batches(timestamp, batches, udid, existing_standards):
    session_id = str(uuid.uuid4())
    sleep_time = 0.5  
    max_retries = 4  
    past_category_list = []
    city_info = [] # 0:start_city, 1: 
    results = []
    with requests.Session() as session:
        for i, current_batch in enumerate(batches):
            next_batch = batches[i+1] if i+1 < len(batches) else None
            future_data = get_future_data(next_batch)
            combined_text = "\n".join(current_batch)
            retries = 0
            while retries < max_retries:
                try:
                    prompt = create_batch_prompt(past_category_list, existing_standards, future_data, city_info)
                    response = send_to_api(session, combined_text, session_id, prompt)
                    response_data = json.loads(response)
                    responses_list = response_data.get("responses", [])
                    num_responses = len(responses_list)
                    if num_responses > 0:
                        num_15_percent = max(1, int(num_responses * 0.15))
                        past_category_list = responses_list[-num_15_percent:]
                    if  i == 0:
                        city_info.append(response_data.get("startCity", []))  
                        city_info.append(response_data.get("currentCity", []))

                    else:
                        city_info[1] = response_data.get("currentCity", [])
                                

                    # Prepare results for current batch
                    results.extend([[udid, timestamp, resp, current_batch[i]] for i, resp in enumerate(responses_list)])
                    break
                except Exception as e:
                    retries += 1
                    if retries < max_retries:
                        print(f"发生错误：{e}，正在重试")
                        time.sleep(sleep_time)  
                    else:
                        error_msg = f"ERROR: {str(e)} - UDID: {udid}"
                        results.extend([[error_msg] for _ in current_batch])
                        break
            # 写入文件
            with open(output_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if f.tell() == 0:
                    writer.writerow(["udid", "request", "text"])
                writer.writerows(results)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_udid', type=str, default=None, help='起始UDID')
    args = parser.parse_args()
    start_udid = args.start_udid
    batch_n = 30
    data_groups = defaultdict(list)

    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamp = row['TIME']
            udid = row['UDID']
            text = row['TEXT']
            data_groups[udid].append(text)

    udid_num = 0
    with tqdm(total=len(data_groups), desc="总进度", unit="udid") as pbar:
        for udid, group in sorted(data_groups.items()):
            if start_udid is not None and udid < start_udid:
                continue
            udid_num += 1
            pbar.set_description(f"处理UDID {udid}")
            batches = split_into_batches(group, batch_n)
            process_batches(timestamp, batches, udid, existing_standards)
            pbar.update(1)

    print(f"所有记录已处理，共生成{udid_num}个udid，输出文件：标注/更新标注_all.csv")

if __name__ == "__main__":
    input_file = "语义化test.csv"
    output_file = "标注/7.22.csv"
    label_file = "llm标注再处理/label_large.csv"
    df = pd.read_csv(label_file, header=None)
    existing_standards = df[0].tolist()
    main()
