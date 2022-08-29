import requests 
import _thread as thread 
import time
from contextlib import closing
from urllib.parse import urlparse
import socket
from urllib3.util import connection
import re

default_url = "https://cloud.ljxnet.cn/temp"

def check_string(re_exp, str):
    res = re.search(re_exp, str)
    if res:
        return True
    else:
        return False
def check(sleep_time,c):
  time.sleep(sleep_time)
  global max
  max = 0

print("\n 连接测速脚本\n")
url = input(" 请输入测速URL，默认:" + default_url + "\n → ")or default_url
if check_string("^((https|http|ftp|rtsp|mms)?:\/\/)[^\s]+", url) is False:
  print(" 输入无效，已使用默认值")
  url = default_url

print("\n DNS解析中...")
domain =  urlparse(url).hostname
answer =socket.gethostbyname(domain)
print(" " + domain , "-", answer,"\n")
connect = input(" 请输入连接地址，默认为DNS解析地址\n → ")or answer
if check_string("(25[0-5]|2[0-4]\d|[0-1]\d{2}|[1-9]?\d)\.(25[0-5]|2[0-4]\d|[0-1]\d{2}|[1-9]?\d)\.(25[0-5]|2[0-4]\d|[0-1]\d{2}|[1-9]?\d)\.(25[0-5]|2[0-4]\d|[0-1]\d{2}|[1-9]?\d)", connect) is False and check_string("/^(([\da-fA-F]{1,4}):){8}$/",connect) is False:
  print(" 输入无效，已使用默认值")
  connect = answer

thread_count = input("\n 请输入线程数，默认单线程\n → ")or 1
if check_string("[1-9]\d*", str(thread_count)) is False:
  print(" 输入无效，已使用默认值")
  thread_count = 1
else:
  thread_count = int(thread_count)

max_des = input("\n 请输入目标流量(不加MB)或时间(要加s)，默认10s \n → ")or "10s"
if check_string("^[1-9]\d*$", max_des):
    max = int(max_des)
    if max >= 1024:
      max_des = format(max/1024, '.2f') + "GB"
    else:
      max_des = max_des + "MB"
elif check_string("^[1-9]\d*[sS]$", max_des):
   thread.start_new_thread(check, (int(re.match("[1-9]\d*",max_des).group()),"check"))
   max = 999999999999999
else:
  print(" 输入无效，已使用默认值")
  thread.start_new_thread(check, (10,"check"))
  max_des = "10s"
  max = 999999999999999


refresh =  1

print("\n URL:%s\n 连接地址:%s\n 线程数:%s\n 目标:%s\n" % (url,connect,thread_count,max_des))

_orig_create_connection = connection.create_connection
def patched_create_connection(address, *args, **kwargs):
    """Wrap urllib3's create_connection to resolve the name elsewhere"""
    host, port = address
    hostname = connect
    return _orig_create_connection((hostname, port), *args, **kwargs)
connection.create_connection = patched_create_connection

data_count = 0
try_count = 0
def speed(thread,chunk_size):
    global data_count
    global try_count
    while True:
      
      try:
        with closing(requests.get(url, stream=True)) as response:
            for data in response.iter_content(chunk_size=chunk_size):
                data_count = data_count + len(data)
                if data_count/102400/8 >= max:
                  return 0
            if data_count/102400/8 >= max:
                  return 0
      except requests.exceptions.RequestException as e:
         try_count = try_count + 1
def start_new_thread(thread_th):
    try:
     thread.start_new_thread(speed, (thread_th,1024))
    except:
      print("Error: unable to start thread")
for thread_th in range(1,thread_count + 1):
    start_new_thread(thread_th)
start_time = time.time()
all_down = 0
max_speed = 0 
while all_down < max:
    data_count_old = data_count
    time.sleep(refresh)
    down_speed = (data_count - data_count_old)/102400/refresh
    down_speed_byte = down_speed/8
    if down_speed_byte > max_speed:
      max_speed = down_speed_byte
    all_down = data_count/102400/8
    now_time = time.time()
    avg_speed_byte= data_count/102400/(now_time - start_time)/8
    avg_speed = data_count/102400/(now_time - start_time)
    if all_down >= 1024:
      all_down_des = format(all_down/1024, '.2f') + "GB"
    else:
      all_down_des = format(all_down, '.1f') + "MB"
    if down_speed == 0:
      print("\r %.0fs 总计%s 最大速度：%.1fM/s %.1fMbps 平均速度：%.1fM/s %.1fMbps 连接速度：0 已尝试：%s次     " % (now_time - start_time,all_down_des, max_speed, max_speed *8,avg_speed_byte,avg_speed,try_count), end=" ")
    else:
      print("\r %.0fs 总计%s 最大速度：%.1fM/s %.1fMbps 平均速度：%.1fM/s %.1fMbps 连接速度：%.1fM/s %.1fMbps     " % (now_time - start_time,all_down_des, max_speed, max_speed *8,avg_speed_byte,avg_speed,down_speed_byte,down_speed), end=" ")

input("\n 执行完毕 Enter键关闭此窗口")
