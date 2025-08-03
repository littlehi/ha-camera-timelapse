# Changelog

All notable changes to this project will be documented in this file.

## [0.4.0] - 2024-12-XX

### 🎯 Major Features Added
- **State Change Trigger Mode**: Capture frames when entity states change instead of fixed intervals
- **Dual Trigger System**: Support both interval and state-change based frame capture
- **Enhanced Configuration UI**: New trigger mode and entity selectors

### ✨ New Features
- Motion detection triggered timelapses
- Door/window state monitoring
- Environmental change recording (temperature, humidity, etc.)
- Device state change monitoring
- Real-time trigger mode display in switch entity

### 🔧 Technical Improvements
- Efficient state change monitoring using HA event system
- Automatic state listener cleanup
- Enhanced error handling and resource management
- Improved logging and debugging capabilities

### 🔄 Backward Compatibility
- 100% compatible with existing configurations
- Default behavior unchanged for existing users
- All previous features preserved

### 📚 Documentation
- Comprehensive feature documentation
- Usage examples and scenarios
- Implementation details and workflow diagrams

## [0.3.2] - Previous Release

### Features
- Google Photos integration
- Smart storage management
- Auto-delete after upload
- Multi-language support
- Task management and history

---

## Migration Guide

### From 0.3.x to 0.4.0
- No action required for existing users
- Existing configurations will continue to work
- New trigger mode options available in configuration
- Consider exploring state change triggers for event-driven timelapses