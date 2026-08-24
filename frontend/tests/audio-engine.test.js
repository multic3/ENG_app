const fs = require("fs");
const vm = require("vm");


class MockUtterance {
    constructor(text) {
        this.text = text;
        this.voice = null;
    }
}


const spoken = [];
let cancelCount = 0;

const synthesis = {
    speaking: false,
    pending: false,
    paused: false,

    getVoices() {
        return [
            {
                name: "English local",
                lang: "en-US",
                localService: true
            }
        ];
    },

    speak(utterance) {
        spoken.push(utterance);
        utterance.onstart?.();
        utterance.onend?.();
    },

    cancel() {
        cancelCount++;
        this.speaking = false;
        this.pending = false;
    },

    resume() {
        this.paused = false;
    }
};


const context = {
    window: {
        speechSynthesis: synthesis,
        SpeechSynthesisUtterance:
            MockUtterance,
        SpeechRecognition: undefined,
        webkitSpeechRecognition: undefined
    },
    setTimeout,
    clearTimeout,
    console
};


vm.createContext(context);
vm.runInContext(
    `${fs.readFileSync(
        "frontend/audio-engine.js",
        "utf8"
    )}; this.audioEngine = AudioEngine;`,
    context
);


async function run() {
    const engine = context.audioEngine;
    let started = false;
    let ended = false;

    const supported = engine.speak(
        "Nagisa needs coffee.",
        {
            onStart: () => {
                started = true;
            },
            onEnd: () => {
                ended = true;
            }
        }
    );

    if (!supported) {
        throw new Error(
            "Supported synthesis was reported unavailable"
        );
    }

    if (!started || !ended) {
        throw new Error(
            "Speech lifecycle callbacks did not run"
        );
    }

    if (
        spoken[0].text !==
        "Nagisa needs coffee."
    ) {
        throw new Error(
            "The requested phrase was not spoken"
        );
    }

    if (
        spoken[0].voice?.lang !==
        "en-US"
    ) {
        throw new Error(
            "An English voice was not selected"
        );
    }

    synthesis.speaking = true;

    engine.speak(
        "Play it again."
    );

    await new Promise(
        resolve => setTimeout(resolve, 120)
    );

    if (cancelCount !== 1) {
        throw new Error(
            "Repeated speech did not cancel the old phrase"
        );
    }

    if (
        spoken.at(-1).text !==
        "Play it again."
    ) {
        throw new Error(
            "Repeated speech was swallowed"
        );
    }

    console.log(
        "OK speech playback and repeat handling"
    );
}


run().catch(
    error => {
        console.error(error);
        process.exit(1);
    }
);
