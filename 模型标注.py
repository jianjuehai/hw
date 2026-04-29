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
    ###角色定位
    你是一个具有时空推理能力的用户行为分析专家，需要综合分析多维度的时序数据，为每个时间点标注正在进行的最佳场景类别。
    ### 数据说明
    - 输入数据是一个用户一段时间的交互序列，每个时间都有对应的行为
    - 数据中会出现很多兴趣点，可能都是该位置附近的，需要结合上下文综合判断

    ### 重要原则
    **数据维度（独立证据）**：时间、移动距离、具体地点、应用、WIFI、充电状态等
    **平衡性原则**：既要避免创建重复类别，也要避免强行使用与数据不符的类别
    **连续性原则**：重视时间连续性，相邻时间点的场景应该保持合理的逻辑关系，避免频繁的场景切换
    **证据链原则**：每个判断需有≥2个数据维度支撑
    **结合上下文原则**：场景判断时必须参考上下文相关信息

    ### 上下文相关信息
    - 这是当前数据之前的场景：
        {past_category}
    - 这是当前数据之后的原数据：
        {future_data}
    
    - 始发城市：{start_city}
    - 当前城市：{current_city}
    - 终点地区
    - 主要活动模式
    - 最近的交通工具

    ### 已用的标准类别
    **仔细评估语义匹配度，避免强行使用不相关标注**
    {standards_text}

    **标签选择策略**
    - 依据当前数据推测场景与现有类别高度匹配(>90%)：直接映射到已有标签
    - 依据当前数据推测场景与现有类别中度匹配(70%-90%)：仔细评估，倾向于映射但可创造新类别
    - 依据当前数据推测场景与现有类别低度匹配(<70%)：应该创建新类别

    ### 场景判断逻辑
    1. 当前是否为出行相关场景
        - 是出行
            - 特殊工作：如送外卖、送货、网约车司机等户外工作的，或者机场、高铁站的工作人员（多天持续出现在高铁站或机场）
            - 旅游相关：有行程规划如“携程”“美团”“相机”等应用且跨城后GPS频繁变动，涉及出境需要明确区分
            - 交通方式：飞机、高铁、地铁、公交、驾车、网约车等
        - 非出行
            - 非出行场景：常驻城市居家、娱乐、办公、学习等静态场景，没有具体目的地（如散步、跑步）或短暂行为（如外卖点餐、寄取快递）。
            - 判断依据：移动距离未显示、地点为固定场所、应用以聊天/娱乐为主。
    2. 关键判断依据
        - 城市与POI：跨城市变动为长途出行或旅游出行；固定地点（如餐厅、医院）对应目的场景。
        - 位置停留时间超过2小时视为稳定场景
        - 位置快速变化(<30分钟)视为移动场景
        - 应用组合：行程规划：地图（高德/百度）、网约车（滴滴）、订票（携程）、查天气、找攻略（小红书）；演唱会：相机、订票（大麦、猫眼）
        - 交通工具判断： 
            - 高铁/飞机：当数据中有城市变化+地点（高铁站/机场）和前后数据出现相关应用（如铁路12306/航旅纵横、携程等）
            - 网约车：同时出现应用记录（滴滴出行等网约车相关应用）以及距离变化
            - 地铁：地铁站以及距离变化同时存在（必要条件）、应用记录（地铁相关、支付宝、微信）
        - 高铁/飞机子场景判断：
            - 抵达始发高铁站/机场：与之前的城市相同，且之后的城市发生变化，存在移动距离
            - 在高铁站候车：从抵达始发高铁站之后，一直到出现移动
            - 高铁行程途中：从候车之后一直到抵达终点高铁站
            - 抵达终点高铁站/机场：与之前的城市不同且出现高铁站，且，之后的城市稳定，存在移动距离
    3. 时间前后关联性
        - 前序场景：检查前一时间点的地点、应用和运动状态，确保逻辑连贯（如“出行准备”后应接“途中”或“目的场景”）。
        - 后续场景：有些场景可能因为后续数据引入而改变，应根据后续场景反推前面的场景，同时后续场景也需要和前面的场景符合逻辑（如出现乘坐高铁长距离位移且后续没有城市变化时，应标注为抵达终点高铁站）。
    4. 模糊场景处理
        - 当出现矛盾数据时：
            优先选择时间邻近的相似场景
            其次选择高频出现的默认场景

    **场景置信度评分标准**
    置信度由两个方面组成：数据要求和证据链要求
    - 高置信度（90-100分）：完整匹配3个以上的数据维度特征，且存在明确的场景定义和验证标准，数据完全覆盖场景要素，多维度证据链完整且逻辑自洽
    - 中等置信度（70-89分）：匹配2个数据维度特征，相对存在有效数据支撑核心要素，关键场景特征有数据验证， 辅助性证据存在部分缺失
    - 低置信度（0-69分）：数据维度特征不全或冲突，无合理解释，断逻辑存在明显不确定性
   
    ### 输出格式要求
    - 每条数据都要标注，格式为：时间#出行/非出行#具体场景描述#置信分数
    - 具体场景描述：需体现行为阶段（如“规划”“旅行”“返程”）
    - 逻辑连贯性：同一时间段内场景需衔接合理（如“出行规划→始发地→交通工具→目的地→途中规划→目的地→交通工具→始发地”）。
    - 按照JSON格式输出：
        "responses"的内容是每条数据的场景类别, 
        "startCity"是第一个时间所处的城市，
        "currentCIty"是当前数据最后一个时间所处的城市，
        

    ### 常见错误
    - 避免场景中出现城市地区名！！！
    - 避免高铁和地铁场景混乱，如前面是“抵达始发地铁站”，后面变成“抵达终点高铁站”
    - 避免一段场景的前后关系混乱或者中断，不能有始无终，例如高铁相关场景（抵达始发高铁站→在高铁站候车→高铁行程途中→抵达终点高铁站→离开终点高铁站），必须要有“抵达始发高铁站”和“抵达终点高铁站”！！！
    - 避免将旅游相关判断为非出行。"旅游住宿休息"是旅游过程中，虽然在室内但属于出行。
    - 只有网约车相关应用出现，并且有距离变化才能是网约车相关场景！！！
    - 避免将网约车司机判断成乘坐网约车的场景   
    - 出现城市变化且后续无城市变化，应该是抵达终点       

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
    ### 致命错误案例
    输入：地点=高铁站，城市=成都（前后都为成都）
    错误输出："出行#高铁行程途中#90"  
    修正输出："出行#高铁站内活动#50"  
    惩罚说明：!违反规则+端点缺失! 置信度应为50

    ### 错误数据
    该时间段的数据全部都是相同地点，如高铁站
    置信度应该均为50

    通过以上流程确保场景判断的逻辑清晰、分类准确且符合用户需求，以下是用户数据：
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
