# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2025-10-08

### Added
- **Windows Support**: Added `run.bat` script for Windows users with double-click execution
- **Auto Port Detection**: Automatically finds available ports (8000-8010) when default port is occupied
- **Browser Auto-Launch**: Automatically opens browser after server starts successfully
- **Environment Validation**: Added comprehensive Python and pip installation checks
- **Dependency Auto-Installation**: Automatically installs required packages from requirements.txt
- **Cross-Platform Compatibility**: Enhanced support for both Windows and Unix/Linux systems
- **Comprehensive .gitignore**: Added patterns for Python, IDE, OS-specific, and temporary files
- **Version Management System**: Centralized version control with Git integration (`version.py`)
- **Version API Endpoint**: RESTful `/api/version` endpoint for programmatic version access
- **Startup Version Display**: Version information shown in run.sh and run.bat scripts
- **Multi-language Placeholders**: Enhanced UI placeholders for all supported languages
- **Cache Prevention**: Development-friendly HTTP headers for real-time updates

### Changed
- **Enhanced Startup Scripts**: Improved `run.sh` with better error handling and user feedback
- **Server Startup Logic**: Refactored main.py to handle port conflicts and browser launching
- **User Experience**: Streamlined setup process from manual steps to one-click execution
- **Language Selection Flow**: Fixed auto-redirect to prevent language selector flash
- **HTML Structure**: Corrected Image Description form layout (removed duplicate labels)

### Improved
- **Error Handling**: Added detailed error messages with solution suggestions
- **Threading**: Non-blocking browser launch using separate thread
- **Logging**: Better console output with clear status messages
- **Code Organization**: Removed redundant file existence checks
- **Version Tracking**: Real-time Git branch and commit status monitoring
- **Development Workflow**: Automatic cache prevention for faster development cycles

### Technical Details
- Port detection using socket programming (8000-8010 range)
- Browser launch with 3-second delay for server stabilization
- Python 3.8+ version validation
- Automatic fallback from python3 to python command
- Windows batch script with pause on errors for better debugging

## [1.0.0] - 2025-09-23

### Added
- Initial release of ImageCrop
- FastAPI-based web application for image cropping
- Multi-language support (English, Korean, Japanese, German, French, Russian, Chinese)
- Web-based cropping interface with interactive tools
- Static file serving for HTML, CSS, and JavaScript
- Basic server startup with uvicorn
- Image processing capabilities using Pillow
- Responsive web design for various screen sizes

### Features
- Drag-and-drop image upload
- Interactive cropping with visual feedback
- Multiple image format support
- Localized user interface
- RESTful API endpoints
- Real-time image preview

---

## Version Numbering

This project uses [Semantic Versioning](https://semver.org/):
- **MAJOR** version when you make incompatible API changes
- **MINOR** version when you add functionality in a backwards compatible manner  
- **PATCH** version when you make backwards compatible bug fixes

## Links
- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)
