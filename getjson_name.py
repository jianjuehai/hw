import pandas as pd
import json

# # 读取字段定义表
# df_meta = pd.read_excel("content字段含义.xlsx", sheet_name="Sheet1", header=0)

# #构建字段名称表
# ziduan_name = {
#     int(k): v for k, v in zip(df_meta["顺序"], df_meta["字段名（columns）"]) 
#     if pd.notna(k) and pd.notna(v)
# }
ziduan_name = {1: 'timeStamp', 2: 'serviceUsage', 3: 'serviceExposure', 4: 'serviceSource', 5: 'motionState', 6: 'sceneIds', 7: 'connectedDeviceList', 8: 'wifiEnableState', 9: 'wifiConnectedState', 10: 'bluetoothEnableState', 11: 'bluetoothConnectedState', 12: 'powerConnectedState', 13: 'semanticPlace', 14: 'longitude', 15: 'latitude', 16: 'geodeticSystem', 17: 'altitude', 18: 'country', 19: 'province', 20: 'city', 21: 'district', 22: 'cellId', 23: 'cellMCC', 24: 'cellMNC', 25: 'cellLAC', 26: 'cellRSSI', 27: 'wifiBSSID', 28: 'wifiLevel', 29: 'unionPreServiceUsages', 30: 'unionPostServiceUsages', 31: 'unionFutureServiceUsages', 32: 'sessionId', 33: 'traceId', 34: 'recallReason', 35: 'recId', 36: 'recallServiceMap', 37: 'refreshResult', 38: 'dislikeService', 39: 'poiInfo', 40: 'voiceIntents or adsVisitInfo', 41: 'sharedIntentData', 42: 'hwPoiInfo', 43: 'dsIntents', 44: 'personalWorkDay', 45: 'residence'}

#构建serviceusage名称表
content="""packageName:包名
moduleName:模块名，FA必选
activityName:activity名
isAd:是否广告，0非广告
pageName:page名
sectionName:section名
positionIndex:位置索引
abTeststrategy:ab测试策略
pages:页面，Json数组字串(取sha256 hash的前16位)
isHarmonyApp:是否鸿蒙App
isMainApp:是否主App
duration:使用时长
serviceSource:服务来源，0:AMS，5:FMS
formName:卡片名，FA必选
formType:卡片规格
timestamp:时间戳
intentName:意图名
intentRelatedService:意图相关服务名
isFlowControl:是否流控，默认为0，不参与流控
serviceType:服务类型（当前仅serviceType=9模板卡片有意图名）
abilityId:云侧服务abilityId
templateFAAbilityType:模板卡片FA云侧召回ability类型，仅serviceType=9时有效
virtualSelfOwnedAbilityInfo:虚拟自有服务假四件套信息
serviceId:APP类型为包名，上云可省略
"""
# 提取冒号前部分
serviceusage_name = [line.split(":", 1)[0].strip() for line in content.strip().split("\n") if ":" in line]


def convert_pipe_to_json(input_str):
    # 按'|'分割字符串
    parts = input_str.split('|')
    # 创建键值对字典，键从1开始递增
    result = {ziduan_name[i]: part for i, part in enumerate(parts, start=1)}
    result["unionPreServiceUsages"] = Serviceusage(result["unionPreServiceUsages"])
    result["unionPostServiceUsages"] = Serviceusage(result["unionPostServiceUsages"])
    result["unionFutureServiceUsages"] = Serviceusage(result["unionFutureServiceUsages"])
    # 转换为JSON并返回格式化结果
    return json.dumps(result, ensure_ascii=False, indent=2)

def Serviceusage(input_str):
    # 按','分割字符串
    parts = input_str.split(',')
    # 取两者中较小的长度，避免索引越界
    min_length = min(len(parts), len(serviceusage_name))
    # 创建键值对字典，键从1开始递增
    result = {serviceusage_name[i]: parts[i] for i in range(min_length)}
    # 转换为JSON并返回格式化结果
    return result

