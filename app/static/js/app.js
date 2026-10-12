/**
 * Main Application Frontend Logic
 * Camera capture, image upload, FastAPI prediction call, dynamic rendering, and language switching
 */

let currentLanguage = "mr";
let selectedCrop = "Pomegranate";
let selectedFile = null;
let lastAudioUrl = null;
let lastSpokenText = "";
let cameraStream = null;
let currentFacingMode = "environment";

// UI Text Dictionary for Seamless Multilingual Switching
const UI_STRINGS = {
    app_title: { mr: "कृषी डॉक्टर", hi: "कृषि डॉक्टर", en: "Crop Doctor" },
    app_subtitle: { mr: "पिकांवरील रोग निदान व उपचार", hi: "फसल रोग पहचान और उपचार", en: "Smart Disease Detection" },
    select_crop: { mr: "पीक निवडा:", hi: "फसल चुनें:", en: "Select Crop:" },
    crop_pom: { mr: "डाळिंब", hi: "अनार", en: "Pomegranate" },
    crop_onion: { mr: "कांदा", hi: "प्याज", en: "Onion" },
    crop_tomato: { mr: "टोमॅटो", hi: "टमाटर", en: "Tomato" },
    upload_heading: { mr: "पानाचा फोटो काढा किंवा अपलोड करा", hi: "पत्ती का फोटो लें या अपलोड करें", en: "Take Leaf Photo or Upload" },
    upload_sub: { mr: "चांगल्या प्रकाशात पानाचा स्पष्ट फोटो निवडा", hi: "अच्छी रोशनी में पत्ती की तस्वीर चुनें", en: "Clear close-up photo in good lighting" },
    btn_gallery: { mr: "गॅलरी", hi: "गैलरी", en: "Gallery" },
    btn_camera: { mr: "कॅमेरा", hi: "कैमरा", en: "Camera" },
    btn_change: { mr: "फोटो बदला", hi: "फोटो बदलें", en: "Change Photo" },
    btn_analyze: { mr: "रोग तपासा", hi: "रोग की जांच करें", en: "Diagnose Leaf" },
    analyzing: { mr: "तपासत आहे...", hi: "जांच जारी है...", en: "Diagnosing..." },
    confidence_label: { mr: "विश्वासार्हता:", hi: "सटीकता:", en: "Confidence:" },
    tab_organic: { mr: "सेंद्रिय उपाय", hi: "जैविक उपचार", en: "Organic Option" },
    tab_chemical: { mr: "रासायनिक उपाय", hi: "रासायनिक उपचार", en: "Chemical Option" },
    tab_preventive: { mr: "प्रतिबंधात्मक काळजी", hi: "निवारक उपाय", en: "Prevention" },
    nav_home: { mr: "होम", hi: "होम", en: "Home" },
    nav_history: { mr: "इतिहास", hi: "इतिहास", en: "History" },
    nav_admin: { mr: "अॅडमिन", hi: "एडमिन", en: "Admin" },
    camera_title: { mr: "थेट कॅमेरा", hi: "लाइव कैमरा", en: "Live Camera" },
    camera_guide: { mr: "पानावर कॅमेरा स्थिर ठेवा", hi: "पत्ती पर कैमरा स्थिर रखें", en: "Align leaf inside frame" },
    camera_error: { 
        mr: "कॅमेरा सुरू करता आला नाही. कृपया कॅमेरा परवानगी द्या किंवा गॅलरी वापरा.", 
        hi: "कैमरा शुरू नहीं हो सका। कृपया अनुमति दें या गैलरी का उपयोग करें।", 
        en: "Unable to access camera. Please allow camera permission or use gallery." 
    }
};

