import os
import io
import json
import socket
import webbrowser
import threading
import time
import uvicorn
from contextlib import closing
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from PIL import Image

# --- FastAPI App ---
app = FastAPI()

# --- Pydantic Models ---
class ImageListRequest(BaseModel):
    folder_path: str

class CropRequest(BaseModel):
    folder_path: str
    image_name: str
    coords: dict
    description: Optional[str] = ""
    target_width: Optional[int] = None
    target_height: Optional[int] = None
    resize: bool = False

class LanguageRequest(BaseModel):
    language: str

class SettingsRequest(BaseModel):
    last_image_dir: Optional[str] = None

LANGUAGE_FILE = "language.json"
SETTINGS_FILE = "save.json" # 설정 파일 이름 추가

# --- API Endpoints ---
@app.get("/")
async def read_root():
    if os.path.exists(LANGUAGE_FILE):
        return FileResponse('static/cropper.html')
    else:
        return FileResponse('static/index.html')

@app.get("/cropper")
async def get_cropper_page():
    return FileResponse('static/cropper.html')

# --- Language API ---
@app.post("/api/save-language")
async def save_language(request: LanguageRequest):
    try:
        with open(LANGUAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump({"language": request.language}, f)
        return {"status": "success", "language": request.language}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save language file: {e}")

@app.get("/api/get-language")
async def get_language():
    if not os.path.exists(LANGUAGE_FILE):
        raise HTTPException(status_code=404, detail="Language file not found.")
    try:
        with open(LANGUAGE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read language file: {e}")

# --- NEW: Settings API ---
@app.post("/api/save-settings")
async def save_settings(request: SettingsRequest):
    """Saves settings like the last used image directory."""
    try:
        settings = {}
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        
        # Update settings with new data from the request
        settings.update(request.dict(exclude_unset=True))

        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)
        return {"status": "success", "settings": settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save settings file: {e}")

@app.get("/api/get-settings")
async def get_settings():
    """Gets saved settings. Returns empty if not set."""
    if not os.path.exists(SETTINGS_FILE):
        return JSONResponse(content={}) # 파일이 없으면 빈 객체 반환
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read settings file: {e}")

# --- Image Processing API ---
@app.post("/api/list-images")
async def list_images(request: ImageListRequest):
    folder_path = request.folder_path
    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=404, detail="Folder not found. Please check the path.")
    
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    images = []
    try:
        for filename in sorted(os.listdir(folder_path)):
            if os.path.splitext(filename)[1].lower() in allowed_extensions:
                images.append(filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading files: {e}")
        
    return {"images": images}

@app.get("/api/get-image")
async def get_image(folder_path: str, image_name: str):
    image_path = os.path.join(folder_path, image_name)
    if not os.path.isfile(image_path):
        raise HTTPException(status_code=404, detail="Image not found.")
    return FileResponse(image_path)

@app.post("/api/crop-and-save")
async def crop_and_save(request: CropRequest):
    try:
        original_path = os.path.join(request.folder_path, request.image_name)
        resized_folder = os.path.join(request.folder_path, "resized")
        os.makedirs(resized_folder, exist_ok=True)

        img = Image.open(original_path).convert("RGBA")
        
        x1 = int(request.coords['x'])
        y1 = int(request.coords['y'])
        x2 = int(x1 + request.coords['width'])
        y2 = int(y1 + request.coords['height'])
        
        cropped_img = img.crop((x1, y1, x2, y2))
        
        if request.resize and request.target_width and request.target_height:
            cropped_img = cropped_img.resize((request.target_width, request.target_height), Image.Resampling.LANCZOS)

        base_name, _ = os.path.splitext(request.image_name)
        save_path_png = os.path.join(resized_folder, f"{base_name}.png")
        counter = 1
        while os.path.exists(save_path_png):
            save_path_png = os.path.join(resized_folder, f"{base_name}-{counter:02d}.png")
            counter += 1
            
        cropped_img.save(save_path_png, 'PNG')

        saved_text = False
        if request.description and request.description.strip():
            txt_path = os.path.splitext(save_path_png)[0] + ".txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(request.description)
            saved_text = True

        return {"status": "success", "path": save_path_png, "saved_text": saved_text}

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Original image not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during image processing: {e}")

# --- Static Files Mount ---
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/locales", StaticFiles(directory="locales"), name="locales")

# --- Server Startup Functions ---
def find_free_port(start_port=8000, max_port=8010):
    """Find an available port starting from start_port"""
    for port in range(start_port, max_port + 1):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            if sock.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return None

def open_browser(port):
    """Open web browser after a short delay"""
    def delayed_open():
        time.sleep(3)  # Wait for server to fully start
        try:
            webbrowser.open(f'http://127.0.0.1:{port}')
            print(f"Browser opened: http://127.0.0.1:{port}")
        except Exception as e:
            print(f"Could not open browser automatically: {e}")
            print(f"Please open http://127.0.0.1:{port} manually")
    
    threading.Thread(target=delayed_open, daemon=True).start()

# --- Main Server Start ---
if __name__ == "__main__":
    print("Starting ImageCrop Server...")
    
    # Find available port
    port = find_free_port()
    if port is None:
        print("Error: No available ports found between 8000-8010")
        print("Please close other applications using these ports")
        exit(1)
    
    print(f"Found available port: {port}")
    print(f"Server will be available at http://127.0.0.1:{port}")
    
    # Start browser opening in background
    open_browser(port)
    
    # Start the server
    try:
        uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)
    except Exception as e:
        print(f"Error starting server: {e}")
        exit(1)