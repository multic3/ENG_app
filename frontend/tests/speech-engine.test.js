const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const context = { window: {} };
vm.createContext(context);
vm.runInContext(
    `${fs.readFileSync("frontend/speech-engine.js", "utf8")}; this.speechEngine = SpeechEngine;`,
    context
);

const repeat = {
    phrase: "Hello, Mia. Nice to meet you.",
    accepted_answers: ["Hello Mia, nice to meet you"],
    speech_settings: {
        required_concepts: ["hello", "mia", "nice to meet you"],
        min_words: 5,
        pronunciation_assessed: false
    }
};
assert.strictEqual(
    context.speechEngine.evaluate("Hello Mia nice to meet you", repeat).correct,
    true
);
assert.strictEqual(
    context.speechEngine.evaluate("anything", repeat).correct,
    false
);
assert.strictEqual(
    context.speechEngine.evaluate("Hello Mia nice to meet you", repeat).pronunciation_assessed,
    false
);

const response = {
    accepted_answers: ["I am Anya and I am from Russia"],
    speech_settings: {
        required_concepts: ["anya", "russia"],
        min_words: 5
    }
};
assert.strictEqual(
    context.speechEngine.evaluate("My name is Anya and I live in Russia", response).correct,
    true
);

console.log("OK speech provider architecture and semantic answer checks");