document.addEventListener("DOMContentLoaded", () => {
    // Initialize Voice Assistant
    VoiceAssistant.init(currentLanguage);

    // Setup File & Camera Listeners
    const fileInput = document.getElementById("fileInput");
    const cameraInput = document.getElementById("cameraInput");
    const startCameraBtn = document.getElementById("startCameraBtn");
    const closeCameraBtn = document.getElementById("closeCameraBtn");
    const switchCameraBtn = document.getElementById("switchCameraBtn");
    const capturePhotoBtn = document.getElementById("capturePhotoBtn");
    const cameraModal = document.getElementById("cameraModal");
    const uploadArea = document.getElementById("uploadArea");
    const analyzeBtn = document.getElementById("analyzeBtn");

    if (fileInput) {
        fileInput.addEventListener("change", (e) => handleFileSelected(e.target.files[0]));
    }
    if (cameraInput) {
        cameraInput.addEventListener("change", (e) => handleFileSelected(e.target.files[0]));
    }

    // Real Live Camera Controls
    if (startCameraBtn) {
        startCameraBtn.addEventListener("click", startCamera);
    }
    if (closeCameraBtn) {
        closeCameraBtn.addEventListener("click", closeCamera);
    }
    if (switchCameraBtn) {
        switchCameraBtn.addEventListener("click", switchCamera);
    }
    if (capturePhotoBtn) {
        capturePhotoBtn.addEventListener("click", capturePhoto);
    }

    // Close camera on Escape key or background click
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && cameraModal && cameraModal.style.display !== "none") {
            closeCamera();
        }
    });

    if (cameraModal) {
        cameraModal.addEventListener("click", (e) => {
            if (e.target === cameraModal) {
                closeCamera();
            }
        });
    }

    // Drag & Drop
    if (uploadArea) {
        uploadArea.addEventListener("dragover", (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = "#15803d";
        });
        uploadArea.addEventListener("dragleave", () => {
            uploadArea.style.borderColor = "#86efac";
        });
        uploadArea.addEventListener("drop", (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = "#86efac";
            if (e.dataTransfer.files.length > 0) {
                handleFileSelected(e.dataTransfer.files[0]);
            }
        });
    }

    if (analyzeBtn) {
        analyzeBtn.addEventListener("click", performPrediction);
    }

    // Load Initial Language
    setAppLanguage("mr");
});

/* Live Camera Functions */
async function startCamera() {
    const cameraModal = document.getElementById("cameraModal");

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.warn("getUserMedia not supported, falling back to camera input");
        const cameraInput = document.getElementById("cameraInput");
        if (cameraInput) cameraInput.click();
        return;
    }

    try {
        cameraModal.style.display = "flex";
        await initCameraStream(currentFacingMode);

        // Check if multiple camera devices exist
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(d => d.kind === "videoinput");
            const switchBtn = document.getElementById("switchCameraBtn");
            if (switchBtn) {
                switchBtn.style.display = videoDevices.length > 1 ? "inline-flex" : "none";
            }
        } catch (enumErr) {
            console.log("Device enumeration not supported:", enumErr);
        }

    } catch (err) {
        console.error("Camera access error:", err);
        closeCamera();
        const errMsg = (UI_STRINGS["camera_error"] && UI_STRINGS["camera_error"][currentLanguage]) || 
                       "Camera could not be started. Opening file picker.";
        alert(errMsg);
        const cameraInput = document.getElementById("cameraInput");
        if (cameraInput) cameraInput.click();
    }
}

async function initCameraStream(facingMode) {
    stopCameraStream();

    const constraints = {
        video: {
            facingMode: facingMode ? { ideal: facingMode } : "environment",
            width: { ideal: 1280 },
            height: { ideal: 720 }
        },
        audio: false
    };

    cameraStream = await navigator.mediaDevices.getUserMedia(constraints);
    const video = document.getElementById("cameraVideo");
    if (video) {
        video.srcObject = cameraStream;
        await video.play();
    }
}

function stopCameraStream() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    const video = document.getElementById("cameraVideo");
    if (video) {
        video.srcObject = null;
    }
}

function closeCamera() {
    stopCameraStream();
    const cameraModal = document.getElementById("cameraModal");
    if (cameraModal) {
        cameraModal.style.display = "none";
    }
}

function switchCamera() {
    currentFacingMode = currentFacingMode === "environment" ? "user" : "environment";
    initCameraStream(currentFacingMode).catch(err => {
        console.warn("Could not switch camera:", err);
    });
}

