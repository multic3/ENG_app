const BrowserSpeechProvider = {
    recognition: null,
    listening: false,

    isSupported() {
        return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
    },

    start(options = {}) {
        if (!this.isSupported()) {
            options.onError?.("Speech recognition is not supported in this browser.");
            return false;
        }
        const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new Recognition();
        this.recognition.lang = options.language || "en-US";
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.maxAlternatives = 1;
        this.recognition.onstart = () => {
            this.listening = true;
            options.onStart?.();
        };
        this.recognition.onresult = event => {
            let transcript = "";
            for (let index = event.resultIndex; index < event.results.length; index++) {
                transcript += event.results[index][0].transcript;
            }
            const lastResult = event.results[event.results.length - 1];
            options.onTranscript?.(transcript.trim(), lastResult?.isFinal ?? true);
        };
        this.recognition.onerror = event => {
            this.listening = false;
            options.onError?.(event.error || "Microphone error");
        };
        this.recognition.onend = () => {
            this.listening = false;
            options.onEnd?.();
        };
        try {
            this.recognition.start();
            return true;
        } catch (error) {
            options.onError?.(error.message || "Microphone could not start.");
            return false;
        }
    },

    stop() {
        if (this.recognition && this.listening) {
            this.recognition.stop();
        }
    }
};


const SpeechEngine = {
    providers: [BrowserSpeechProvider],
    activeProvider: null,

    getProvider() {
        return this.providers.find(provider => provider.isSupported()) || null;
    },

    isSupported() {
        return Boolean(this.getProvider());
    },

    start(settings, callbacks) {
        this.stop();
        this.activeProvider = this.getProvider();
        if (!this.activeProvider) {
            callbacks.onError?.("Speech recognition is unavailable.");
            return false;
        }
        return this.activeProvider.start({
            language: settings?.language || "en-US",
            ...callbacks
        });
    },

    stop() {
        this.activeProvider?.stop();
    },

    normalize(value) {
        return String(value || "")
            .toLowerCase()
            .replace(/[’‘]/g, "'")
            .replace(/[^a-z0-9'\s]/g, " ")
            .replace(/\s+/g, " ")
            .trim();
    },

    evaluate(transcript, exercise) {
        const normalized = this.normalize(transcript);
        const words = normalized.split(" ").filter(Boolean);
        const settings = exercise.speech_settings || {};
        const variants = [exercise.phrase, ...(exercise.accepted_answers || [])]
            .filter(Boolean)
            .map(value => this.normalize(value));
        const concepts = (settings.required_concepts || [])
            .map(value => this.normalize(value))
            .filter(Boolean);
        const missingConcepts = concepts.filter(concept => (
            concept.includes(" ")
                ? !normalized.includes(concept)
                : !words.includes(concept)
        ));
        const exactVariant = variants.includes(normalized);
        const enoughWords = words.length >= (settings.min_words || 1);
        const conceptMatch = concepts.length > 0 && missingConcepts.length === 0;
        const correct = enoughWords && (exactVariant || conceptMatch);
        return {
            correct,
            transcript: normalized,
            missing_concepts: missingConcepts,
            message: correct
                ? "Слова и смысл распознаны. Произношение система не оценивает."
                : missingConcepts.length
                    ? `Не хватает: ${missingConcepts.join(", ")}.`
                    : "Ответ слишком короткий или не совпал с допустимым вариантом.",
            pronunciation_assessed: false
        };
    }
};
