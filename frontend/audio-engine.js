const AudioEngine = {

    recognition: null,

    isListening: false,

    utterance: null,

    speakTimer: null,


    isSpeechSynthesisSupported() {

        return Boolean(
            window.speechSynthesis &&
            window.SpeechSynthesisUtterance
        );

    },


    getEnglishVoice(
        language = "en-US"
    ) {

        if (
            !this.isSpeechSynthesisSupported()
        ) {
            return null;
        }


        const voices =
            typeof window.speechSynthesis
                .getVoices === "function"
                ? window.speechSynthesis
                    .getVoices()
                : [];


        return (
            voices.find(
                voice =>
                    voice.lang === language &&
                    voice.localService
            ) ||
            voices.find(
                voice =>
                    voice.lang === language
            ) ||
            voices.find(
                voice =>
                    voice.lang
                        .toLowerCase()
                        .startsWith("en") &&
                    voice.localService
            ) ||
            voices.find(
                voice =>
                    voice.lang
                        .toLowerCase()
                        .startsWith("en")
            ) ||
            null
        );

    },


    speak(
        text,
        options = {}
    ) {

        if (
            !this.isSpeechSynthesisSupported()
        ) {
            options.onError?.(
                "Speech synthesis is not supported."
            );

            return false;
        }


        const phrase =
            String(text ?? "").trim();


        if (!phrase) {
            options.onError?.(
                "There is no text to play."
            );

            return false;
        }


        const synthesis =
            window.speechSynthesis;


        if (this.speakTimer) {
            clearTimeout(
                this.speakTimer
            );

            this.speakTimer = null;
        }


        const play =
            () => {

                const utterance =
                    new window
                        .SpeechSynthesisUtterance(
                            phrase
                        );


                utterance.lang =
                    options.lang ?? "en-US";

                utterance.rate =
                    options.rate ?? 0.86;

                utterance.pitch =
                    options.pitch ?? 1;


                const voice =
                    this.getEnglishVoice(
                        utterance.lang
                    );


                if (voice) {
                    utterance.voice = voice;
                }


                utterance.onstart =
                    () => {

                        options.onStart?.();

                    };


                utterance.onend =
                    () => {

                        if (
                            this.utterance ===
                            utterance
                        ) {
                            this.utterance = null;
                        }


                        options.onEnd?.();

                    };


                utterance.onerror =
                    event => {

                        if (
                            this.utterance !==
                            utterance
                        ) {
                            return;
                        }


                        this.utterance = null;


                        if (
                            event.error !== "canceled" &&
                            event.error !== "interrupted"
                        ) {
                            options.onError?.(
                                event.error ||
                                "Audio playback failed."
                            );
                        }

                    };


                this.utterance =
                    utterance;


                try {

                    if (synthesis.paused) {
                        synthesis.resume();
                    }


                    synthesis.speak(
                        utterance
                    );

                } catch (error) {

                    this.utterance = null;


                    options.onError?.(
                        error.message ||
                        "Audio playback failed."
                    );

                }

            };


        if (
            synthesis.speaking ||
            synthesis.pending
        ) {

            synthesis.cancel();


            this.speakTimer =
                setTimeout(
                    () => {

                        this.speakTimer = null;

                        play();

                    },
                    80
                );

        } else {

            play();

        }


        return true;
    },


    stop() {

        if (this.speakTimer) {

            clearTimeout(
                this.speakTimer
            );

            this.speakTimer = null;

        }

        if (
            "speechSynthesis" in window
        ) {
            window.speechSynthesis
                .cancel();
        }


        this.utterance = null;


        if (
            this.recognition &&
            this.isListening
        ) {
            this.recognition.stop();
        }

    },


    isSpeechRecognitionSupported() {

        return Boolean(
            window.SpeechRecognition ||
            window.webkitSpeechRecognition
        );

    },


    listen(
        onResult,
        onStart,
        onEnd,
        onError
    ) {

        if (
            !this.isSpeechRecognitionSupported()
        ) {

            onError?.(
                "Speech recognition is not supported in this browser."
            );

            return;
        }


        const Recognition =
            window.SpeechRecognition ||
            window.webkitSpeechRecognition;


        this.recognition =
            new Recognition();


        this.recognition.lang =
            "en-US";

        this.recognition.continuous =
            false;

        this.recognition.interimResults =
            false;

        this.recognition.maxAlternatives =
            1;


        this.recognition.onstart =
            () => {

                this.isListening =
                    true;

                onStart?.();

            };


        this.recognition.onresult =
            event => {

                const transcript =
                    event
                        .results[0][0]
                        .transcript;

                onResult?.(
                    transcript
                );

            };


        this.recognition.onerror =
            event => {

                this.isListening =
                    false;

                onError?.(
                    event.error
                );

            };


        this.recognition.onend =
            () => {

                this.isListening =
                    false;

                onEnd?.();

            };

        try {

            this.recognition.start();

        } catch (error) {

            this.isListening = false;


            onError?.(
                error.message ||
                "Microphone could not start."
            );

        }

    }

};
