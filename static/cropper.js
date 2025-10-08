document.addEventListener('DOMContentLoaded', async () => {
    // --- State & Translations ---
    let translations = {};

    // --- DOM Elements ---
    const getEl = (id) => document.getElementById(id);
    const imageFolderPathInput = getEl('image-folder-path');
    const loadButton = getEl('load-button');
    const sizePresetSelect = getEl('size-preset');
    const targetWidthInput = getEl('target-width');
    const targetHeightInput = getEl('target-height');
    const aspectRatioDisplay = getEl('aspect-ratio-display');
    const mainImageViewer = getEl('main-image-viewer');
    const thumbnailList = getEl('thumbnail-list');
    const imageDescriptionTextarea = getEl('image-description');
    const saveButton = getEl('save-button');
    const cropAndResizeButton = getEl('crop-and-resize-button');
    const languageSelectorDropdown = getEl('language-selector-dropdown');
    const originalSizeDisplay = getEl('original-size-display');

    // --- State Variables ---
    let currentFolder = '';
    let imageFiles = [];
    let activeImage = null;
    let cropBox = null;
    let cropperState = {};
    let mainImageElement = null;
    let cropWidthDisplay, cropHeightDisplay;
    const CROP_BOX_BORDER_WIDTH = 2; // Define border width as a constant

    // --- I18n & Settings ---
    const applyTranslations = (data) => {
        translations = data;
        document.querySelectorAll('[data-i18n-key]').forEach(el => {
            const key = el.getAttribute('data-i18n-key');
            if (translations[key]) {
                if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                    if (el.type !== 'button') el.placeholder = translations[key];
                } else {
                    el.textContent = translations[key];
                }
            }
        });
        // Handle placeholder translations
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (translations[key]) {
                el.placeholder = translations[key];
            }
        });
        document.title = translations['headerTitle'] || 'Image Resizer';
    };

    const loadLanguage = async () => {
        try {
            const response = await fetch('/api/get-language');
            if (!response.ok) { window.location.href = '/'; return; }
            const data = await response.json();
            const lang = data.language || 'en';
            const langResponse = await fetch(`/locales/${lang}.json`);
            const langData = await langResponse.json();
            applyTranslations(langData);
            languageSelectorDropdown.value = lang;
        } catch (error) { console.error("Failed to load language settings, redirecting.", error); window.location.href = '/'; }
    };

    const loadInitialSettings = async () => {
        try {
            const response = await fetch('/api/get-settings');
            if (response.ok) {
                const settings = await response.json();
                if (settings.last_image_dir) {
                    imageFolderPathInput.value = settings.last_image_dir;
                }
            }
        } catch (error) { console.error("Failed to load initial settings:", error); }
    };

    // --- Utility Functions ---
    const gcd = (a, b) => b === 0 ? a : gcd(b, a % b);

    const updateAspectRatio = () => {
        const width = parseInt(targetWidthInput.value, 10);
        const height = parseInt(targetHeightInput.value, 10);
        if (isNaN(width) || isNaN(height) || width <= 0 || height <= 0) {
            aspectRatioDisplay.textContent = 'N/A';
            return;
        }
        const commonDivisor = gcd(width, height);
        aspectRatioDisplay.textContent = `${width / commonDivisor}:${height / commonDivisor}`;
        if (mainImageElement) { resetCropBox(); }
    };

    const handleApiError = (error) => {
        console.error('API Error:', error);
        alert(`Error: ${error.detail || 'Could not connect to the server.'}`);
    };

    // --- Core Functions ---
    const loadImages = async () => {
        currentFolder = imageFolderPathInput.value.trim();
        if (!currentFolder) { alert(translations['alert_folder_required'] || 'Image folder path is required.'); return; }
        try {
            const response = await fetch('/api/list-images', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ folder_path: currentFolder }), });
            if (!response.ok) throw await response.json();
            await fetch('/api/save-settings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ last_image_dir: currentFolder }) });
            const data = await response.json();
            imageFiles = data.images;
            if (imageFiles.length === 0) {
                thumbnailList.innerHTML = `<p>${translations['noImagesFound'] || 'No images found.'}</p>`;
                mainImageViewer.innerHTML = `<p>${translations['viewerPlaceholder']}</p>`;
                saveButton.disabled = true; cropAndResizeButton.disabled = true;
                return;
            }
            displayThumbnails();
            if (imageFiles[0]) { selectImage(imageFiles[0]); }
        } catch (error) { handleApiError(error); }
    };

    const displayThumbnails = () => {
        thumbnailList.innerHTML = '';
        imageFiles.forEach(fileName => {
            const thumbDiv = document.createElement('div');
            thumbDiv.className = 'thumbnail';
            thumbDiv.dataset.imageName = fileName;
            const img = document.createElement('img');
            img.src = `/api/get-image?folder_path=${encodeURIComponent(currentFolder)}&image_name=${encodeURIComponent(fileName)}`;
            thumbDiv.appendChild(img);
            thumbDiv.addEventListener('click', () => selectImage(fileName));
            thumbnailList.appendChild(thumbDiv);
        });
    };

    const selectImage = (fileName) => {
        activeImage = fileName;
        document.querySelectorAll('.thumbnail').forEach(thumb => { thumb.classList.toggle('active', thumb.dataset.imageName === fileName); });
        mainImageViewer.innerHTML = '';
        imageDescriptionTextarea.value = '';
        originalSizeDisplay.textContent = '...';
        saveButton.disabled = true; cropAndResizeButton.disabled = true;
        mainImageElement = document.createElement('img');
        mainImageElement.src = `/api/get-image?folder_path=${encodeURIComponent(currentFolder)}&image_name=${encodeURIComponent(fileName)}`;
        mainImageElement.onload = () => {
            originalSizeDisplay.textContent = `${mainImageElement.naturalWidth} x ${mainImageElement.naturalHeight}`;
            saveButton.disabled = false; cropAndResizeButton.disabled = false;
            initCropper();
        };
        mainImageElement.onerror = () => {
            mainImageViewer.innerHTML = `<p>${translations['imageLoadError'] || 'Could not load image.'}</p>`;
            originalSizeDisplay.textContent = 'N/A';
        };
        mainImageViewer.appendChild(mainImageElement);
    };

    const saveImage = async (resizeAfterCrop) => {
        if (!activeImage || !cropBox) { alert(translations['alert_no_selection'] || 'No image or crop area selected.'); return; }
        const scale = mainImageElement.naturalWidth / mainImageElement.clientWidth;
        const imageOffsetX = mainImageElement.offsetLeft;
        const imageOffsetY = mainImageElement.offsetTop;
        const cropCoords = {
            x: Math.round((cropBox.offsetLeft - imageOffsetX + CROP_BOX_BORDER_WIDTH) * scale),
            y: Math.round((cropBox.offsetTop - imageOffsetY + CROP_BOX_BORDER_WIDTH) * scale),
            width: Math.round(cropBox.clientWidth * scale),
            height: Math.round(cropBox.clientHeight * scale),
        };
        try {
            const body = {
                folder_path: currentFolder, image_name: activeImage, coords: cropCoords,
                description: imageDescriptionTextarea.value.trim(), resize: resizeAfterCrop,
                target_width: resizeAfterCrop ? parseInt(targetWidthInput.value, 10) : null,
                target_height: resizeAfterCrop ? parseInt(targetHeightInput.value, 10) : null,
            };
            const response = await fetch('/api/crop-and-save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), });
            if (!response.ok) throw await response.json();
            const result = await response.json();
            markAsEdited(activeImage, result.saved_text);
        } catch (error) { handleApiError(error); }
    };

    const markAsEdited = (fileName, hasText) => {
        const thumbnail = document.querySelector(`.thumbnail[data-image-name="${fileName}"]`);
        if (!thumbnail) return;
        let indicator = thumbnail.querySelector('.edited-indicator');
        if (!indicator) { indicator = document.createElement('div'); indicator.className = 'edited-indicator'; thumbnail.appendChild(indicator); }
        indicator.textContent = hasText ? (translations['editedWithText'] || 'Text') : (translations['edited'] || 'Edited');
        indicator.classList.toggle('with-text', hasText);
    };

    // --- Cropper Logic ---
    const updateCropDimensions = () => {
        if (!cropBox || !mainImageElement) return;
        const scale = mainImageElement.naturalWidth / mainImageElement.clientWidth;
        const realWidth = Math.round(cropBox.clientWidth * scale);
        const realHeight = Math.round(cropBox.clientHeight * scale);
        cropWidthDisplay.textContent = `${realWidth}px`;
        cropHeightDisplay.textContent = `${realHeight}px`;
    };

    const updateDimensionDisplayPosition = () => {
        if (!cropBox || !cropWidthDisplay || !cropHeightDisplay) return;
        if (cropBox.offsetTop < 30) { cropWidthDisplay.classList.add('inside'); }
        else { cropWidthDisplay.classList.remove('inside'); }
        if (cropBox.offsetLeft < 40) { cropHeightDisplay.classList.add('inside'); }
        else { cropHeightDisplay.classList.remove('inside'); }
    };

    const initCropper = () => {
        if (cropBox && cropBox.parentElement) { cropBox.parentElement.removeChild(cropBox); }
        cropBox = document.createElement('div');
        cropBox.className = 'crop-box';
        const handles = ['tl', 'tr', 'bl', 'br'];
        handles.forEach(handleType => {
            const handle = document.createElement('div');
            handle.className = `crop-handle ${handleType}`;
            handle.dataset.handle = handleType;
            handle.addEventListener('mousedown', startResize);
            cropBox.appendChild(handle);
        });
        cropWidthDisplay = document.createElement('div');
        cropWidthDisplay.className = 'crop-dimension-display width-display';
        cropBox.appendChild(cropWidthDisplay);
        cropHeightDisplay = document.createElement('div');
        cropHeightDisplay.className = 'crop-dimension-display height-display';
        cropBox.appendChild(cropHeightDisplay);
        mainImageViewer.appendChild(cropBox);
        resetCropBox();
        cropBox.addEventListener('mousedown', startDrag);
    };

    const resetCropBox = () => {
        if (!mainImageElement || !cropBox) return;
        const imgWidth = mainImageElement.clientWidth;
        const imgHeight = mainImageElement.clientHeight;
        const imageOffsetX = mainImageElement.offsetLeft;
        const imageOffsetY = mainImageElement.offsetTop;
        const targetW = parseInt(targetWidthInput.value, 10);
        const targetH = parseInt(targetHeightInput.value, 10);
        if (isNaN(targetW) || isNaN(targetH) || targetW <= 0 || targetH <= 0) return;
        const aspectRatio = targetW / targetH;
        let boxContentWidth, boxContentHeight;
        if (imgWidth / imgHeight > aspectRatio) { boxContentHeight = imgHeight * 0.9; boxContentWidth = boxContentHeight * aspectRatio; }
        else { boxContentWidth = imgWidth * 0.9; boxContentHeight = boxContentWidth / aspectRatio; }

        cropBox.style.width = `${boxContentWidth + (CROP_BOX_BORDER_WIDTH * 2)}px`;
        cropBox.style.height = `${boxContentHeight + (CROP_BOX_BORDER_WIDTH * 2)}px`;
        cropBox.style.left = `${imageOffsetX + (imgWidth - boxContentWidth) / 2 - CROP_BOX_BORDER_WIDTH}px`;
        cropBox.style.top = `${imageOffsetY + (imgHeight - boxContentHeight) / 2 - CROP_BOX_BORDER_WIDTH}px`;

        updateCropDimensions();
        updateDimensionDisplayPosition();
    };

    // --- MODIFIED CODE START (drag, resize, startResize have been fixed) ---

    function drag(e) {
        if (!cropperState.isDragging) return;
        const imageOffsetX = mainImageElement.offsetLeft;
        const imageOffsetY = mainImageElement.offsetTop;
        const imageW = mainImageElement.clientWidth;
        const imageH = mainImageElement.clientHeight;
        const boxW = cropBox.clientWidth;
        const boxH = cropBox.clientHeight;

        const dx = e.clientX - cropperState.startX;
        const dy = e.clientY - cropperState.startY;
        let newLeft = cropperState.initialLeft + dx;
        let newTop = cropperState.initialTop + dy;

        // Clamp position so the content area stays within the image's content area
        const minLeft = imageOffsetX - CROP_BOX_BORDER_WIDTH;
        const minTop = imageOffsetY - CROP_BOX_BORDER_WIDTH;
        const maxLeft = imageOffsetX + imageW - boxW - CROP_BOX_BORDER_WIDTH;
        const maxTop = imageOffsetY + imageH - boxH - CROP_BOX_BORDER_WIDTH;

        newLeft = Math.max(minLeft, Math.min(newLeft, maxLeft));
        newTop = Math.max(minTop, Math.min(newTop, maxTop));

        cropBox.style.left = `${newLeft}px`;
        cropBox.style.top = `${newTop}px`;
        updateDimensionDisplayPosition();
    }

    function resize(e) {
        if (!cropperState.isResizing) return;

        const imageRect = mainImageElement.getBoundingClientRect();
        const imageWidth = mainImageElement.clientWidth;
        const imageHeight = mainImageElement.clientHeight;
        const imageOffsetX = mainImageElement.offsetLeft;
        const imageOffsetY = mainImageElement.offsetTop;

        const aspectRatio = cropperState.aspectRatio;
        const anchorX = cropperState.anchor.x; // Inner anchor X
        const anchorY = cropperState.anchor.y; // Inner anchor Y
        const handle = cropperState.activeHandle;

        const mouseX = Math.max(0, Math.min(e.clientX - imageRect.left, imageWidth));
        const mouseY = Math.max(0, Math.min(e.clientY - imageRect.top, imageHeight));

        let maxWidth, maxHeight; // Max content width/height
        if (handle.includes('l')) { maxWidth = anchorX; } else { maxWidth = imageWidth - anchorX; }
        if (handle.includes('t')) { maxHeight = anchorY; } else { maxHeight = imageHeight - anchorY; }

        let newContentWidth, newContentHeight;
        if (maxWidth / aspectRatio > maxHeight) { newContentHeight = maxHeight; newContentWidth = newContentHeight * aspectRatio; }
        else { newContentWidth = maxWidth; newContentHeight = newContentWidth / aspectRatio; }

        const desiredWidth = Math.abs(mouseX - anchorX);
        if (desiredWidth < newContentWidth) {
            newContentWidth = desiredWidth;
            newContentHeight = newContentWidth / aspectRatio;
        }

        let newLeft, newTop; // Outer position
        if (handle.includes('l')) { newLeft = imageOffsetX + anchorX - newContentWidth - CROP_BOX_BORDER_WIDTH; }
        else { newLeft = imageOffsetX + anchorX - CROP_BOX_BORDER_WIDTH; }
        if (handle.includes('t')) { newTop = imageOffsetY + anchorY - newContentHeight - CROP_BOX_BORDER_WIDTH; }
        else { newTop = imageOffsetY + anchorY - CROP_BOX_BORDER_WIDTH; }

        if (newContentWidth < 20 || newContentHeight < 20) return;

        cropBox.style.width = `${Math.round(newContentWidth + CROP_BOX_BORDER_WIDTH * 2)}px`;
        cropBox.style.height = `${Math.round(newContentHeight + CROP_BOX_BORDER_WIDTH * 2)}px`;
        cropBox.style.left = `${Math.round(newLeft)}px`;
        cropBox.style.top = `${Math.round(newTop)}px`;

        updateCropDimensions();
        updateDimensionDisplayPosition();
    }

    function startResize(e) {
        e.preventDefault();
        e.stopPropagation();
        cropperState.isResizing = true;
        cropperState.activeHandle = e.target.dataset.handle;

        const imageOffsetX = mainImageElement.offsetLeft;
        const imageOffsetY = mainImageElement.offsetTop;

        // Calculate positions of the CONTENT box relative to the image's content area
        const left = (cropBox.offsetLeft - imageOffsetX) + CROP_BOX_BORDER_WIDTH;
        const top = (cropBox.offsetTop - imageOffsetY) + CROP_BOX_BORDER_WIDTH;
        const width = cropBox.clientWidth;
        const height = cropBox.clientHeight;

        const right = left + width;
        const bottom = top + height;

        // Anchor points are now the inner corners
        switch (cropperState.activeHandle) {
            case 'br': cropperState.anchor = { x: left, y: top }; break;
            case 'bl': cropperState.anchor = { x: right, y: top }; break;
            case 'tr': cropperState.anchor = { x: left, y: bottom }; break;
            case 'tl': cropperState.anchor = { x: right, y: bottom }; break;
        }

        const targetW = parseInt(targetWidthInput.value, 10);
        const targetH = parseInt(targetHeightInput.value, 10);
        if (!isNaN(targetW) && !isNaN(targetH) && targetH > 0) {
            cropperState.aspectRatio = targetW / targetH;
        } else {
            cropperState.aspectRatio = cropBox.clientWidth / cropBox.clientHeight;
        }

        document.addEventListener('mousemove', resize);
        document.addEventListener('mouseup', stopResize);
    }

    // --- MODIFIED CODE END ---

    function stopDrag() { cropperState.isDragging = false; document.removeEventListener('mousemove', drag); document.removeEventListener('mouseup', stopDrag); }
    function stopResize() { cropperState.isResizing = false; document.removeEventListener('mousemove', resize); document.removeEventListener('mouseup', stopResize); }
    function startDrag(e) { e.preventDefault(); e.stopPropagation(); cropperState.isDragging = true; cropperState.startX = e.clientX; cropperState.startY = e.clientY; cropperState.initialLeft = cropBox.offsetLeft; cropperState.initialTop = cropBox.offsetTop; document.addEventListener('mousemove', drag); document.addEventListener('mouseup', stopDrag); }

    // --- Event Listeners ---
    loadButton.addEventListener('click', loadImages);
    targetWidthInput.addEventListener('input', updateAspectRatio);
    targetHeightInput.addEventListener('input', updateAspectRatio);
    saveButton.addEventListener('click', () => saveImage(false));
    cropAndResizeButton.addEventListener('click', () => saveImage(true));
    sizePresetSelect.addEventListener('change', (e) => {
        const value = e.target.value;
        if (value === 'custom') { targetWidthInput.value = ''; targetHeightInput.value = ''; return; }
        const [width, height] = value.split('x');
        targetWidthInput.value = width;
        targetHeightInput.value = height;
        updateAspectRatio();
    });

    languageSelectorDropdown.addEventListener('change', async (e) => {
        const newLang = e.target.value;
        try {
            await fetch('/api/save-language', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ language: newLang }) });
            const langResponse = await fetch(`/locales/${newLang}.json`);
            const langData = await langResponse.json();
            applyTranslations(langData);
        } catch (error) { console.error(`Failed to update language to ${newLang}:`, error); }
    });

    // --- Initial Call ---
    await loadLanguage();
    await loadInitialSettings();
    updateAspectRatio();
});