# ImageCrop v1.1.0 Release Notes

🎉 **Major Update: Cross-Platform Support & Enhanced User Experience**

We're excited to announce ImageCrop v1.1.0, which brings significant improvements to make the application more accessible and user-friendly across all platforms!

## ✨ What's New

### 🖥️ **Windows Support**
- **One-Click Execution**: New `run.bat` script allows Windows users to start the server with just a double-click
- **Smart Environment Validation**: Automatically checks Python and pip installation
- **User-Friendly Error Messages**: Clear instructions when issues are detected

### 🚀 **Enhanced Automation**
- **Auto Port Detection**: No more port conflicts! Automatically finds available ports (8000-8010)
- **Browser Auto-Launch**: Server automatically opens your browser when ready
- **Dependency Management**: Automatically installs required packages on first run

### 🔧 **Improved Developer Experience**
- **Cross-Platform Scripts**: Enhanced `run.sh` for Unix/Linux with better error handling
- **Comprehensive Environment Checks**: Python 3.8+ validation and dependency verification
- **Cleaner Repository**: Added comprehensive `.gitignore` patterns

## 🛠️ **Technical Improvements**

- **Non-Blocking Browser Launch**: Uses threading to prevent server startup delays
- **Robust Port Management**: Socket-based port detection with automatic fallback
- **Enhanced Error Handling**: Detailed error messages with solution suggestions
- **Code Optimization**: Removed redundant checks and improved startup logic

## 📥 **How to Use**

### Windows Users
1. Download the latest release
2. Double-click `run.bat`
3. That's it! Your browser will open automatically

### Unix/Linux Users
1. Download the latest release
2. Run `./run.sh` in terminal
3. Your browser will open automatically

## 🔄 **Upgrade Instructions**

If upgrading from v1.0.0:
1. Download the new release
2. Replace your existing files
3. No breaking changes - your existing setup will continue to work!

## 🐛 **Bug Fixes & Compatibility**

- Improved error handling across all platforms
- Better Python version detection
- Enhanced dependency resolution
- More reliable server startup process

## 📚 **Full Changelog**

See [CHANGELOG.md](./CHANGELOG.md) for complete details of all changes.

## 🙏 **Thanks**

Thank you for using ImageCrop! This release makes the application much more accessible to users across all platforms.

---

**Full Changelog**: https://github.com/KwangryeolPark/ImageCrop/compare/v1.0.0...v1.1.0
