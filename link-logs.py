# %%
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
import random

# %%
logs = sorted(Path('./log').glob('*.log'))

# %%
log_lines = []
for file in logs:
    for line in open(file, encoding='utf-8').read().split('\n'):
        print(line)
        if line.startswith('2026') and '数据库' not in line and '数据初始化完成' not in line:
            log_lines.append(line)

random.shuffle(log_lines)


# %%
# 定义时间范围
start_time = datetime(2026, 7, 21, 11, 0, 0)
end_time = datetime(2026, 7, 22, 13, 0, 0)
time_range_seconds = int((end_time - start_time).total_seconds())

# 正则匹配时间戳
timestamp_pattern = re.compile(
    r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})')

# 存储要替换的时间戳列表
timestamps_to_replace = []

# 先收集所有需要替换的时间戳
for line in log_lines:
    match = timestamp_pattern.match(line)
    if match:
        timestamps_to_replace.append(match.group(1))

# 生成随机时间戳（保持原始顺序，但每个时间戳随机生成）
new_log_lines = []
for line in log_lines:
    match = timestamp_pattern.match(line)
    if match:
        old_ts = match.group(1)
        # 生成随机偏移秒数（精确到毫秒）
        random_seconds = random.randint(0, time_range_seconds - 1)
        random_microseconds = random.randint(0, 999999)
        new_dt = start_time + \
            timedelta(seconds=random_seconds, microseconds=random_microseconds)
        new_ts = new_dt.strftime('%Y-%m-%d %H:%M:%S.') + \
            f'{new_dt.microsecond // 1000:03d}'
        # 替换时间戳
        new_line = line.replace(old_ts, new_ts, 1)
        new_log_lines.append(new_line)
    else:
        new_log_lines.append(line)

# Sort new_log_lines by times
new_log_lines.sort(key=lambda e: e.split('|')[0])

# 写入文件
filename = 'a.log'
with open(filename, 'w', encoding='utf-8') as f:
    for line in new_log_lines:
        f.write(line + '\n')

print(f"已生成 a.log 文件，共 {len(new_log_lines)} 行")
print(f"时间范围: {start_time} 到 {end_time}")

# %%
# 设置创建时间为 2026-07-21 11:00:00
create_time = datetime(2026, 7, 21, 11, 0, 0)
# 设置修改时间为 2026-07-22 14:00:00
modify_time = datetime(2026, 7, 22, 14, 0, 0)

# 转换为时间戳
create_timestamp = create_time.timestamp()
modify_timestamp = modify_time.timestamp()

# 使用os.utime设置访问时间和修改时间
# 注意：在Windows上，os.utime可以设置atime和mtime
# 在Unix上，ctime会随着mtime改变而改变（如果文件内容改变）
# 但由于我们刚创建文件，我们尽可能设置
try:
    # 设置访问时间和修改时间
    os.utime(filename, (create_timestamp, modify_timestamp))
    print(f"已设置文件访问时间: {create_time}")
    print(f"已设置文件修改时间: {modify_time}")

    # 获取文件状态信息
    stat_info = os.stat(filename)
    print(f"\n文件时间戳信息:")
    print(f"  访问时间 (atime): {datetime.fromtimestamp(stat_info.st_atime)}")
    print(f"  修改时间 (mtime): {datetime.fromtimestamp(stat_info.st_mtime)}")
    print(f"  状态更改时间 (ctime): {datetime.fromtimestamp(stat_info.st_ctime)}")

except Exception as e:
    print(f"设置文件时间戳时出错: {e}")
    print("注意: 在某些系统上，可能无法直接设置文件的创建时间(ctime)")
