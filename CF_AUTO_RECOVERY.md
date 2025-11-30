# 🔄 Cloudflare 卡住自动恢复功能

## 更新时间
2025-11-30 20:27

## 🎯 问题背景

程序运行一段时间后，可能出现无法跳过 Cloudflare 挑战的情况：
- Cloudflare 挑战页面一直卡住
- `wait_for_cloudflare()` 超时失败
- 同一页面反复失败

## ✅ 解决方案

### 自动检测和重启

当检测到同一页面 Cloudflare 失败次数超过阈值时，自动重启 Chrome Driver。

### 工作原理

1. **失败计数追踪**
   ```
   页面 245 → CF 失败 → 计数 +1
   页面 245 → CF 失败 → 计数 +1
   页面 245 → CF 失败 → 计数 +1 (达到阈值)
   ↓
   触发重启 Chrome Driver
   ```

2. **自动重置**
   ```
   页面成功加载 → 重置计数为 0
   切换到新页面 → 重置计数为 0
   ```

## ⚙️ 配置参数

### .env 配置
```bash
# Cloudflare 卡住检测
MAX_CF_FAILS=3  # 同一页面最大失败次数
```

### 推荐值
- **保守**（更容易触发重启）: `MAX_CF_FAILS=2`
- **标准**（推荐）: `MAX_CF_FAILS=3`
- **宽松**（较少重启）: `MAX_CF_FAILS=5`

## 📊 运行流程

### 正常情况
```
检查 p245
  ↓
遇到 CF → 等待 30秒
  ↓
✅ 挑战通过
  ↓
继续监控
```

### CF 失败一次
```
检查 p245
  ↓
遇到 CF → 等待 30秒
  ↓
❌ 超时失败 (1/3)
  ↓
⏳ 等待重试
  ↓
再次检查 p245
  ↓
✅ 成功 → 重置计数
```

### CF 连续失败（触发重启）
```
检查 p245
  ↓
❌ CF 失败 (1/3)
  ↓
❌ CF 失败 (2/3)
  ↓
❌ CF 失败 (3/3) 达到阈值
  ↓
🔄 触发 Chrome Driver 重启
  ↓
✅ 重启完成
  ↓
重置计数，继续检查 p245
```

## 🔍 日志示例

### CF 失败计数
```
⚠️  Cloudflare 挑战失败 (1/3)
❌ 第 1 次加载页面 245 失败: Cloudflare 挑战超时
⏳ 等待 10 秒后重试...

⚠️  Cloudflare 挑战失败 (2/3)
❌ 第 2 次加载页面 245 失败: Cloudflare 挑战超时
⏳ 等待 20 秒后重试...

⚠️  Cloudflare 挑战失败 (3/3)
❌ 同一页面 Cloudflare 失败 3 次，触发重启
```

### 自动重启
```
🔄 检测到 Cloudflare 卡住，执行强制重启...
🔄 重启 Chrome driver 以释放资源...
关闭旧 driver...
🚀 初始化 Chrome driver...
✅ Chrome driver 初始化成功
✅ Chrome driver 重启完成
✅ 重启完成，继续监控...
```

### 成功恢复
```
🔍 检查页面 245
⏳ 等待页面元素加载...
✅ 页面 245 加载成功
✅ 页面加载成功，重置 CF 失败计数（之前 3 次）
📊 找到 30 条评论
```

## 💡 技术实现

### 1. 失败追踪
```python
# 初始化
self.current_page = None
self.cf_fail_count = 0

# 检测页面切换
if self.current_page != current_page:
    self.cf_fail_count = 0  # 重置
```

### 2. 失败计数
```python
if not self.wait_for_cloudflare():
    self.cf_fail_count += 1
    
    if self.cf_fail_count >= Config.MAX_CF_FAILS:
        raise Exception("需要重启 Driver")
```

### 3. 异常处理和重启
```python
except Exception as e:
    if "需要重启 Driver" in str(e):
        self.restart_driver()
        self.cf_fail_count = 0  # 重置
        continue  # 继续监控
```

## 📈 效果对比

| 场景 | 修改前 | 修改后 |
|------|--------|--------|
| CF 卡住 | ❌ 一直失败，无法恢复 | ✅ 自动重启恢复 |
| 监控中断 | ⚠️ 需要人工重启 | ✅ 自动恢复 |
| 失败率 | 高（卡住后停止） | 低（自动恢复） |

## 🎯 使用场景

### 场景 1: 短暂的 CF 问题
```
CF 失败 1 次 → 重试 → 成功 → 继续
```
**结果**: 不触发重启

### 场景 2: 持续的 CF 卡住
```
CF 失败 3 次 → 触发重启 → 恢复正常
```
**结果**: 自动恢复，继续监控

### 场景 3: 页面切换
```
p245 CF 失败 2 次 → 切换到 p246 → 计数重置
```
**结果**: 新页面重新开始计数

## ⚙️ 调优建议

### 频繁触发重启
如果发现经常触发重启：
```bash
# 增加阈值
MAX_CF_FAILS=5
```

### CF 问题严重
如果 CF 问题很严重：
```bash
# 降低阈值以更快恢复
MAX_CF_FAILS=2
```

### 网络不稳定
```bash
# 增加 CF 超时时间
CLOUDFLARE_TIMEOUT=60

# 增加失败阈值
MAX_CF_FAILS=5
```

## ⚠️ 注意事项

1. **重启会中断当前检查**
   - 短暂中断（约10秒）
   - seen_comments 不会丢失
   - 会重新检查当前页面

2. **不影响其他重启机制**
   - 定期重启（N页一次）仍然生效
   - 两种重启机制独立工作

3. **计数器只针对当前页面**
   - 切换页面会重置
   - 不累积不同页面的失败

## 🔄 重启时机对比

| 重启类型 | 触发条件 | 频率 |
|----------|----------|------|
| 定期重启 | 检查N页后 | 每5页 |
| CF重启 | 同一页CF失败N次 | CF卡住时 |
| 手动重启 | 用户操作 | 按需 |

## 📊 监控建议

### 查看 CF 失败统计
```bash
# 查看 CF 失败次数
grep "Cloudflare 挑战失败" monitor.log | wc -l

# 查看触发的重启次数
grep "检测到 Cloudflare 卡住" monitor.log | wc -l
```

### 最佳实践
```bash
# 推荐配置
MAX_CF_FAILS=3
CLOUDFLARE_TIMEOUT=30
RESTART_INTERVAL=5
```

## 🎉 改进效果

- ✅ **自动恢复**: CF 卡住时自动重启
- ✅ **零停机**: 重启后立即继续监控
- ✅ **智能判断**: 只在真正卡住时重启
- ✅ **可配置**: 根据实际情况调整阈值

---

**更新状态**: ✅ 已完成
**建议**: 先使用默认配置（MAX_CF_FAILS=3），观察运行情况后调整