function capturePhoto() {
    const video = document.getElementById("cameraVideo");
    if (!video || !cameraStream) return;

    // Shutter flash animation effect
    const viewport = document.querySelector(".camera-viewport");
    if (viewport) {
        viewport.style.filter = "brightness(2.2)";
        setTimeout(() => {
            if (viewport) viewport.style.filter = "none";
        }, 120);
    }

    const width = video.videoWidth || 640;
    const height = video.videoHeight || 480;

    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");

    if (currentFacingMode === "user") {
        ctx.translate(width, 0);
        ctx.scale(-1, 1);
    }
    ctx.drawImage(video, 0, 0, width, height);

    canvas.toBlob((blob) => {
        if (!blob) {
            alert("Failed to capture image.");
            return;
        }

        const capturedFile = new File([blob], `leaf_photo_${Date.now()}.jpg`, { type: "image/jpeg" });
        closeCamera();
        handleFileSelected(capturedFile);
    }, "image/jpeg", 0.95);
}

function handleFileSelected(file) {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
        alert("Please select an image file (JPG, PNG).");
        return;
    }

    selectedFile = file;

    // Show Preview
    const previewContainer = document.getElementById("previewContainer");
    const previewImg = document.getElementById("previewImg");
    const uploadArea = document.getElementById("uploadArea");
    const analyzeBtn = document.getElementById("analyzeBtn");

    const reader = new FileReader();
    reader.onload = (e) => {
        previewImg.src = e.target.result;
        previewContainer.style.display = "block";
        uploadArea.style.display = "none";
        analyzeBtn.disabled = false;

        // Hide previous results
        document.getElementById("resultContainer").style.display = "none";
    };
    reader.readAsDataURL(file);
}

function resetUpload() {
    stopCameraStream();
    selectedFile = null;
    document.getElementById("fileInput").value = "";
    document.getElementById("cameraInput").value = "";
    document.getElementById("previewContainer").style.display = "none";
    document.getElementById("uploadArea").style.display = "block";
    document.getElementById("analyzeBtn").disabled = true;
    document.getElementById("resultContainer").style.display = "none";
}

function selectCrop(cropName) {
    selectedCrop = cropName;
    document.querySelectorAll(".crop-chip").forEach(chip => {
        if (chip.dataset.crop === cropName) {
            chip.classList.add("active");
        } else {
            chip.classList.remove("active");
        }
    });
}

function setAppLanguage(lang) {
    currentLanguage = lang;
    VoiceAssistant.init(lang);

    // Update active state on language buttons
    document.querySelectorAll(".lang-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.lang === lang);
    });

    // Update static UI text
    document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.dataset.i18n;
        if (UI_STRINGS[key] && UI_STRINGS[key][lang]) {
            el.textContent = UI_STRINGS[key][lang];
        }
    });

    // If results are already showing, re-fetch treatment in new language
    const lastClassEl = document.getElementById("detectedClassRaw");
    if (lastClassEl && lastClassEl.value && selectedFile) {
        performPrediction();
    }
}

async function performPrediction() {
    if (!selectedFile) return;

    const analyzeBtn = document.getElementById("analyzeBtn");
    const btnText = document.getElementById("btnText");
    const spinner = document.getElementById("spinner");
    const resultContainer = document.getElementById("resultContainer");

    // UI Loading state
    analyzeBtn.disabled = true;
    spinner.style.display = "inline-block";
    btnText.textContent = UI_STRINGS["analyzing"][currentLanguage];

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("lang", currentLanguage);

    try {
        const response = await fetch("/api/predict", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Server error");
        }

        renderPredictionResults(data);

    } catch (err) {
        console.error("Prediction error:", err);
        alert("Error analyzing image: " + err.message);
    } finally {
        analyzeBtn.disabled = false;
        spinner.style.display = "none";
        btnText.textContent = UI_STRINGS["btn_analyze"][currentLanguage];
    }
}