input_string1 = """
1737959472228|com.tencent.mm,,,0,,,,,["e2779edcad74791b"],0,1,4967,0,,1*1,1737959472228,,,0,2,,-1,,com.tencent.mm,|["com.tdx.AndroidMSZQ,,,0,,,,,,1*1,2,,,,,,[],0,,,0,,-1,,","com.tencent.mm,,,0,,,,,,1*1,2,,,,,,[],0,,,0,,-1,,","com.kmxs.reader,,,1,,,,,,1*1,2,,,,,,[],0,,,0,,-1,,","com.tencent.weworklocal,,,0,,,,,,1*1,2,,,,,,[],0,,,0,,-1,,"]|1||||1|1|1|1|0||||GCJ02||CN||||||||||-44|[]|["com.tencent.mm,,,,,,,,[\"4980c11f1485cc54\"#\"e2779edcad74791b\"#\"2adec9d3275f324e\"],0,1,354263,0,,,1737958890629,,,0,0,,-1,,null,"]|["com.tdx.AndroidMSZQ,,,0,,,,,[\"18fabb1ccc22dd32\"],0,1,40706,0,,1*1,1737959488433,,,0,2,,-1,,com.tdx.AndroidMSZQ,","com.tencent.mm,,,0,,,,,[\"e2779edcad74791b\"#\"4980c11f1485cc54\"],0,1,72445,0,,1*1,1737959530897,,,0,2,,-1,,com.tencent.mm,","com.tencent.mm,,,0,,,,,[\"4980c11f1485cc54\"#\"bfcad5f6a285c715\"],0,1,76908,0,,1*1,1737959697860,,,0,2,,-1,,com.tencent.mm,","com.tencent.mm,,,,,,,,[\"4980c11f1485cc54\"],0,1,32883,0,,,1737959898653,,,0,0,,-1,,null,","com.tencent.mm,,,,,,,,[\"4980c11f1485cc54\"#\"e2779edcad74791b\"],0,1,99825,0,,,1737959946968,,,0,0,,-1,,null,","com.tencent.mm,,,,,,,,[\"e2779edcad74791b\"#\"4980c11f1485cc54\"#\"956e03df4566fc36\"],0,1,26385,0,,,1737960045851,,,0,0,,-1,,null,"]|45b3cb4236e643cdb8366b1a343d24a7|||082cb6d3-4e36-4fac-b9d5-d97cb89b9bfe|{"routine":["com.tencent.mm,,,1*1,,,0.2439,,2","com.kmxs.reader,,,1*1,,,0.6,,2","com.tencent.mm,,,1*1,,,0.43,,2","com.tdx.AndroidMSZQ,,,1*1,,,0.1,,2","com.eg.android.AlipayGphone,,,1*1,,,0.1,,2","com.tencent.weworklocal,,,1*1,,,0.1,,2"],"recentlyUsed":["com.tencent.mm,,,1*1,,,0,,2","com.kmxs.reader,,,1*1,,,1,,2","com.ss.android.ugc.aweme.lite,,,1*1,,,2,,2","com.tencent.weworklocal,,,1*1,,,3,,2","com.android.mms,,,1*1,,,4,,2","com.tdx.AndroidMSZQ,,,1*1,,,5,,2","com.huawei.camera,,,1*1,,,6,,2","com.huawei.health,,,1*1,,,7,,2"]}|{"2*2":["com.tdx.AndroidMSZQ,,,0,,,,,,1*1,2,,,,,,[],0,,,0,,-1,,","com.tencent.weworklocal,,,0,,,,,,1*1,2,,,,,,[],0,,,0,,-1,,","com.kmxs.reader,,,1,,,,,,1*1,2,,,,,,[],0,,,0,,-1,,","com.tencent.mm,,,0,,,,,,1*1,2,,,,,,[],0,,,0,,-1,,"]}|[]|||[]||1001101330010000,1.000000,1004100530010000,0.677257,1003100300000000,0.173156,1004100730030000,0.124852|1|1
"""

