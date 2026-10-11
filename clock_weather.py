#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.realpath(__file__))

# 尝试在当前目录查找 lib 和 pic
libdir = os.path.join(current_dir, 'lib')
picdir = os.path.join(current_dir, 'pic')

# 如果当前目录没有，尝试父目录
if not os.path.exists(libdir):
    parent_dir = os.path.dirname(current_dir)
    libdir = os.path.join(parent_dir, 'lib')
    picdir = os.path.join(parent_dir, 'pic')

# 添加 lib 到路径
if os.path.exists(libdir):
    sys.path.append(libdir)
else:
    print(f"警告: 未找到 lib 目录，尝试路径: {libdir}")

import logging
from waveshare_epd import epd2in13_V3
import time
from PIL import Image, ImageDraw, ImageFont
import traceback
import requests
from datetime import datetime

logging.basicConfig(level=logging.INFO)

# ==================== 用户配置 ====================
# 目标城市：支持中文城市名（如"广州"、"北京"、"深圳"、"天河区"），或9位城市代码（如"101280101"）
CITY = "广州"

# 天气更新间隔（秒），默认3600秒（1小时）
WEATHER_UPDATE_INTERVAL = 3600

# 可选配置：高德开放平台 WebService API Key（选填）
# 若填写则优先使用官方高德API（个人免费5000次/天），不填则自动使用完全免费的公共天气API
AMAP_KEY = ""
# =================================================

# 常用城市代码对照表（用于 itboy / 中国天气网免费接口，支持空气质量AQI）
CITY_CODE_MAP = {
    # 直辖市
    '北京': '101010100', '上海': '101020100', '天津': '101030100', '重庆': '101040100',
    # 广东
    '广州': '101280101', '深圳': '101280601', '珠海': '101280701', '汕头': '101280501',
    '佛山': '101280800', '韶关': '101280201', '湛江': '101281001', '肇庆': '101280901',
    '江门': '101281101', '茂名': '101282001', '惠州': '101280301', '梅州': '101280401',
    '汕尾': '101282101', '河源': '101281201', '阳江': '101281801', '清远': '101281301',
    '东莞': '101281601', '中山': '101281701', '潮州': '101281501', '揭阳': '101281901',
    '云浮': '101281401',
    # 浙江
    '杭州': '101210101', '宁波': '101210401', '温州': '101210701', '嘉兴': '101210301',
    '湖州': '101210201', '绍兴': '101210501', '金华': '101210901', '衢州': '101211001',
    '舟山': '101211101', '台州': '101210601', '丽水': '101210801',
    # 江苏
    '南京': '101190101', '无锡': '101190201', '徐州': '101190801', '常州': '101190301',
    '苏州': '101190401', '南通': '101190501', '连云港': '101191001', '淮安': '101190901',
    '盐城': '101190701', '扬州': '101190601', '镇江': '101190104', '泰州': '101191201',
    '宿迁': '101191301',
    # 四川
    '成都': '101270101', '绵阳': '101270401', '德阳': '101272001', '宜宾': '101271101',
    '南充': '101270501', '泸州': '101271001', '达州': '101270601',
    # 湖北
    '武汉': '101200101', '黄石': '101200601', '十堰': '101201101', '宜昌': '101200901',
    '襄阳': '101200201', '荆州': '101200801',
    # 湖南
    '长沙': '101250101', '株洲': '101250301', '湘潭': '101250201', '衡阳': '101250401',
    '岳阳': '101251001', '常德': '101250601',
    # 福建
    '福州': '101230101', '厦门': '101230201', '泉州': '101230501', '漳州': '101230601',
    # 山东
    '济南': '101120101', '青岛': '101120201', '淄博': '101120301', '烟台': '101120501',
    '潍坊': '101120601', '威海': '101121301', '临沂': '101120901',
    # 陕西
    '西安': '101110101', '宝鸡': '101110901', '咸阳': '101110201',
    # 河南
    '郑州': '101180101', '洛阳': '101180901', '开封': '101180801',
    # 河北
    '石家庄': '101090101', '唐山': '101090501', '保定': '101090201',
    # 安徽
    '合肥': '101220101', '芜湖': '101220301', '蚌埠': '101220201',
    # 江西
    '南昌': '101240101', '九江': '101240201', '赣州': '101240701',
    # 辽宁
    '沈阳': '101070101', '大连': '101070201', '鞍山': '101070301',
    # 吉林
    '长春': '101060101', '吉林': '101060201',
    # 黑龙江
    '哈尔滨': '101050101', '大庆': '101050901',
    # 云南
    '昆明': '101290101', '大理': '101290201', '丽江': '101291401',
    # 贵州
    '贵阳': '101260101', '遵义': '101260201',
    # 广西
    '南宁': '101300101', '桂林': '101300501', '柳州': '101300301',
    # 海南
    '海口': '101310101', '三亚': '101310201',
    # 山西
    '太原': '101100101', '大同': '101100201',
    # 内蒙古
    '呼和浩特': '101080101', '包头': '101080201',
    # 新疆
    '乌鲁木齐': '101130101',
    # 甘肃
    '兰州': '101160101',
    # 宁夏
    '银川': '101170101',
    # 青海
    '西宁': '101150101',
    # 西藏
    '拉萨': '101140101',
    # 港澳台
    '香港': '101320101', '澳门': '101330101', '台北': '101340101'
}

