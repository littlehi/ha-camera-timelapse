# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.2] - 2025-01-29

### 🐛 Fixed
- **Critical FFmpeg Error**: Fixed video generation failure that resulted in 0-byte output files
  - Resolved MJPEG encoder profile parameter conflict
  - Used stream-specific parameters (`-c:v:0`, `-profile:v:0`, etc.) to avoid parameter conflicts
  - Fixed "Unable to parse option value 'high'" error for MJPEG poster streams
  - Ensured proper separation between main video stream and poster stream encoding parameters

## [0.3.1] - 2025-01-29

### 🎨 Enhanced
- **Video poster/thumbnail**: Modified video generation to use the second-to-last frame as video poster/thumbnail
  - Provides a more representative preview of the timelapse content
  - Uses FFmpeg's `attached_pic` disposition to embed the poster frame
  - Fallback to first frame if only one frame is available
  - Applies to both direct pattern and concat video generation methods

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