function renderPredictionResults(data) {
    const resultContainer = document.getElementById("resultContainer");
    resultContainer.style.display = "block";
    resultContainer.scrollIntoView({ behavior: "smooth", block: "start" });

    const resultContent = document.getElementById("resultContent");

    // Case 1: Non-Leaf Image Rejected (Feature 1)
    if (!data.leaf_check_passed) {
        resultContent.innerHTML = `
            <div class="warning-box" style="border-color: #fca5a5; background: #fef2f2;">
                <span class="icon">🚫</span>
                <div>
                    <h4 style="color: #991b1b;">अवैध फोटो / Non-Leaf Image</h4>
                    <p style="color: #b91c1c;">${data.message}</p>
                </div>
            </div>
        `;
        return;
    }

    // Case 2: Low-Confidence (<70%) Handling (Feature 3)
    if (data.is_low_confidence) {
        let topSuggestions = data.top_predictions.map(p => `
            <div style="display:flex; justify-content:space-between; font-size:13px; padding:6px 0; border-bottom:1px dashed #e2e8f0;">
                <span>${p.common_name}</span>
                <span style="font-weight:700;">${p.confidence_percentage}</span>
            </div>
        `).join("");

        resultContent.innerHTML = `
            <div class="warning-box">
                <span class="icon">⚠️</span>
                <div>
                    <h4>अचूकता कमी आहे (कमी विश्वासार्हता)</h4>
                    <p>${data.message}</p>
                </div>
            </div>
            <div class="result-card">
                <h4 style="font-size:14px; margin-bottom:8px; color:var(--text-muted);">शक्यता (Top Predictions):</h4>
                ${topSuggestions}
            </div>
        `;
        return;
    }

    // Case 3: High-Confidence Accurate Detection
    const top = data.top_predictions[0];
    const treatment = data.treatment;
    lastAudioUrl = data.audio_url;

    document.getElementById("detectedClassRaw").value = top.class_name;

    let treatmentHtml = "";
    if (treatment) {
        treatmentHtml = `
            <div class="treatment-tabs">
                <button class="tab-btn active" onclick="switchTreatmentTab('organic')">${UI_STRINGS['tab_organic'][currentLanguage]}</button>
                <button class="tab-btn" onclick="switchTreatmentTab('chemical')">${UI_STRINGS['tab_chemical'][currentLanguage]}</button>
                <button class="tab-btn" onclick="switchTreatmentTab('preventive')">${UI_STRINGS['tab_preventive'][currentLanguage]}</button>
            </div>
            
            <div id="tab-organic" class="tab-panel active">
                <strong>🌱 सेंद्रिय पर्याय:</strong><br>${treatment.organic}
            </div>
            <div id="tab-chemical" class="tab-panel">
                <strong>🧪 रासायनिक उपाय व प्रमाण:</strong><br>${treatment.chemical}
            </div>
            <div id="tab-preventive" class="tab-panel">
                <strong>🛡️ प्रतिबंधात्मक व्यवस्थापन:</strong><br>${treatment.preventive}
            </div>

            <div class="officer-note-box">
                ⚠️ <strong>महत्त्वाची सूचना:</strong> ${treatment.officer_note}
            </div>
        `;
    }

    resultContent.innerHTML = `
        <div class="result-card">
            <div class="result-header">
                <div class="disease-title">
                    <span class="crop-name">${top.crop_name}</span>
                    <h2>${top.common_name}</h2>
                </div>
                <button class="audio-play-btn" onclick="playCurrentAudio()" title="आवाज ऐका (Listen)">
                    🔊
                </button>
            </div>

            <div class="confidence-box">
                <div class="confidence-label">
                    <span>${UI_STRINGS['confidence_label'][currentLanguage]}</span>
                    <span>${top.confidence_percentage}</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: ${top.confidence_percentage}"></div>
                </div>
            </div>

            ${treatmentHtml}
        </div>
    `;

    // Auto-play audio or announce completion
    if (lastAudioUrl) {
        VoiceAssistant.playAudio(lastAudioUrl);
    }
}

function switchTreatmentTab(tabName) {
    document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(panel => panel.classList.remove("active"));

    const activePanel = document.getElementById(`tab-${tabName}`);
    if (activePanel) activePanel.classList.add("active");

    // Highlight button
    event.target.classList.add("active");
}

function playCurrentAudio() {
    if (lastAudioUrl) {
        VoiceAssistant.playAudio(lastAudioUrl);
    } else {
        alert("Audio explanation is being generated.");
    }
}