def get_weather_itboy(city):
    """数据源1：itboy / 中国天气网免费接口（含空气质量AQI）"""
    clean_city = city.replace('市', '').replace('区', '').replace('县', '')
    code = CITY_CODE_MAP.get(clean_city) or CITY_CODE_MAP.get(city) or (city if city.isdigit() else None)
    if not code:
        return None
    url = f"http://t.weather.itboy.net/api/weather/city/{code}"
    resp = requests.get(url, timeout=6)
    if resp.status_code == 200:
        d = resp.json()
        if d.get('status') == 200:
            data = d.get('data', {})
            forecast = data.get('forecast', [{}])[0]
            wendu = data.get('wendu', '')
            temp = f"{wendu}°C" if wendu else ""
            sky = forecast.get('type', '')
            hum = data.get('shidu', '')
            quality = data.get('quality', '')
            wind = f"{forecast.get('fx', '')}{forecast.get('fl', '')}".strip()
            return {
                'temperature': temp,
                'skycon': sky,
                'humidity': hum,
                'aqi_desc': quality,
                'wind': wind,
                'source': 'itboy'
            }
    return None

def get_weather_uapis(city):
    """数据源2：uapis 公共天气接口（免Key，支持全国任意城市/区县）"""
    url = f"https://uapis.cn/api/v1/misc/weather?city={city}"
    resp = requests.get(url, timeout=6)
    if resp.status_code == 200:
        d = resp.json()
        if 'temperature' in d:
            temp = f"{d.get('temperature', '')}°C"
            sky = d.get('weather', '')
            hum_val = d.get('humidity', '')
            hum = f"{hum_val}%" if hum_val != '' else ''
            wind_dir = d.get('wind_direction', '')
            wind_pwr = d.get('wind_power', '')
            wind = f"{wind_dir}{wind_pwr}".strip()
            return {
                'temperature': temp,
                'skycon': sky,
                'humidity': hum,
                'aqi_desc': '',
                'wind': wind,
                'source': 'uapis'
            }
    return None

def get_weather_amap(city, amap_key):
    """可选数据源：高德开放平台 WebService API"""
    if not amap_key:
        return None
    url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={city}&key={amap_key}"
    resp = requests.get(url, timeout=6)
    if resp.status_code == 200:
        d = resp.json()
        if d.get('status') == '1' and d.get('lives'):
            live = d['lives'][0]
            temp = f"{live.get('temperature', '')}°C"
            sky = live.get('weather', '')
            hum_val = live.get('humidity', '')
            hum = f"{hum_val}%" if hum_val else ''
            wind = f"{live.get('winddirection', '')}风{live.get('windpower', '')}级"
            return {
                'temperature': temp,
                'skycon': sky,
                'humidity': hum,
                'aqi_desc': '',
                'wind': wind,
                'source': 'amap'
            }
    return None

