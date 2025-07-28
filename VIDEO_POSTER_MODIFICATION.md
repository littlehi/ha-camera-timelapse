# 视频封面修改说明

## 修改内容

本次修改将延时摄影视频的封面（poster/thumbnail）从默认设置改为使用**倒数第二个图像**。

## 修改原因

- **更好的代表性**：倒数第二个图像通常能更好地代表整个延时摄影的内容，而不是开始时的状态
- **避免初始化问题**：第一帧可能包含摄像头初始化或调整的问题
- **更好的预览体验**：用户在查看视频文件时能看到更有意义的缩略图

## 技术实现

### 修改的文件
- `custom_components/ha_camera_timelapse/coordinator.py`

### 修改的方法
- `_generate_timelapse()` 方法中的两种视频生成方式：
  1. 直接模式（Direct pattern approach）
  2. 连接模式（Concat method）

### FFmpeg 参数
添加了以下 FFmpeg 参数来设置视频封面：

```bash
# 添加封面图像作为第二个输入
-i /path/to/second_to_last_frame.jpg

# 映射视频流和封面流
-map 0:v                    # 映射主视频流
-map 1:v                    # 映射封面图像流
-c:v:1 mjpeg               # 封面使用MJPEG编码
-disposition:v:1 attached_pic  # 设置为附加图片（封面）
```

### 逻辑处理
```python
# 选择倒数第二个图像作为封面
poster_frame = None
if len(frame_files) >= 2:
    poster_frame = os.path.join(frame_dir, frame_files[-2])  # 倒数第二个图像
    _LOGGER.info("Using second-to-last frame as poster: %s", frame_files[-2])
elif len(frame_files) == 1:
    poster_frame = os.path.join(frame_dir, frame_files[0])  # 如果只有一帧，使用第一帧
    _LOGGER.info("Only one frame available, using it as poster: %s", frame_files[0])
```

## 测试验证

创建了测试脚本 `test_poster_modification.py` 来验证修改：

- ✅ 创建测试帧图像
- ✅ 验证 FFmpeg 命令构建
- ✅ 确认视频生成成功
- ✅ 验证视频包含两个流：主视频流和封面流
- ✅ 确认封面流标记为 `attached_pic`

## 兼容性

- **向后兼容**：不影响现有功能
- **错误处理**：如果封面图像不存在，会跳过封面设置
- **日志记录**：添加了详细的日志信息用于调试

## 使用效果

用户在文件管理器或媒体播放器中查看生成的延时摄影视频时，将看到倒数第二帧作为视频的缩略图/封面，提供更好的预览体验。