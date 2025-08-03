# 🚀 GitHub Release Guide v0.4.0

## 📦 Release Package Ready

发布包已准备完成：
- ✅ 版本号已更新到 0.4.0
- ✅ 发布包已创建：`release/ha-camera-timelapse-v0.4.0.zip`
- ✅ 校验和已生成：`release/ha-camera-timelapse-v0.4.0.zip.sha256`
- ✅ 所有文档已准备完成

## 🎯 发布步骤

### 1. 提交所有更改到 Git

```bash
git add .
git commit -m "feat: Add state change trigger mode v0.4.0

- Add dual trigger modes (interval/state_change)
- Implement state change monitoring
- Enhance configuration UI
- Add comprehensive documentation
- Maintain 100% backward compatibility"

git push origin main
```

### 2. 创建 GitHub Release

1. **访问 GitHub 仓库**：https://github.com/littlehi/ha-camera-timelapse

2. **点击 "Releases"** → **"Create a new release"**

3. **填写发布信息**：
   - **Tag version**: `v0.4.0`
   - **Release title**: `v0.4.0 - State Change Trigger Mode`
   - **Target**: `main` branch

4. **发布描述**：复制 `GITHUB_RELEASE_TEMPLATE.md` 的内容

5. **上传文件**：
   - 上传 `release/ha-camera-timelapse-v0.4.0.zip`
   - 上传 `release/ha-camera-timelapse-v0.4.0.zip.sha256`

6. **发布选项**：
   - ✅ Set as the latest release
   - ✅ Create a discussion for this release (可选)

### 3. 验证发布

发布后检查：
- [ ] Release 页面显示正确
- [ ] 下载链接工作正常
- [ ] 文档链接可访问
- [ ] 版本标签正确

## 📋 发布内容摘要

### 🎯 主要新功能
- **状态变化触发模式**：基于实体状态变化捕获图片
- **双触发系统**：支持间隔和状态变化两种模式
- **智能家居集成**：运动检测、门窗监控、环境变化等

### 🔧 技术改进
- 高效的状态监听机制
- 自动资源清理
- 增强的错误处理
- 改进的日志记录

### 🔄 向后兼容
- 100% 兼容现有配置
- 默认行为保持不变
- 所有原有功能保留

## 📚 文档结构

```
📁 Documentation
├── 📄 README.md (主要文档，已更新)
├── 📄 STATE_CHANGE_TRIGGER_FEATURE.md (详细功能说明)
├── 📄 USAGE_EXAMPLES.md (使用示例)
├── 📄 IMPLEMENTATION_SUMMARY.md (实现总结)
├── 📄 WORKFLOW_DIAGRAM.md (工作流程图)
├── 📄 CHANGELOG.md (变更日志)
└── 📄 RELEASE_NOTES_v0.4.0.md (发布说明)
```

## 🎉 发布后任务

### 立即任务
- [ ] 在 Home Assistant 社区论坛发布公告
- [ ] 更新任何外部文档链接
- [ ] 监控 GitHub Issues 中的反馈

### 后续任务
- [ ] 收集用户反馈
- [ ] 监控性能和稳定性
- [ ] 计划下一个版本的功能

## 📞 支持准备

准备回答的常见问题：

1. **如何从间隔模式切换到状态变化模式？**
   - 进入集成配置，选择触发模式

2. **现有配置会受影响吗？**
   - 不会，100% 向后兼容

3. **支持哪些类型的触发实体？**
   - 任何 Home Assistant 实体都可以作为触发源

4. **如何调试状态变化触发？**
   - 启用调试模式，查看日志

## 🔗 重要链接

- **GitHub Repository**: https://github.com/littlehi/ha-camera-timelapse
- **Issues**: https://github.com/littlehi/ha-camera-timelapse/issues
- **Discussions**: https://github.com/littlehi/ha-camera-timelapse/discussions
- **HACS**: (如果已提交到 HACS)

## 🎊 发布完成！

一旦发布完成，这将是一个重要的里程碑版本，为用户提供了更灵活和智能的延时摄影解决方案！

---

**记住**：这个版本保持了用户熟悉的开关控制方式，同时添加了强大的事件驱动功能。这是向后兼容性和创新功能的完美结合！