input_string2 = """
1737961970138|com.huawei.fastapp,,,,,,,,["bd86d23d01218705"],0,1,1748,0,,,1737961970138,,,0,0,,-1,,null,|[]|0||||1|0|0|0|0|||||||||||||||||["com.android.packageinstaller,,,,,,,,[\"923f11cb29211040\"],0,1,2210,0,,,1737961673561,,,0,0,,-1,,null,","com.huawei.appmarket,,,,,,,,[\"25f2f7d4b9701898\"],0,1,2782,0,,,1737961675771,,,0,0,,-1,,null,","com.huawei.coauthservice,,,,,,,,[\"427b38c9dea09609\"],0,1,2808,0,,,1737961678553,,,0,0,,-1,,null,","com.huawei.appmarket,,,,,,,,[\"25f2f7d4b9701898\"],0,1,24842,0,,,1737961681361,,,0,0,,-1,,null,","com.huawei.browser,,,,,,,,[\"b0f9fed21cb1cca4\"],0,1,1375,0,,,1737961706203,,,0,0,,-1,,null,","com.yqfkc.qckj,,,,,,,,[\"8a17dcbc9755cf5c\"#\"1e4623b2a3064325\"],0,1,15788,0,,,1737961938877,,,0,0,,-1,,null,","com.tencent.mm,,,,,,,,[\"6c9204b5ed7e728f\"],0,1,2395,0,,,1737961954665,,,0,0,,-1,,null,","com.yqfkc.qckj,,,,,,,,[\"1e4623b2a3064325\"],0,1,13078,0,,,1737961957060,,,0,0,,-1,,null,"]|["com.sm188w.sm188m,,,,,,,,[\"a27ffac763b7e5ef\"],0,1,251692,0,,,1737960783034,,,0,0,,-1,,null,","com.huawei.browser,,,,,,,,[\"73038923a0f3aa37\"#\"b0f9fed21cb1cca4\"#\"7ec3a8917835f329\"],0,1,7355,0,,,1737961037553,,,0,0,,-1,,null,","com.huawei.photos,,,,,,,,[\"8de3fc87cc9a246c\"],0,1,3589,0,,,1737961044908,,,0,0,,-1,,null,","com.huawei.browser,,,,,,,,[\"b0f9fed21cb1cca4\"],0,1,167230,0,,,1737961048497,,,0,0,,-1,,null,","com.tencent.mm,,,,,,,,[\"4980c11f1485cc54\"#\"1256d3a5fab7ed5f\"#\"1b493ca6172f746f\"#\"7a97c898c8f53caa\"],0,1,29242,0,,,1737961217143,,,0,0,,-1,,null,","com.tencent.mm,,,,,,,,[\"4980c11f1485cc54\"#\"1256d3a5fab7ed5f\"#\"1b493ca6172f746f\"#\"7a97c898c8f53caa\"],0,1,13477,0,,,1737961267642,,,0,0,,-1,,null,","com.huawei.browser,,,,,,,,[\"b0f9fed21cb1cca4\"],0,1,74540,0,,,1737961284189,,,0,0,,-1,,null,","android,,,,,,,,[\"2b0ae0e00dd15bab\"],0,1,2633,0,,,1737961358729,,,0,0,,-1,,null,","com.android.documentsui,,,,,,,,[\"bd1833089e7d6444\"],0,1,2251,0,,,1737961361362,,,0,0,,-1,,null,","com.huawei.browser,,,,,,,,[\"b0f9fed21cb1cca4\"],0,1,62057,0,,,1737961363613,,,0,0,,-1,,null,","com.sm188w.sm188m,,,,,,,,[\"a27ffac763b7e5ef\"],0,1,200550,0,,,1737961427458,,,0,0,,-1,,null,","com.huawei.photos,,,,,,,,[\"1c83d73799191325\"],0,1,16094,0,,,1737961632912,,,0,0,,-1,,null,","com.huawei.browser,,,,,,,,[\"b0f9fed21cb1cca4\"#\"7ec3a8917835f329\"],0,1,5453,0,,,1737961654438,,,0,0,,-1,,null,","com.huawei.photos,,,,,,,,[\"8de3fc87cc9a246c\"],0,1,2412,0,,,1737961659891,,,0,0,,-1,,null,","com.huawei.browser,,,,,,,,[\"b0f9fed21cb1cca4\"],0,1,11258,0,,,1737961662303,,,0,0,,-1,,null,"]|["com.yqfkc.qckj,,,,,,,,[\"1e4623b2a3064325\"#\"cdbad14ff19ac8af\"#\"bb6c192a0cf85620\"],0,1,61224,0,,,1737961971886,,,0,0,,-1,,null,","com.huawei.fastapp,,,,,,,,[\"bd86d23d01218705\"],0,1,4753,0,,,1737962033110,,,0,0,,-1,,null,","com.yqfkc.qckj,,,,,,,,[\"1e4623b2a3064325\"#\"cdbad14ff19ac8af\"#\"bb6c192a0cf85620\"#\"c095d4e942da4522\"#\"4ee0d969f28f8f76\"],0,1,70226,0,,,1737962037863,,,0,0,,-1,,null,","com.eg.android.AlipayGphone,,,,,,,,[\"6a94ae9a144f2e0f\"#\"fda3530a12dc63d2\"],0,1,3329,0,,,1737962108089,,,0,0,,-1,,null,","com.yqfkc.qckj,,,,,,,,[\"1e4623b2a3064325\"#\"878e629e9c1d3bcf\"],0,1,31392,0,,,1737962111418,,,0,0,,-1,,null,","com.eg.android.AlipayGphone,,,,,,,,[\"0a46e174259b660f\"],0,1,2284,0,,,1737962142810,,,0,0,,-1,,null,","com.yqfkc.qckj,,,,,,,,[\"878e629e9c1d3bcf\"#\"bb6c192a0cf85620\"#\"1e4623b2a3064325\"#\"8a17dcbc9755cf5c\"#\"53b4455a7c8ccab2\"],0,1,89339,0,,,1737962145094,,,0,0,,-1,,null,","com.huawei.systemmanager,,,,,,,,[\"a14bff0022fa28ff\"#\"09930d5ddbb0a5b3\"#\"7ec6a162f7301484\"],0,1,52469,0,,,1737962239213,,,0,0,,-1,,null,","com.xunmeng.pinduoduo,,,,,,,,[\"a96d4c52fc170a2a\"#\"b816db6970d52eff\"],0,1,244376,0,,,1737962569915,,,0,0,,-1,,null,"]||||||{}|[]
"""

