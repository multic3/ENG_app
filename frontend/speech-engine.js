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
            .replace(/\bi'm\b/g, "i am")
            .replace(/\b(he|she|it)'s\b/g, "$1 is")
            .replace(/\b(is|are|was|were|have|has|do|does|did|can|could|will|would|should)n't\b/g, "$1 not")
            .replace(/\bi've\b/g, "i have")
            .replace(/\bwe've\b/g, "we have")
            .replace(/[^a-z0-9'\s]/g, " ")
            .replace(/\s+/g, " ")
            .trim();
    },

    phoneticToken(value) {
        return String(value || "")
            .replace(/ph/g, "f")
            .replace(/ck/g, "k")
            .replace(/qu/g, "kw")
            .replace(/ie$/g, "i")
            .replace(/y$/g, "i")
            .replace(/(.)\1+/g, "$1");
    },

    tokenSimilarity(left, right) {
        const a = this.phoneticToken(left);
        const b = this.phoneticToken(right);
        if (a === b) return 1;
        if (!a.length || !b.length) return 0;
        const previous = Array.from({ length: b.length + 1 }, (_, index) => index);
        for (let row = 1; row <= a.length; row++) {
            const current = [row];
            for (let column = 1; column <= b.length; column++) {
                current[column] = Math.min(
                    current[column - 1] + 1,
                    previous[column] + 1,
                    previous[column - 1] + (a[row - 1] === b[column - 1] ? 0 : 1)
                );
            }
            previous.splice(0, previous.length, ...current);
        }
        return Math.max(0, 1 - (previous[b.length] / Math.max(a.length, b.length)));
    },

    phraseScore(expected, actual) {
        const expectedWords = this.normalize(expected).split(" ").filter(Boolean);
        const actualWords = this.normalize(actual).split(" ").filter(Boolean);
        if (!expectedWords.length || !actualWords.length) return 0;
        const wordScore = expectedWords.reduce((total, expectedWord) => {
            const best = Math.max(
                0,
                ...actualWords.map(actualWord => this.tokenSimilarity(expectedWord, actualWord))
            );
            return total + best;
        }, 0) / expectedWords.length;
        const lengthScore = Math.min(expectedWords.length, actualWords.length) /
            Math.max(expectedWords.length, actualWords.length);
        return Math.round(((wordScore * 0.85) + (lengthScore * 0.15)) * 100);
    },

    evaluate(transcript, exercise) {
        const normalized = this.normalize(transcript);
        const words = normalized.split(" ").filter(Boolean);
        const settings = exercise.speech_settings || {};
        const variants = [exercise.phrase, ...(exercise.accepted_answers || [])]
            .filter(Boolean)
            .map(value => this.normalize(value));
        const concepts = (settings.required_concepts || []).filter(Boolean);
        const conceptScores = concepts.map(concept => this.phraseScore(concept, normalized));
        const missingConcepts = concepts.filter((_, index) => conceptScores[index] < 72);
        const variantPercentage = Math.max(
            0,
            ...variants.map(variant => this.phraseScore(variant, normalized))
        );
        const conceptPercentage = conceptScores.length
            ? Math.round(conceptScores.reduce((sum, score) => sum + score, 0) / conceptScores.length)
            : 0;
        const enoughWords = words.length >= (settings.min_words || 1);
        const percentage = variants.length
            ? Math.max(variantPercentage, conceptPercentage)
            : conceptPercentage;
        const correct = enoughWords && percentage >= 75 && (
            variantPercentage >= 75 ||
            (concepts.length > 0 && missingConcepts.length === 0)
        );
        return {
            correct,
            percentage,
            transcript: normalized,
            missing_concepts: missingConcepts,
            message: correct
                ? `Совпадение ${percentage}%. Слова и смысл распознаны; произношение не оценивается.`
                : missingConcepts.length
                    ? `Совпадение ${percentage}%. Не распознано: ${missingConcepts.join(", ")}.`
                    : `Совпадение ${percentage}%. Ответ слишком короткий или сильно отличается от образца.`,
            pronunciation_assessed: false
        };
    }
};
