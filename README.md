# Image Cropper & Resizer

This project is a web-based tool for cropping and resizing images from a specified local folder. Built with **FastAPI** and a modern web frontend, it provides an intuitive interface to manage and process your image files efficiently.

## Features

-   **Language Selection**: Choose from multiple languages, including English, Korean, Japanese, and more, for a localized user experience.
-   **Image Folder Management**: Easily load all images from a local directory by simply entering its path.
-   **Interactive Cropping**: A visual, interactive cropper allows you to define a precise area to crop.
-   **Aspect Ratio Control**: Automatically resize your crop box to maintain a specific aspect ratio, with presets for common sizes like 512x512 and 512x768.
-   **Save & Export**: Save cropped images to a dedicated `resized` subfolder. You can choose to either save the cropped image as-is or resize it to your target dimensions.
-   **Image Description**: Add an optional text description that gets saved alongside the processed image in a `.txt` file.
-   **🆕 Cross-Platform Support**: Easy-to-use startup scripts for both Windows (`run.bat`) and Unix/Linux (`run.sh`) systems.
-   **🆕 Auto Port Detection**: Automatically finds available ports (8000-8010) when the default port is occupied.
-   **🆕 Browser Auto-Launch**: Automatically opens your browser after the server starts successfully.
-   **🆕 Environment Validation**: Comprehensive checks for Python and pip installation with helpful error messages.
-   **🆕 Version Management**: Real-time version tracking with Git integration, branch status, and commit information.

---

## Getting Started

### Prerequisites

You'll need **Python 3.8+** installed on your system. The startup scripts will automatically check and install required dependencies.

### Installation

#### For Windows Users

1.  Clone this repository:
    ```cmd
    git clone https://github.com/KwangryeolPark/ImageCrop.git
    cd ImageCrop
    ```
2.  Double-click `run.bat` to automatically install dependencies and start the server.

#### For Linux/macOS Users

1.  Clone this repository:
    ```bash
    git clone https://github.com/KwangryeolPark/ImageCrop.git
    cd ImageCrop
    ```
2.  Make the script executable and run:
    ```bash
    chmod +x run.sh
    ./run.sh
    ```

#### Manual Installation (All Platforms)

If you prefer to install dependencies manually:
```bash
pip install -r requirements.txt
```

### Running the Application

#### Windows
Simply double-click `run.bat` file. The script will:
- Automatically validate your Python installation
- Install required dependencies if needed
- Start the server on an available port (8000-8010)
- Open your browser automatically

#### Linux/macOS
Run the following command in your terminal:
```bash
./run.sh
```
The script will:
- Check Python 3.8+ installation
- Validate pip availability
- Install dependencies automatically
- Start the server and open your browser

#### Manual Start (All Platforms)
You can also start the server manually:
```bash
# Direct method
python main.py

# Or using uvicorn directly
uvicorn main:app --reload
```

The application will automatically find an available port (starting from 8000) and display the URL in the console. Your browser will open automatically, or you can manually navigate to the displayed URL.

---

## Releases

<details>
<summary><strong>v1.1.0</strong> - 2025-10-08 🎉</summary>

### What's New
- **🖥️ Windows Support**: Added `run.bat` script for one-click execution on Windows
- **🚀 Auto Port Detection**: Automatically finds available ports (8000-8010) when default port is occupied
- **🌐 Browser Auto-Launch**: Automatically opens browser after server starts successfully
- **✅ Environment Validation**: Comprehensive Python and pip installation checks
- **📦 Dependency Management**: Automatic installation of required packages
- **🔧 Enhanced Scripts**: Improved error handling and user feedback across all platforms

### Technical Improvements
- Non-blocking browser launch using threading
- Robust port management with socket-based detection
- Enhanced error messages with solution suggestions
- Cross-platform compatibility improvements

[View Full Changelog](./CHANGELOG.md) | [Release Notes](./release-notes/RELEASE_NOTES_v1.1.0.md)
</details>

---

## Project Structure & File Descriptions

<details>
<summary><strong>Project Structure & File Descriptions</strong></summary>

| File/Directory            | Description                                                                                                                                                                   |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [main.py](http://main.py) | The core backend application built with FastAPI. Handles API endpoints, image processing, and includes auto port detection and browser launching features. |
| **version.py** | **🆕 Version management system** with Git integration, branch tracking, commit status, and `/api/version` endpoint support. |
| **run.bat** | **🆕 Windows startup script** with environment validation, dependency installation, version display, and one-click execution support. |
| **run.sh** | **Enhanced Unix/Linux startup script** with Python version checking, pip validation, version display, and automatic dependency management. |
| cropper.html              | The main HTML file for the image cropping interface. This is the primary user-facing page of the application.                                                                 |
| index.html                | The initial landing page where users select their preferred language.                                                                                                         |
| static/                   | Contains static web assets: style.css for all styling and script.js & cropper.js for frontend logic.                                                                          |
| locales/                  | Stores JSON files for different language translations. The application dynamically loads these to support multiple languages.                                                 |
| requirements.txt          | Lists the Python packages required to run the backend, including FastAPI and Pillow.                                                                                              |
| **CHANGELOG.md**                | **🆕 Version history and detailed change documentation following Keep a Changelog standard.** |
| **release-notes/**                | **🆕 Directory containing detailed release notes for each version.** |
| .gitignore                | **Enhanced Git ignore patterns** for Python projects, IDEs, OS-specific files, and development artifacts.                                                                                         |

</details>


## Acknowledgements
* FastAPI: A modern, fast web framework for building APIs.
* Pillow: The friendly Python Imaging Library, used for all image processing tasks.
* GitHub's gitignore templates: The .gitignore file is based on their excellent Python template.
