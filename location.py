import requests

class GaodeGeo:
    def __init__(self):
        self.key = '6bf5fa8c77821c98758c0cd26df3830a'

    def requestApi(self, url):
        re = requests.get(url).json()
        return re

    # 地理编码
    def getGeoCode(self, address):
        url = f'https://restapi.amap.com/v3/geocode/geo?parameters&key={self.key}&address={address}'
        json_data = self.requestApi(url)
        if json_data['status'] == '1':
            location = json_data['geocodes'][0]['location']
            return location
        else:
            return '获取失败'

    # 根据经纬坐标获取地址等信息
    def getInverseGeoCode(self, location):
        url = f'https://restapi.amap.com/v3/geocode/regeo?parameters&key={self.key}&location={location}'
        json_data = self.requestApi(url)
        if json_data['status'] == '1':
            area = json_data['regeocode']['addressComponent']['district']
            return area
        else:
            return '获取失败'

## 使用说明
gd = GaodeGeo()

# 通过坐标获取所在区县
area = gd.getInverseGeoCode('121.381709,31.112813')
print('area:',area)

geocoding = gd.getGeoCode('福建省厦门市思明区')
print('geocoding:',geocoding)
