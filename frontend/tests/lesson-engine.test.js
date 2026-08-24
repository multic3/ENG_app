const fs = require("fs");
const vm = require("vm");


const source = fs.readFileSync(
    "frontend/lesson-engine.js",
    "utf8"
);

const context = {};

vm.createContext(context);
vm.runInContext(
    `${source}; this.engine = LessonEngine;`,
    context
);

const engine = context.engine;


if (
    engine.isTextAnswerCorrect(
        "anything",
        "watching"
    )
) {
    throw new Error(
        "An arbitrary correction was accepted"
    );
}


if (
    !engine.isTextAnswerCorrect(
        "  WATCHING! ",
        "watching"
    )
) {
    throw new Error(
        "A normalized correct answer was rejected"
    );
}


if (
    !engine.isTextAnswerCorrect(
        "I'm ready",
        "I am ready",
        ["I'm ready"]
    )
) {
    throw new Error(
        "An accepted answer was rejected"
    );
}


if (
    !engine.isTextAnswerCorrect(
        "The cat is sleeping",
        "The cat is sleeping now.",
        ["The cat is sleeping."]
    )
) {
    throw new Error(
        "Present Continuous without optional now was rejected"
    );
}


engine.start({
    steps: [{}]
});

if (
    engine.answerText(
        "anything",
        "watching"
    )
) {
    throw new Error(
        "An arbitrary lesson answer was accepted"
    );
}


const result = engine.getResult();

if (
    result.correct !== 0 ||
    result.total !== 1
) {
    throw new Error(
        "A wrong answer was scored incorrectly"
    );
}


console.log(
    "OK arbitrary text is rejected"
);
