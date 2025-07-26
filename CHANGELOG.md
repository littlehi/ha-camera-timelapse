# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-01-27

### 🎉 Added
- **Auto-delete local files after upload**: New `delete_after_upload` configuration option
  - Automatically deletes local video files after successful Google Photos upload
  - Configurable in the integration UI (disabled by default)
  - Only deletes files after confirmed successful upload
  - Includes detailed logging with file size information
- **Multi-language support**: Added Chinese (zh) and improved English (en) translations
- **Enhanced task tracking**: Added `local_file_deleted` status to task registry

### 🔧 Improved
- **Google Photos upload compatibility**: 
  - Added service-based upload approach as primary method
  - Fallback to direct function import for compatibility
  - Better error handling and troubleshooting information
- **Configuration flow**: Enhanced UI with Google Photos and file deletion options
- **Logging**: More detailed and informative log messages throughout the system

### 🐛 Fixed
- **Critical naming conflict**: Fixed "'bool' object is not callable" error
  - Renamed `_upload_to_google_photos` boolean to `_upload_to_google_photos_enabled`
  - Resolved conflict between configuration variable and method name
- **Google Photos integration**: Improved service detection and error reporting

### 🛡️ Security
- **Safe file deletion**: 
  - Permission checks before deletion
  - File existence validation
  - Post-deletion verification
  - Error isolation (deletion failures don't affect main functionality)

## [0.2.0] - Previous Release

### Added
- Google Photos integration support
- Task management system
- Enhanced error handling

## [0.1.0] - Initial Release

### Added
- Basic timelapse functionality
- Camera entity integration
- Configurable intervals and duration
- Local file output