# 📝 日志轮转配置说明

## 更新时间
2025-11-30 19:37

## 🎯 功能说明

添加了日志文件大小和数量限制，防止日志文件无限增长占用磁盘空间。

## ⚙️ 配置参数

### 日志轮转设置
- **单个文件最大**: 5MB
- **历史文件保留**: 3份
- **总磁盘占用**: 最多 20MB (5MB × 4份)

### 文件命名规则
```
monitor.log         # 当前日志（最新）
monitor.log.1       # 历史日志1（较新）
monitor.log.2       # 历史日志2
monitor.log.3       # 历史日志3（最旧）
```

## 🔄 工作原理

### 自动轮转流程

1. **正常写入**
   ```
   monitor.log (0.5MB) ← 持续写入
   ```

2. **达到5MB**
   ```
   monitor.log (5.0MB) → monitor.log.1
   monitor.log (新建)   ← 继续写入
   ```

3. **再次达到5MB**
   ```
   monitor.log.1 → monitor.log.2
   monitor.log (5MB) → monitor.log.1
   monitor.log (新建) ← 继续写入
   ```

4. **保持3份历史**
   ```
   monitor.log.3 (删除，最旧的)
   monitor.log.2 → monitor.log.3
   monitor.log.1 → monitor.log.2
   monitor.log → monitor.log.1
   monitor.log (新建)
   ```

## 📊 示例场景

### 长期运行

**运行1天** (普通日志量):
```
monitor.log         # 2MB
```

**运行3天** (密集日志):
```
monitor.log         # 3MB
monitor.log.1       # 5MB
monitor.log.2       # 5MB
总计: 13MB
```

**运行7天** (高频日志):
```
monitor.log         # 4MB
monitor.log.1       # 5MB
monitor.log.2       # 5MB
monitor.log.3       # 5MB
总计: 19MB (最大)
```

## 💡 技术实现

### Python logging.handlers

使用 `RotatingFileHandler`:
```python
from logging.handlers import RotatingFileHandler

file_handler = RotatingFileHandler(
    'monitor.log',
    maxBytes=5*1024*1024,  # 5MB
    backupCount=3,         # 保留3份
    encoding='utf-8'
)
```

### 特点
- ✅ 自动轮转（无需手动干预）
- ✅ 线程安全
- ✅ 精确的大小控制
- ✅ 自动删除最旧文件

## 🔍 查看日志

### 查看当前日志
```bash
# 实时查看
tail -f monitor.log

# 查看最后100行
tail -n 100 monitor.log

# 搜索关键字
grep "ERROR" monitor.log
```

### 查看历史日志
```bash
# 查看所有日志文件
ls -lh monitor.log*

# 查看历史日志
cat monitor.log.1
cat monitor.log.2
cat monitor.log.3

# 搜索所有日志
grep "FAT32" monitor.log*
```

### 合并查看
```bash
# 按时间顺序查看所有日志
cat monitor.log.3 monitor.log.2 monitor.log.1 monitor.log | less

# 搜索所有日志中的错误
grep "ERROR" monitor.log* | less
```

## 📈 日志量预估

### 正常运行

**每次检查产生日志**:
- 页面加载: ~3 行
- 评论解析: ~2 行
- 结果输出: ~2 行
- **总计**: ~7 行/页 ≈ 700 字节

**每小时** (60秒间隔):
- 60 页 × 700 字节 ≈ 42KB/小时

**每天**:
- 42KB × 24 = 1008KB ≈ 1MB/天

**轮转周期**:
- 5MB ÷ 1MB/天 ≈ **5天轮转一次**

### 高频运行 (30秒间隔)

**每天**:
- 2MB/天

**轮转周期**:
- 5MB ÷ 2MB/天 ≈ **2.5天轮转一次**

## ⚙️ 自定义配置

如果需要修改日志轮转参数，编辑 `monitor.py`:

### 修改单文件大小
```python
# 10MB
maxBytes=10*1024*1024

# 1MB
maxBytes=1*1024*1024
```

### 修改历史文件数量
```python
# 保留5份
backupCount=5

# 只保留1份
backupCount=1

# 不保留历史（仅轮转）
backupCount=0
```

## 🗂️ 日志管理建议

### 1. 定期检查
```bash
# 查看日志文件大小
du -h monitor.log*

# 查看磁盘使用
df -h .
```

### 2. 手动清理（如需要）
```bash
# 删除所有历史日志（保留当前）
rm monitor.log.[0-9]*

# 清空当前日志
> monitor.log
```

### 3. 备份重要日志
```bash
# 备份到其他目录
cp monitor.log* ~/backup/

# 压缩备份
tar -czf logs_backup_$(date +%Y%m%d).tar.gz monitor.log*
```

## ⚠️ 注意事项

1. **轮转不会丢失数据**
   - 当前写入会立即刷新
   - 轮转时会先关闭再重命名
   - 不会出现日志丢失

2. **并发写入安全**
   - RotatingFileHandler 线程安全
   - 多个进程同时写入时也是安全的

3. **磁盘空间**
   - 最大占用: `(maxBytes * (backupCount + 1))`
   - 当前配置: `5MB × 4 = 20MB`

4. **历史日志访问**
   - 历史日志是只读的
   - 不会再修改已轮转的文件

## 📊 对比

| 配置 | 轮转前 | 轮转后 |
|------|--------|--------|
| 单文件大小 | 无限制 ⚠️ | 5MB ✅ |
| 历史保留 | 无限制 ⚠️ | 3份 ✅ |
| 磁盘占用 | 可能无限增长 | 最多20MB |
| 管理难度 | 需手动清理 | 自动管理 |

## 🎯 最佳实践

### 推荐配置（当前）
```python
maxBytes=5*1024*1024    # 5MB
backupCount=3           # 3份历史
```

**适用场景**:
- 正常监控频率（60秒间隔）
- 磁盘空间有限
- 需要保留一定历史

### 高频监控
```python
maxBytes=10*1024*1024   # 10MB
backupCount=5           # 5份历史
```

### 存储受限
```python
maxBytes=2*1024*1024    # 2MB
backupCount=1           # 1份历史
```

---

**更新状态**: ✅ 已完成
**效果**: 日志文件自动管理，不会无限增长