input_string3 = """
1737864160262|com.huawei.contacts,,,,,,,,["dfe85a79c9f5badf"],1,1,32734,0,,,1737864160262,,,0,0,,-1,,null,|[]|0||["1615366304332","1618806525000"]||1|0|1|1|0|||||||||||||||||["com.doudoubird.calculation,,,,,,,,[\"1c04a0bda1b33977\"],0,1,15941,0,,,1737863889296,,,0,0,,-1,,null,","com.doudoubird.calculation,,,,,,,,[\"1c04a0bda1b33977\"],0,1,5727,0,,,1737864036628,,,0,0,,-1,,null,","com.huawei.contacts,,,,,,,,[\"dfe85a79c9f5badf\"],1,1,1418,0,,,1737864043584,,,0,0,,-1,,null,","com.android.incallui,,,,,,,,[\"a782743c3bff24dc\"],0,1,25269,0,,,1737864045002,,,0,0,,-1,,null,","com.huawei.contacts,,,,,,,,[\"dfe85a79c9f5badf\"],1,1,27072,0,,,1737864070271,,,0,0,,-1,,null,","com.huawei.contacts,,,,,,,,[\"dfe85a79c9f5badf\"],1,1,2455,0,,,1737864099909,,,0,0,,-1,,null,","com.android.incallui,,,,,,,,[\"a782743c3bff24dc\"],0,1,45931,0,,,1737864102364,,,0,0,,-1,,null,"]|["com.android.incallui,,,,,,,,[\"a782743c3bff24dc\"],0,1,353441,0,,,1737863420707,,,0,0,,-1,,null,","com.tencent.qqmusic,,,,,,,,[\"36b63883802a4afa\"],0,1,2377,0,,,1737863774148,,,0,0,,-1,,null,","com.tencent.qqmusic,,,,,,,,[\"36b63883802a4afa\"],0,1,3574,0,,,1737863779485,,,0,0,,-1,,null,","com.doudoubird.calculation,,,,,,,,[\"1c04a0bda1b33977\"],0,1,94936,0,,,1737863787384,,,0,0,,-1,,null,"]|[]|af2c41093ffd492ab8c022e14009a104|||f7889d7c-c424-49e7-b0ee-83820512c808|{"routine":["com.juanvision.EseeNetProj,,,1*1,,,6.3578,,2","com.tencent.mm,,,1*1,,,0.1364,,2","com.xunmeng.pinduoduo,,,1*1,,,0.24,,2","com.juanvision.EseeNetProj,,,1*1,,,0.24,,2","com.ss.android.ugc.aweme,,,1*1,,,0.14,,2","com.tencent.mm,,,1*1,,,0.14,,2","com.phoenix.read,,,1*1,,,0.1,,2","com.tencent.qqmusic,,,1*1,,,0.072000004,,2"],"recentlyUsed":["com.doudoubird.calculation,,,1*1,,,0,,2","com.tencent.qqmusic,,,1*1,,,1,,2","com.tencent.mm,,,1*1,,,2,,2","com.xs.fm,,,1*1,,,3,,2","com.ss.android.ugc.aweme,,,1*1,,,4,,2","com.huawei.camera,,,1*1,,,5,,2"]}|{"2*2":["com.ss.android.ugc.aweme.lite,,,0,,,,,,1*1,2,,,,,,[],0,,,0,,-1,,","com.tencent.mm,,,0,,,,,,1*1,2,,,,,,[],0,,,0,,-1,,","com.ss.android.ugc.aweme,,,0,,,,,,1*1,2,,,,,,[],0,,,0,,-1,,","com.xunmeng.pinduoduo,,,0,,,,,,1*1,2,,,,,,[],0,,,0,,-1,,"]}|[]
"""

# 转换并输出结果
print(convert_pipe_to_json(input_string3))
