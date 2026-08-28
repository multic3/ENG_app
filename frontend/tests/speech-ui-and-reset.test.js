const assert = require("assert");
const fs = require("fs");

const app = fs.readFileSync("frontend/app.js", "utf8");
const html = fs.readFileSync("frontend/index.html", "utf8");
const styles = fs.readFileSync("frontend/styles.css", "utf8");
const speechEngine = fs.readFileSync("frontend/speech-engine.js", "utf8");

assert.match(html, /id="resetProgressButton"/);
assert.match(app, /Ты уверен, что хочешь сбросить прогресс\?/);
assert.match(app, /function addSpeechCorrectionTask/);
assert.match(app, /addSpeechCorrectionTask\(step\)/);
assert.match(speechEngine, /percentage/);
assert.match(styles, /\.speech-retry\.hidden[\s\S]*display:\s*none\s*!important/);
assert.match(styles, /grid-template-columns:\s*repeat\(3/);

console.log("OK speech controls, voice correction and confirmed progress reset");
