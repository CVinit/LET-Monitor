# 🔍 评论筛选功能说明

## 更新时间
2025-11-30 19:15

## 🎯 功能说明

添加了智能评论筛选机制，只通知符合特定条件的评论。

## ✅ 筛选条件

### 必须满足的条件（AND逻辑）

1. **包含特定图片** ✅
   - 必须包含指定的图片标签
   - 默认图片URL: `https://lowendtalk.com/uploads/editor/jm/2b3rylu483wr.png`

2. **不包含引用** ✅
   - 不能包含 `<blockquote>` 标签
   - 即：不是引用别人的评论

### 筛选逻辑
```python
if 有指定图片 AND 没有blockquote:
    ✅ 发送通知
else:
    ❌ 跳过
```

## 📝 实现方式

### HTML 检测

**检查图片**:
```python
required_image = message_elem.find('img', src='指定URL')
if not required_image:
    continue  # 跳过
```

**检查引用**:
```python
has_blockquote = message_elem.find('blockquote') is not None
if has_blockquote:
    continue  # 跳过
```

## ⚙️ 配置选项

### .env 配置
```bash
# 筛选配置
REQUIRED_IMAGE_URL=https://lowendtalk.com/uploads/editor/jm/2b3rylu483wr.png
FILTER_BLOCKQUOTE=true  # 是否过滤包含引用的评论
```

### 配置说明

**REQUIRED_IMAGE_URL**:
- 指定必须包含的图片URL
- 完整匹配图片的 `src` 属性
- 可以修改为其他图片URL

**FILTER_BLOCKQUOTE**:
- `true`: 过滤掉包含引用的评论（默认）
- `false`: 不过滤引用，只要有图片就通知

## 📊 筛选效果示例

### 示例 1: ✅ 符合条件（会通知）

```html
<div class="Message userContent">
    <img src="https://lowendtalk.com/uploads/editor/jm/2b3rylu483wr.png" width="100%">
    <p>HyperhostSolutions: £10/yr...</p>
    <!-- 没有 blockquote -->
</div>
```
**结果**: ✅ 发送通知

### 示例 2: ❌ 不符合（跳过 - 无图片）

```html
<div class="Message userContent">
    <p>Some comment without image...</p>
</div>
```
**结果**: ❌ 跳过（不包含指定图片）

### 示例 3: ❌ 不符合（跳过 - 有引用）

```html
<div class="Message userContent">
    <img src="https://lowendtalk.com/uploads/editor/jm/2b3rylu483wr.png" width="100%">
    <blockquote>
        引用别人的话...
    </blockquote>
    <p>我的回复...</p>
</div>
```
**结果**: ❌ 跳过（包含 blockquote）

### 示例 4: ❌ 不符合（跳过 - 图片URL不同）

```html
<div class="Message userContent">
    <img src="https://lowendtalk.com/uploads/editor/xx/different.png" width="100%">
    <p>Some content...</p>
</div>
```
**结果**: ❌ 跳过（图片URL不匹配）

## 🔍 日志输出

### 符合条件
```
🎯 发现 FAT32 的评论: Comment_4629336
✅ 评论 Comment_4629336 通过筛选（有图片且无引用）
🎉 在页面 245 发现 1 条 FAT32 的评论
📤 已发送评论 Comment_4629336 的通知
```

### 不符合条件
```
🎯 发现 FAT32 的评论: Comment_4629400
跳过评论 Comment_4629400: 不包含指定图片

🎯 发现 FAT32 的评论: Comment_4629401
跳过评论 Comment_4629401: 包含引用(blockquote)

📭 页面 246 没有 FAT32 的评论，继续下一页...
```

## 💡 使用场景

### 为什么需要这个筛选？

1. **过滤广告帖** - 只关注带官方图片的优惠
2. **过滤回复** - 不关心引用别人的回复
3. **精准通知** - 只通知真正的新优惠发布

### 典型应用

**黑五优惠监控**:
- 官方优惠帖都有统一图片标识
- 引用别人的帖子不是新优惠
- 只需要首发优惠通知

## 🧪 测试验证

```bash
# 测试筛选功能
python monitor.py --test --start-page 245
```

### 预期结果

如果页面有多条 FAT32 评论：
- ✅ 只通知符合条件的（有图片无引用）
- ❌ 跳过不符合的（记录在日志中）

## ⚙️ 高级配置

### 1. 关闭引用过滤

如果想接收所有有图片的评论（包括引用）：
```bash
FILTER_BLOCKQUOTE=false
```

### 2. 修改目标图片

如果要监控其他图片标识：
```bash
REQUIRED_IMAGE_URL=https://lowendtalk.com/uploads/editor/xx/other.png
```

### 3. 调试模式

查看所有跳过的评论：
```bash
# 日志中查找
grep "跳过评论" monitor.log
```

## 📈 效果统计

### 过滤效果

假设 FAT32 发了 10 条评论：
- 5 条纯优惠（有图片无引用）→ ✅ 通知
- 3 条回复别人（有引用）→ ❌ 跳过
- 2 条普通评论（无图片）→ ❌ 跳过

**通知数量**: 5 条（50%）
**准确率**: 100%（都是真正的优惠）

## ⚠️ 注意事项

1. **图片URL必须完全匹配**
   - 大小写敏感
   - 参数也要匹配
   - 建议从实际HTML复制

2. **blockquote检测**
   - 检测任何级别的 blockquote
   - 包括嵌套的引用

3. **日志级别**
   - 跳过的评论使用 `debug` 级别
   - 不会在控制台显示（只在日志文件中）
   - 符合条件的评论使用 `info` 级别

## 🎯 最佳实践

### 推荐配置
```bash
# .env
REQUIRED_IMAGE_URL=https://lowendtalk.com/uploads/editor/jm/2b3rylu483wr.png
FILTER_BLOCKQUOTE=true
```

### 查看筛选效果
```bash
# 实时查看通过筛选的评论
tail -f monitor.log | grep "通过筛选"

# 查看跳过的评论
tail -f monitor.log | grep "跳过评论"
```

---

**更新状态**: ✅ 已完成
**建议**: 先测试确认图片URL正确
