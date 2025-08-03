# Release Checklist v0.4.0

## 📋 Pre-Release Checklist

### ✅ Code Quality
- [x] All Python files pass syntax validation
- [x] No breaking changes to existing functionality
- [x] Backward compatibility maintained
- [x] Error handling implemented
- [x] Resource cleanup properly handled

### ✅ Version Updates
- [x] Updated `manifest.json` version to 0.4.0
- [x] Updated switch entity version info (if applicable)
- [x] Version consistency across all files

### ✅ Documentation
- [x] README.md updated with new features
- [x] Created STATE_CHANGE_TRIGGER_FEATURE.md
- [x] Created USAGE_EXAMPLES.md
- [x] Created IMPLEMENTATION_SUMMARY.md
- [x] Created WORKFLOW_DIAGRAM.md
- [x] Created CHANGELOG.md

### ✅ Testing
- [x] Syntax validation passed
- [x] Configuration flow tested conceptually
- [x] Service definitions validated
- [x] Switch integration verified

## 🚀 Release Process

### 1. GitHub Repository Preparation
```bash
# Ensure all files are committed
git add .
git commit -m "feat: Add state change trigger mode v0.4.0"
git push origin main
```

### 2. Create GitHub Release
1. Go to GitHub repository
2. Click "Releases" → "Create a new release"
3. **Tag version**: `v0.4.0`
4. **Release title**: `v0.4.0 - State Change Trigger Mode`
5. **Description**: Use content from `GITHUB_RELEASE_TEMPLATE.md`
6. **Attach files**: 
   - Source code (auto-generated)
   - Optional: Create a zip of `custom_components/ha_camera_timelapse/`

### 3. Release Assets
Create a zip file containing:
```
ha-camera-timelapse-v0.4.0.zip
├── custom_components/
│   └── ha_camera_timelapse/
│       ├── __init__.py
│       ├── manifest.json
│       ├── config_flow.py
│       ├── coordinator.py
│       ├── switch.py
│       ├── const.py
│       ├── services.yaml
│       └── google_photos.py
├── README.md
├── CHANGELOG.md
└── STATE_CHANGE_TRIGGER_FEATURE.md
```

### 4. HACS Compatibility
Ensure the release is compatible with HACS:
- [x] `manifest.json` is valid
- [x] `hacs.json` exists (if needed)
- [x] Repository structure follows HACS standards

### 5. Post-Release Tasks
- [ ] Update any external documentation
- [ ] Announce in Home Assistant community forums
- [ ] Update HACS repository (if applicable)
- [ ] Monitor for issues and feedback

## 📝 Release Notes Template

Copy this for the GitHub release description:

```markdown
# 🎯 State Change Trigger Mode

Major new feature: Capture timelapse frames based on entity state changes!

## ✨ Key Features
- Motion detection triggered timelapses
- Door/window state monitoring
- Environmental change recording
- 100% backward compatible

## 🔧 Usage
1. Configure trigger mode in settings
2. Start with the switch (same as before!)
3. Frames captured on state changes
4. Stop to generate video

## 📚 Documentation
- [Feature Guide](STATE_CHANGE_TRIGGER_FEATURE.md)
- [Usage Examples](USAGE_EXAMPLES.md)
- [Full Changelog](CHANGELOG.md)

Perfect for smart home automation and event-driven monitoring!
```

## 🎯 Success Criteria

Release is successful when:
- [ ] GitHub release is published
- [ ] Documentation is accessible
- [ ] No critical issues reported within 24 hours
- [ ] Community feedback is positive
- [ ] HACS users can update successfully

## 🐛 Rollback Plan

If critical issues are found:
1. Create hotfix branch
2. Fix critical issues
3. Release v0.4.1 patch
4. Update documentation accordingly

## 📞 Support Preparation

Be ready to handle:
- Configuration questions
- Migration issues
- Feature usage questions
- Bug reports

Monitor:
- GitHub Issues
- Home Assistant Community Forum
- Discord/Reddit mentions