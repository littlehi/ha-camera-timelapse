#!/bin/bash

# Release preparation script for ha-camera-timelapse v0.4.0

set -e

VERSION="0.4.0"
RELEASE_DIR="release"
COMPONENT_DIR="custom_components/ha_camera_timelapse"

echo "🚀 Preparing release v${VERSION}..."

# Create release directory
mkdir -p ${RELEASE_DIR}

# Create release package
echo "📦 Creating release package..."
zip -r "${RELEASE_DIR}/ha-camera-timelapse-v${VERSION}.zip" \
    ${COMPONENT_DIR}/ \
    README.md \
    CHANGELOG.md \
    STATE_CHANGE_TRIGGER_FEATURE.md \
    USAGE_EXAMPLES.md \
    -x "*.pyc" "*__pycache__*" "*.git*"

# Verify package contents
echo "📋 Package contents:"
unzip -l "${RELEASE_DIR}/ha-camera-timelapse-v${VERSION}.zip"

# Create checksums
echo "🔐 Creating checksums..."
cd ${RELEASE_DIR}
sha256sum "ha-camera-timelapse-v${VERSION}.zip" > "ha-camera-timelapse-v${VERSION}.zip.sha256"
cd ..

echo "✅ Release package ready:"
echo "   📦 ${RELEASE_DIR}/ha-camera-timelapse-v${VERSION}.zip"
echo "   🔐 ${RELEASE_DIR}/ha-camera-timelapse-v${VERSION}.zip.sha256"

echo ""
echo "📝 Next steps:"
echo "1. Review the package contents"
echo "2. Test the package in a Home Assistant instance"
echo "3. Create GitHub release with tag v${VERSION}"
echo "4. Upload the zip file as a release asset"
echo "5. Use GITHUB_RELEASE_TEMPLATE.md for release notes"

echo ""
echo "🎯 Release ready for v${VERSION}!"