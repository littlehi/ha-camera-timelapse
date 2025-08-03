#!/usr/bin/env python3
"""
测试脚本：验证视频封面修改是否正确
"""

import os
import tempfile
import subprocess
from PIL import Image
import numpy as np

def create_test_frames(frame_dir, num_frames=5):
    """创建测试帧图像"""
    os.makedirs(frame_dir, exist_ok=True)
    
    for i in range(num_frames):
        # 创建不同颜色的测试图像
        color = (i * 50 % 255, (i * 80) % 255, (i * 120) % 255)
        img = Image.new('RGB', (640, 480), color)
        
        # 添加帧号文本
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        try:
            # 尝试使用默认字体
            font = ImageFont.load_default()
        except:
            font = None
        
        text = f"Frame {i+1}"
        draw.text((50, 50), text, fill=(255, 255, 255), font=font)
        
        frame_path = os.path.join(frame_dir, f"frame_{i:06d}.jpg")
        img.save(frame_path, "JPEG")
        print(f"Created test frame: {frame_path}")

def test_ffmpeg_poster_command():
    """测试FFmpeg封面命令"""
    with tempfile.TemporaryDirectory() as temp_dir:
        frame_dir = os.path.join(temp_dir, "frames")
        output_file = os.path.join(temp_dir, "test_timelapse.mp4")
        
        # 创建测试帧
        create_test_frames(frame_dir, 5)
        
        # 获取帧文件列表
        frame_files = sorted([f for f in os.listdir(frame_dir) if f.startswith("frame_") and f.endswith(".jpg")])
        print(f"Created {len(frame_files)} test frames")
        
        # 选择倒数第二个图像作为封面
        poster_frame = None
        if len(frame_files) >= 2:
            poster_frame = os.path.join(frame_dir, frame_files[-2])  # 倒数第二个图像
            print(f"Using second-to-last frame as poster: {frame_files[-2]}")
        elif len(frame_files) == 1:
            poster_frame = os.path.join(frame_dir, frame_files[0])  # 如果只有一帧，使用第一帧
            print(f"Only one frame available, using it as poster: {frame_files[0]}")
        
        # 构建FFmpeg命令
        frame_pattern = os.path.join(frame_dir, "frame_%06d.jpg")
        
        cmd = [
            "ffmpeg",
            "-y",  # 覆盖现有文件
            "-framerate", "10",  # 输入帧率
            "-i", frame_pattern,  # 输入模式
        ]
        
        # 如果有封面图像，添加封面输入
        if poster_frame and os.path.exists(poster_frame):
            cmd.extend(["-i", poster_frame])  # 添加封面图像作为第二个输入
        
        # 如果有封面图像，设置封面映射
        if poster_frame and os.path.exists(poster_frame):
            cmd.extend([
                "-map", "0:v",  # 映射第一个输入的视频流
                "-map", "1:v",  # 映射第二个输入（封面）的视频流
                "-c:v:0", "libx264",  # 主视频流使用H264编码器
                "-c:v:1", "mjpeg",  # 封面使用MJPEG编码
                "-preset:v:0", "medium",  # 主视频流使用更平衡的预设
                "-crf:v:0", "23",  # 主视频流使用更好的质量
                "-profile:v:0", "high",  # 只对主视频流使用高配置文件
                "-level:v:0", "4.0",  # 只对主视频流提高级别
                "-pix_fmt:v:0", "yuv420p",  # 主视频流像素格式
                "-disposition:v:1", "attached_pic",  # 设置第二个视频流为附加图片（封面）
            ])
        else:
            cmd.extend([
                "-c:v", "libx264",  # 视频编码器
                "-preset", "medium",  # 使用更平衡的预设，提高兼容性
                "-crf", "23",  # 使用更好的质量，提高兼容性
                "-profile:v", "high",  # 使用高配置文件提高兼容性
                "-level", "4.0",  # 提高级别
                "-pix_fmt", "yuv420p",  # 像素格式
            ])
        
        cmd.extend([
            "-movflags", "+faststart",  # 优化网络播放
        ])
        
        cmd.extend([
            "-metadata", "encoder=Test Camera Timelapse",  # 添加编码器信息
            output_file
        ])
        
        print(f"FFmpeg command: {' '.join(cmd)}")
        
        # 检查FFmpeg是否可用
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            print("FFmpeg is available")
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Video created successfully: {output_file}")
                if os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    print(f"   File size: {file_size} bytes")
                    
                    # 检查视频信息
                    info_cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", output_file]
                    info_result = subprocess.run(info_cmd, capture_output=True, text=True)
                    if info_result.returncode == 0:
                        import json
                        info = json.loads(info_result.stdout)
                        streams = info.get("streams", [])
                        print(f"   Video streams: {len(streams)}")
                        for i, stream in enumerate(streams):
                            print(f"     Stream {i}: {stream.get('codec_name')} - {stream.get('disposition', {})}")
                else:
                    print("❌ Output file was not created")
            else:
                print(f"❌ FFmpeg failed with return code {result.returncode}")
                print(f"   stderr: {result.stderr}")
                
        except FileNotFoundError:
            print("❌ FFmpeg not found. Please install FFmpeg to test this functionality.")
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg version check failed: {e}")

if __name__ == "__main__":
    print("Testing video poster modification...")
    test_ffmpeg_poster_command()
    print("Test completed.")