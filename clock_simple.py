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
from datetime import datetime

logging.basicConfig(level=logging.INFO)

try:
    logging.info("epd2in13_V3 时钟显示")
    epd = epd2in13_V3.EPD()
    
    logging.info("初始化并清屏")
    epd.init()
    epd.Clear(0xFF)
    
    # 加载字体 (屏幕尺寸: 250x122)
    font_time = ImageFont.truetype(os.path.join(picdir, 'MSYH.TTC'), 70)  # 超大时钟
    font_date = ImageFont.truetype(os.path.join(picdir, 'MSYH.TTC'), 20)  # 日期
    font_weekday = ImageFont.truetype(os.path.join(picdir, 'MSYH.TTC'), 18)  # 星期
    
    # 创建图像
    image = Image.new('1', (epd.height, epd.width), 255)
    draw = ImageDraw.Draw(image)
    
    # 获取当前日期时间
    now = datetime.now()
    date_str = now.strftime('%Y年%m月%d日')
    weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
    weekday_str = weekdays[now.weekday()]
    
    # 绘制日期和星期（底部）
    draw.text((10, 95), date_str, font=font_date, fill=0)
    draw.text((170, 97), weekday_str, font=font_weekday, fill=0)
    
    # 显示初始图像
    epd.display(epd.getbuffer(image))
    time.sleep(1)
    
    # 准备局部刷新
    logging.info("开始时钟显示...")
    time_image = Image.new('1', (epd.height, epd.width), 255)
    time_draw = ImageDraw.Draw(time_image)
    
    # 绘制静态内容（日期和星期在底部）
    time_draw.text((10, 95), date_str, font=font_date, fill=0)
    time_draw.text((170, 97), weekday_str, font=font_weekday, fill=0)
    
    # 设置局部刷新基础
    epd.displayPartBaseImage(epd.getbuffer(time_image))
    
    # 循环显示时间
    while True:
        # 清除时间区域（上方大部分区域）
        time_draw.rectangle((0, 0, epd.height, 90), fill=255)
        
        # 获取当前时间
        current_time = datetime.now().strftime('%H:%M')
        
        # 绘制超大时钟（居中显示）
        # 70号字体的 HH:MM 大约宽度180px，屏幕宽250px，居中约35px
        time_draw.text((35, 10), current_time, font=font_time, fill=0)
        
        # 局部刷新
        epd.displayPartial(epd.getbuffer(time_image))
        
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
