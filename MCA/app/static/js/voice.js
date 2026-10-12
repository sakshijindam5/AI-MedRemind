/**
 * Voice Input & Audio Synthesis Engine
 * 1. Web Speech API (SpeechRecognition) for Marathi, Hindi, and English voice commands
 * 2. Audio Player for listening to diagnosis and treatments
 */

const VoiceAssistant = {
    recognition: null,
    isListening: false,
    currentLang: "mr",

    init: function(lang = "mr") {
        this.currentLang = lang;
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.warn("Web Speech API not supported in this browser.");
            const micBtn = document.getElementById("micBtn");
            if (micBtn) {
                micBtn.style.opacity = "0.5";
                micBtn.title = "Voice recognition not supported in your browser";
            }
            return false;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.maxAlternatives = 1;

        // Language code map for speech recognition
        const speechLangMap = {
            "mr": "mr-IN", // Marathi
            "hi": "hi-IN", // Hindi
            "en": "en-IN"  // Indian English
        };

        this.recognition.lang = speechLangMap[lang] || "mr-IN";

        this.recognition.onstart = () => {
            this.isListening = true;
            this.updateUiListening(true);
        };

        this.recognition.onend = () => {
            this.isListening = false;
            this.updateUiListening(false);
        };

        this.recognition.onerror = (event) => {
            console.error("Speech recognition error:", event.error);
            this.isListening = false;
            this.updateUiListening(false);
            const statusEl = document.getElementById("voiceStatusText");
            if (statusEl) {
                statusEl.textContent = this.getText("voice_error");
            }
        };

        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript.toLowerCase().trim();
            console.log("Heard voice command:", transcript);
            this.processVoiceCommand(transcript);
        };

        return true;
    },

    toggleListening: function() {
        if (!this.recognition) {
            this.init(this.currentLang);
        }
        if (!this.recognition) {
            alert("Voice recognition is not supported in this browser. Please use Chrome on Mobile/PC.");
            return;
        }

        if (this.isListening) {
            this.recognition.stop();
        } else {
            try {
                this.recognition.start();
            } catch (e) {
                console.error("Failed to start speech recognition:", e);
            }
        }
    },

    updateUiListening: function(listening) {
        const micBtn = document.getElementById("micBtn");
        const statusEl = document.getElementById("voiceStatusText");
        if (micBtn) {
            if (listening) {
                micBtn.classList.add("listening");
                if (statusEl) statusEl.textContent = this.getText("listening");
            } else {
                micBtn.classList.remove("listening");
                if (statusEl) statusEl.textContent = this.getText("tap_mic");
            }
        }
    },

    processVoiceCommand: function(text) {
        const statusEl = document.getElementById("voiceStatusText");
        if (statusEl) {
            statusEl.textContent = `"${text}"`;
        }

        // 1. Language switching commands
        if (text.includes("मराठी") || text.includes("marathi")) {
            setAppLanguage("mr");
            return;
        }
        if (text.includes("हिंदी") || text.includes("hindi")) {
            setAppLanguage("hi");
            return;
        }
        if (text.includes("english") || text.includes("इंग्रजी")) {
            setAppLanguage("en");
            return;
        }

        // 2. Crop selection commands
        if (text.includes("डाळिंब") || text.includes("dalimb") || text.includes("pomegranate") || text.includes("अनार")) {
            selectCrop("Pomegranate");
            return;
        }
        if (text.includes("कांदा") || text.includes("kanda") || text.includes("onion") || text.includes("प्याज")) {
            selectCrop("Onion");
            return;
        }
        if (text.includes("टोमॅटो") || text.includes("tomato") || text.includes("टमाटर")) {
            selectCrop("Tomato");
            return;
        }

        // 3. Scan command
        if (text.includes("स्कॅन") || text.includes("तपासा") || text.includes("scan") || text.includes("जांच")) {
            const analyzeBtn = document.getElementById("analyzeBtn");
            if (analyzeBtn && !analyzeBtn.disabled) {
                analyzeBtn.click();
            }
        }
    },

    playAudio: function(audioUrl, fallbackText) {
        if (audioUrl) {
            const audio = new Audio(audioUrl);
            audio.play().catch(e => {
                console.warn("Audio file playback blocked, trying SpeechSynthesis fallback:", e);
                this.speakBrowserText(fallbackText);
            });
        } else if (fallbackText) {
            this.speakBrowserText(fallbackText);
        }
    },

    speakBrowserText: function(text) {
        if (!window.speechSynthesis) return;
        window.speechSynthesis.cancel(); // Stop any ongoing speech

        const utterance = new SpeechSynthesisUtterance(text);
        const speechLangMap = { "mr": "mr-IN", "hi": "hi-IN", "en": "en-IN" };
        utterance.lang = speechLangMap[this.currentLang] || "mr-IN";
        utterance.rate = 0.9; // Slightly slower for clear rural understanding
        window.speechSynthesis.speak(utterance);
    },

    getText: function(key) {
        const msgs = {
            listening: {
                mr: "ऐकत आहे... बोला...",
                hi: "सुन रहा हूँ... बोलिए...",
                en: "Listening... speak now..."
            },
            tap_mic: {
                mr: "माइक दाबून बोला (उदा. 'डाळिंब', 'कांदा')",
                hi: "माइक दबाकर बोलें (उदा. 'अनार', 'प्याज')",
                en: "Tap mic to speak (e.g. 'Pomegranate', 'Onion')"
            },
            voice_error: {
                mr: "आवाज समजला नाही. पुन्हा प्रयत्न करा.",
                hi: "आवाज पहचान नहीं सके। दोबारा प्रयास करें।",
                en: "Could not recognize voice. Try again."
            }
        };
        return msgs[key]?.[this.currentLang] || msgs[key]?.["en"] || "";
    }
};