def get_weather(city=CITY, amap_key=AMAP_KEY):
    """
    获取天气信息：支持多源故障转移
    1. 若配置了高德 API Key，优先尝试官方高德
    2. 尝试 itboy 免费接口（带空气质量 AQI）
    3. 备用尝试 uapis 接口（支持所有区县地名）
    """
    # 1. 高德官方接口（需配置 AMAP_KEY）
    if amap_key:
        try:
            res = get_weather_amap(city, amap_key)
            if res:
                logging.info(f"成功通过高德API获取天气: {city}")
                return res
        except Exception as e:
            logging.warning(f"高德API请求失败: {e}")

    # 2. itboy 接口（免Key，含空气质量）
    try:
        res = get_weather_itboy(city)
        if res:
            logging.info(f"成功通过 itboy API 获取天气: {city} (空气质量: {res.get('aqi_desc')})")
            return res
    except Exception as e:
        logging.warning(f"itboy API 请求失败: {e}")

    # 3. uapis 接口（免Key备用）
    try:
        res = get_weather_uapis(city)
        if res:
            logging.info(f"成功通过 uapis API 获取天气: {city}")
            return res
    except Exception as e:
        logging.warning(f"uapis API 请求失败: {e}")

    logging.error(f"所有天气数据源均获取失败: {city}")
    return None

def format_weather_line(weather_data, font=None, max_width=240):
    """格式化顶部天气单行文本，自适应 250px 屏幕宽度，防止溢出"""
    if not weather_data:
        return "天气信息获取失败"
    
    skycon = weather_data.get('skycon', '')
    temperature = weather_data.get('temperature', '')
    humidity = weather_data.get('humidity', '')
    aqi_desc = weather_data.get('aqi_desc', '')
    wind = weather_data.get('wind', '')

    extra = aqi_desc if aqi_desc else wind
    if extra:
        line = f"{skycon} {temperature}  湿度{humidity}  {extra}"
    else:
        line = f"{skycon} {temperature}  湿度{humidity}"
        
    if font:
        bbox = font.getbbox(line)
        if (bbox[2] - bbox[0]) > max_width:
            if extra:
                line = f"{skycon} {temperature} 湿度{humidity} {extra}"
            bbox = font.getbbox(line)
            if (bbox[2] - bbox[0]) > max_width:
                line = f"{skycon} {temperature} 湿度{humidity}"
            bbox = font.getbbox(line)
            if (bbox[2] - bbox[0]) > max_width:
                line = f"{skycon[:3]} {temperature} 湿度{humidity}"
    return line

