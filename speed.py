import requests 
import _thread as thread 
import time
from contextlib import closing
from urllib.parse import urlparse
import socket
from urllib3.util import connection
import re

default_url = "https://speed.cloudflare.com/__down?bytes=104857600"

def check_string(re_exp, str):
    res = re.search(re_exp, str)
    if res:
        return True
    else:
        return False
def check(sleep_time,c):
  time.sleep(sleep_time)
  global max_byte
  max_byte = 0


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
if check_string("(25[0-5]|2[0-4]\d|[0-1]\d{2}|[1-9]?\d)\.(25[0-5]|2[0-4]\d|[0-1]\d{2}|[1-9]?\d)\.(25[0-5]|2[0-4]\d|[0-1]\d{2}|[1-9]?\d)\.(25[0-5]|2[0-4]\d|[0-1]\d{2}|[1-9]?\d)", connect) is False and check_string("^([\da-fA-F]{1,4}:){7}[\da-fA-F]{1,4}|:((:[\da−fA−F]1,4)1,6|:)|:((:[\da−fA−F]1,4)1,6|:)|^[\da-fA-F]{1,4}:((:[\da-fA-F]{1,4}){1,5}|:)|([\da−fA−F]1,4:)2((:[\da−fA−F]1,4)1,4|:)|([\da−fA−F]1,4:)2((:[\da−fA−F]1,4)1,4|:)|^([\da-fA-F]{1,4}:){3}((:[\da-fA-F]{1,4}){1,3}|:)|([\da−fA−F]1,4:)4((:[\da−fA−F]1,4)1,2|:)|([\da−fA−F]1,4:)4((:[\da−fA−F]1,4)1,2|:)|^([\da-fA-F]{1,4}:){5}:([\da-fA-F]{1,4})?|([\da−fA−F]1,4:)6:|([\da−fA−F]1,4:)6:",connect) is False:
  print(" 输入无效，已使用默认值")
  connect = answer

thread_count = input("\n 请输入线程数，默认单线程\n → ")or 1
if check_string("^[1-9]\d*$", str(thread_count)) is False:
  print(" 输入无效，已使用默认值")
  thread_count = 1
else:
  thread_count = int(thread_count)

max_des = input("\n 请输入目标流量(不加MB)或时间(要加s)，默认20s \n → ")or "20s"
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

max_byte = max * 1048576
refresh =  1

print("\n URL:%s\n 连接地址:%s\n 线程数:%s\n 目标:%s\n" % (url,connect,thread_count,max_des))

_orig_create_connection = connection.create_connection
def patched_create_connection(address, *args, **kwargs):
    """Wrap urllib3's create_connection to resolve the name elsewhere"""
    host, port = address
    hostname = connect
    return _orig_create_connection((hostname, port), *args, **kwargs)
connection.create_connection = patched_create_connection

data_count = []
try_count = 0
def speed(thread_th,chunk_size):
    global data_count
    global try_count
    while True:
      try:
        with closing(requests.get(url, stream=True)) as response:
            for data in response.iter_content(chunk_size=chunk_size):
                data_count[thread_th] = data_count[thread_th] + chunk_size
                if sum(data_count) >= max_byte:
                  return 0
            data_count[thread_th] = data_count[thread_th] + len(data) - chunk_size #矫正数值，兼顾性能与精度
            if data_count[thread_th] >= max_byte:
                  return 0
      except requests.exceptions.RequestException as e:
         try_count = try_count + 1
def start_new_thread(thread_th):
    try:
     thread.start_new_thread(speed, (thread_th,1024))
    except:
      print("Error: unable to start thread")
for thread_th in range(0,thread_count ):
    data_count.insert(thread_th, 0)
    start_new_thread(thread_th)
start_time = time.time()
all_down = 0
max_speed = 0 
data_count_sum = 0 
while data_count_sum < max_byte:
    data_count_old = data_count_sum
    time.sleep(refresh)
    data_count_sum = sum(data_count)
    down_speed = (data_count_sum - data_count_old)/1048576/refresh
    if down_speed > max_speed:
      max_speed = down_speed
    all_down = data_count_sum/1048576
    now_time = time.time()
    avg_speed = all_down/(now_time - start_time)
    if all_down >= 1024:
      all_down_des = format(all_down/1024, '.2f') + "GB"
    else:
      all_down_des = format(all_down, '.1f') + "MB"
    if down_speed == 0:
      print("\r %.0fs 总计%s 最大速度：%.1fM/s %.1fMbps 平均速度：%.1fM/s %.1fMbps 连接速度：0 已尝试：%s次     " % (now_time - start_time,all_down_des, max_speed, max_speed *8,avg_speed,avg_speed * 8,try_count), end=" ")
    else:
      print("\r %.0fs 总计%s 最大速度：%.1fM/s %.1fMbps 平均速度：%.1fM/s %.1fMbps 连接速度：%.1fM/s %.1fMbps     " % (now_time - start_time,all_down_des, max_speed, max_speed *8,avg_speed,avg_speed * 8,down_speed,down_speed* 8), end=" ")

input("\n 执行完毕 Enter键关闭此窗口")
