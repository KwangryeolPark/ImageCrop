# Image Cropper & Resizer

This project is a web-based tool for cropping and resizing images from a specified local folder. Built with **FastAPI** and a modern web frontend, it provides an intuitive interface to manage and process your image files efficiently.

## Features

-   **Language Selection**: Choose from multiple languages, including English, Korean, Japanese, and more, for a localized user experience.
-   **Image Folder Management**: Easily load all images from a local directory by simply entering its path.
-   **Interactive Cropping**: A visual, interactive cropper allows you to define a precise area to crop.
-   **Aspect Ratio Control**: Automatically resize your crop box to maintain a specific aspect ratio, with presets for common sizes like 512x512 and 512x768.
-   **Save & Export**: Save cropped images to a dedicated `resized` subfolder. You can choose to either save the cropped image as-is or resize it to your target dimensions.
-   **Image Description**: Add an optional text description that gets saved alongside the processed image in a `.txt` file.

---

## Getting Started

### Prerequisites

You'll need **Python 3.8+** and **uv** (or pip) installed on your system.

### Installation

1.  Clone this repository:
    ```bash
    git clone https://github.com/KwangryeolPark/ImageCrop.git
    cd ImageCrop
    ```
2.  Install the required packages.
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

To run the application, execute the `run.sh` script or use the `uvicorn` command directly:

```bash
# Using the provided script
sh run.sh

# Or directly with uvicorn
uvicorn main:app --reload
```
This will start the development server at http://127.0.0.1:8000. Open this URL in your web browser to use the application.

## Project Structure & File Descriptions

| File/Directory            | Description                                                                                                                                                                   |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [main.py](http://main.py) | The core backend application built with FastAPI. It handles all API endpoints for listing, serving, cropping, and saving images. It also manages language and settings files. |
| cropper.html              | The main HTML file for the image cropping interface. This is the primary user-facing page of the application.                                                                 |
| index.html                | The initial landing page where users select their preferred language.                                                                                                         |
| static/                   | Contains static web assets: style.css for all styling and script.js & cropper.js for frontend logic.                                                                          |
| locales/                  | Stores JSON files for different language translations. The application dynamically loads these to support multiple languages.                                                 |
| requirements.txt          | Lists the Python packages required to run the backend, including                                                                                                              |
| .gitignore                | Configures files and directories that Git should ignore, such as virtual environments                                                                                         |
| [run.sh](http://run.sh)   | A simple shell script to start the FastAPI server with uvicorn.                                                                                                               |


## Acknowledgements
* FastAPI: A modern, fast web framework for building APIs.
* Pillow: The friendly Python Imaging Library, used for all image processing tasks.
* GitHub's gitignore templates: The .gitignore file is based on their excellent Python template.