def main():
    try:
        logging.info("epd2in13_V3 时钟天气显示")
        epd = epd2in13_V3.EPD()
        
        logging.info("初始化并清屏")
        epd.init()
        epd.Clear(0xFF)
        
        # 加载字体 (屏幕尺寸: 250x122)
        font_time = ImageFont.truetype(os.path.join(picdir, 'MSYH.TTC'), 70)  # 超大时钟
        font_date = ImageFont.truetype(os.path.join(picdir, 'MSYH.TTC'), 20)  # 日期
        font_weekday = ImageFont.truetype(os.path.join(picdir, 'MSYH.TTC'), 18)  # 星期
        font_weather = ImageFont.truetype(os.path.join(picdir, 'MSYH.TTC'), 18)  # 顶部天气信息
        
        # 创建图像
        image = Image.new('1', (epd.height, epd.width), 255)
        draw = ImageDraw.Draw(image)
        
        # 获取天气信息
        logging.info(f"获取城市 [{CITY}] 天气信息...")
        weather_data = get_weather(CITY, AMAP_KEY)
        last_valid_weather = weather_data  # 缓存最近一次有效天气，用于网络波动时容灾
        
        # 绘制静态内容（日期、天气）
        now = datetime.now()
        date_str = now.strftime('%Y年%m月%d日')
        weekday_str = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'][now.weekday()]
        
        # 绘制顶部天气信息（一行显示）
        weather_line = format_weather_line(weather_data, font=font_weather)
        draw.text((5, 2), weather_line, font=font_weather, fill=0)
        
        # 绘制底部日期和星期
        draw.text((10, 100), date_str, font=font_date, fill=0)
        draw.text((165, 100), weekday_str, font=font_weekday, fill=0)
        
        # 显示基础图像
        epd.display(epd.getbuffer(image))
        time.sleep(2)
        
        # 准备局部刷新显示时间
        logging.info("开始显示时钟...")
        time_image = Image.new('1', (epd.height, epd.width), 255)
        time_draw = ImageDraw.Draw(time_image)
        
        # 复制静态内容到时间图像
        # 顶部天气信息
        weather_line = format_weather_line(weather_data, font=font_weather)
        time_draw.text((5, 2), weather_line, font=font_weather, fill=0)
        
        # 底部日期和星期
        time_draw.text((10, 100), date_str, font=font_date, fill=0)
        time_draw.text((165, 100), weekday_str, font=font_weekday, fill=0)
        
        # 设置局部刷新基础图像
        epd.displayPartBaseImage(epd.getbuffer(time_image))
        
        # 循环更新时间
        weather_update_count = 0
        last_date = date_str  # 记录上次的日期
        last_minute = ""  # 记录上次的分钟
        
        while True:
            now = datetime.now()
            current_date = now.strftime('%Y年%m月%d日')
            current_weekday = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'][now.weekday()]
            current_time = now.strftime('%H:%M')
            
            # 检查分钟是否变化（每分钟更新时间）
            if current_time != last_minute:
                # 检查日期是否变化
                if current_date != last_date:
                    logging.info("日期变化，更新日期和星期...")
                    # 清除底部日期区域
                    time_draw.rectangle((0, 95, epd.height, epd.width), fill=255)
                    # 重新绘制日期和星期
                    time_draw.text((10, 100), current_date, font=font_date, fill=0)
                    time_draw.text((165, 100), current_weekday, font=font_weekday, fill=0)
                    last_date = current_date
                
                # 清除时间区域（中间大部分区域）
                time_draw.rectangle((0, 25, epd.height, 95), fill=255)
                
                # 绘制超大时钟（上下居中显示）
                time_draw.text((35, 15), current_time, font=font_time, fill=0)
                
                # 局部刷新
                epd.displayPartial(epd.getbuffer(time_image))
                
                last_minute = current_time
                weather_update_count += 60  # 每分钟增加60秒
            
            # 定时更新天气（使用局部刷新）
            if weather_update_count >= WEATHER_UPDATE_INTERVAL:
                logging.info("更新天气信息...")
                new_weather = get_weather(CITY, AMAP_KEY)
                if new_weather:
                    weather_data = new_weather
                    last_valid_weather = new_weather
                elif last_valid_weather:
                    logging.warning("本次天气刷新失败，保留上次有效天气数据")
                    weather_data = last_valid_weather
                else:
                    weather_data = None
                
                # 清除天气区域
                time_draw.rectangle((0, 0, epd.height, 24), fill=255)
                
                # 重新绘制天气信息
                weather_line = format_weather_line(weather_data, font=font_weather)
                time_draw.text((5, 2), weather_line, font=font_weather, fill=0)
                
                # 使用局部刷新更新天气区域
                epd.displayPartial(epd.getbuffer(time_image))
                
                weather_update_count = 0
            
            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("程序被用户中断")
        epd.init()
        epd.Clear(0xFF)
        logging.info("进入睡眠模式...")
        epd.sleep()
        epd2in13_V3.epdconfig.module_exit(cleanup=True)
        
    except Exception as e:
        logging.error(f"发生错误: {e}")
        traceback.print_exc()
        epd2in13_V3.epdconfig.module_exit(cleanup=True)

if __name__ == '__main__':
    main()
