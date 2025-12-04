#!/bin/bash
# Build script for Printavo Quote Creator

echo "=========================================="
echo "Printavo Quote Creator - Build Script"
echo "=========================================="
echo ""

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist __pycache__

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Build with PyInstaller
echo ""
echo "Building application with universal binary support..."
echo "This will work on both Intel and Apple Silicon Macs."
echo ""

# Try universal2 first
pyinstaller printavo_quote_creator.spec

# Check if build was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ Build completed successfully!"
    echo "=========================================="
    echo ""

    echo "macOS app bundle created at: dist/PrintavoQuoteCreator.app"
    echo ""

    # Check architecture
    echo "Checking architecture support..."
    lipo -archs dist/PrintavoQuoteCreator.app/Contents/MacOS/PrintavoQuoteCreator

    echo ""
    echo "To distribute:"
    echo "1. Zip the app: cd dist && zip -r PrintavoQuoteCreator.zip PrintavoQuoteCreator.app"
    echo "2. Share the zip file with your team"
    echo "3. Users should unzip and drag to Applications folder"
    echo ""
    echo "Note: First time users open it, they may need to right-click → Open"
else
    echo ""
    echo "✗ Build failed. Check errors above."
    exit 1
fi