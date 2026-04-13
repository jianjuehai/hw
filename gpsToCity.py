import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from tqdm.auto import tqdm
from cnmaps import get_adm_maps
# pip install cnmaps shapely rtree geopandas

# ---------- 1. 读区县级多边形 & 建空间索引 ----------
print('Loading county-level polygons…')
china = (
    get_adm_maps(level='区县', wgs84=True, engine='geopandas')
    [['省/直辖市', '市', '区/县', 'geometry']]
)
china.sindex  # 触发 STRtree / R-tree

# ---------- 2. 分块读取并处理原始数据 ----------
input_path_original = '单框架5d去重_0409.csv'  # 请替换为你的输入文件路径
output_path = '单框架5d去重_0409带gps.csv'
chunk_size = 200000  # 可调

# 创建输出文件并写入表头
header = ['timeStamp', 'udid', 'personaWorkDay', 'poiTypeCode', 'residence', 'bluetoothEnableState', 'bluetoothConnectState', 'wifiConnectState', 'ScreenOnStatus', 'ScreenLockStatus', 'powerConnectedState', 'sceneIds', 'longitude', 'latitude', '省/直辖市', 'city', 'district', 'top4Intents', 'unionPreActions0_5', 'unionPreActions5_20', 'actions']
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(','.join(header) + '\n')

# 读取并处理数据
for chunk in tqdm(pd.read_csv(input_path_original, chunksize=chunk_size), desc='Processing chunks'):
    # 删除包含无效经纬度值的行
    valid_points_df = chunk.dropna(subset=['longitude', 'latitude'])
    
    N = len(valid_points_df)
    lons = valid_points_df['longitude'].values
    lats = valid_points_df['latitude'].values
    
    # 分块空间连接
    for start in range(0, N, chunk_size):
        end = start + chunk_size
        chunk = valid_points_df.iloc[start:end]
        gdf_pts = gpd.GeoDataFrame(
            chunk,
            geometry=gpd.points_from_xy(chunk.longitude, chunk.latitude),
            crs='EPSG:4326'
        )
        joined = gpd.sjoin(gdf_pts, china, how='left', predicate='within')
        
        # 选择需要的列
        out_df = joined[['timeStamp', 'udid', 'personaWorkDay', 'poiTypeCode', 'residence', 'bluetoothEnableState', 'bluetoothConnectState', 'wifiConnectState', 'ScreenOnStatus', 'ScreenLockStatus', 'powerConnectedState', 'sceneIds', 'longitude', 'latitude', '省/直辖市', '市', '区/县', 'top4Intents', 'unionPreActions0_5', 'unionPreActions5_20', 'actions']]
        
        # 确保省市区列没有乱码
        out_df['省/直辖市'] = out_df['省/直辖市'].fillna('').astype(str)
        out_df['市'] = out_df['市'].fillna('').astype(str)
        out_df['区/县'] = out_df['区/县'].fillna('').astype(str)
        
        # 将结果追加到输出文件
        out_df.to_csv(output_path, index=False, header=False, mode='a', encoding='utf-8')

print(f'Done! Saved → {output_path}')

