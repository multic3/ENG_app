const fs = require("fs");
const vm = require("vm");


const createdElements = [];


function makeElement() {
    const classes = new Set();
    const listeners = {};

    const element = {
        children: [],
        style: {},
        textContent: "",
        disabled: false,
        onclick: null,
        value: "",
        parent: null,
        focused: false,

        classList: {
            add(...names) {
                names.forEach(
                    name => classes.add(name)
                );
            },

            remove(...names) {
                names.forEach(
                    name => classes.delete(name)
                );
            },

            contains(name) {
                return classes.has(name);
            }
        },

        appendChild(child) {
            child.parent = this;
            child.parentElement = this;
            this.children.push(child);
            return child;
        },

        remove() {
            if (!this.parent) {
                return;
            }

            this.parent.children =
                this.parent.children.filter(
                    child => child !== this
                );
            this.parent = null;
            this.parentElement = null;
        },

        addEventListener(type, listener) {
            listeners[type] = listener;
        },

        dispatch(type, event = {}) {
            return listeners[type]?.({
                preventDefault() {},
                stopPropagation() {},
                ...event
            });
        },

        setAttribute(name, value) {
            this[name] = value;
        },

        animate() {},

        focus() {
            this.focused = true;
        },

        select() {},

        hasClass(name) {
            return classes.has(name);
        }
    };

    Object.defineProperty(
        element,
        "className",
        {
            get() {
                return Array.from(classes).join(" ");
            },

            set(value) {
                classes.clear();
                String(value)
                    .split(/\s+/)
                    .filter(Boolean)
                    .forEach(
                        name => classes.add(name)
                    );
            }
        }
    );

    Object.defineProperty(
        element,
        "innerHTML",
        {
            get() {
                return this._innerHTML || "";
            },

            set(value) {
                this._innerHTML = value;

                if (value === "") {
                    this.children = [];
                }
            }
        }
    );

    createdElements.push(element);

    return element;
}


function isAttached(element) {
    let current = element;

    while (current) {
        if (current === lessonCard) {
            return true;
        }

        current = current.parent;
    }

    return false;
}


const elementsById = new Map();
const nagisaBubble = makeElement();
const lessonCard = makeElement();

elementsById.set(
    "lessonCard",
    lessonCard
);


const document = {
    getElementById(id) {
        if (!elementsById.has(id)) {
            elementsById.set(
                id,
                makeElement()
            );
        }

        return elementsById.get(id);
    },

    querySelector(selector) {
        if (selector === ".nagisa-bubble") {
            return nagisaBubble;
        }

        return null;
    },

    querySelectorAll(selector) {
        const className = selector.slice(1);

        return createdElements.filter(
            element =>
                element.hasClass(className) &&
                isAttached(element)
        );
    },

    createElement() {
        return makeElement();
    }
};


function findAttachedByText(text) {
    return createdElements.find(
        element =>
            element.textContent === text &&
            isAttached(element)
    );
}


async function run() {
    const gameData = JSON.parse(
        fs.readFileSync(
            "backend/app/levels.json",
            "utf8"
        )
    );

    const location = gameData.locations[0];
    const level = location.levels[0];
    const progress = {
        current_level: 1,
        xp: 0,
        streak: 1,
        hearts: 5,
        max_hearts: 5,
        completed_levels: []
    };
    const game = {
        player: {
            name: "Player",
            xp: 0,
            level: 1,
            level_xp: 0,
            level_xp_required: 40,
            level_progress_percent: 0,
            max_level: 100,
            streak: 1,
            hearts: 5,
            max_hearts: 5
        },
        progress,
        locations: gameData.locations.map(
            item => ({
                id: item.id,
                name: item.name,
                description: item.description,
                theme: item.theme
            })
        )
    };

    const context = {
        console,
        document,
        fetch: async url => {
            if (
                url ===
                "/api/players/session"
            ) {
                return {
                    ok: true,
                    status: 200,
                    json: async () => ({
                        success: true
                    })
                };
            }

            if (url === "/api/game") {
                return {
                    ok: true,
                    status: 200,
                    json: async () => game
                };
            }

            if (url === "/api/levels/1") {
                return {
                    ok: true,
                    status: 200,
                    json: async () => ({
                        level,
                        location
                    })
                };
            }

            if (
                url ===
                "/api/player/hearts/spend"
            ) {
                progress.hearts = 4;

                return {
                    ok: true,
                    status: 200,
                    json: async () => ({
                        progress
                    })
                };
            }

            throw new Error(
                `Unexpected fetch: ${url}`
            );
        },
        window: {
            scrollTo() {},
            SpeechRecognition: undefined,
            webkitSpeechRecognition: undefined
        },
        Headers,
        localStorage: {
            values: {
                englishRpgPlayerId: "anya",
                englishRpgPlayerName:
                    "Anya is a princess"
            },
            getItem(key) {
                return this.values[key] || null;
            },
            setItem(key, value) {
                this.values[key] = value;
            }
        },
        setTimeout,
        clearTimeout,
        Math
    };

    vm.createContext(context);

    for (
        const file of [
            "lesson-engine.js",
            "map-engine.js",
            "audio-engine.js"
        ]
    ) {
        vm.runInContext(
            fs.readFileSync(
                `frontend/${file}`,
                "utf8"
            ),
            context
        );
    }

    const appSource = fs.readFileSync(
        "frontend/app.js",
        "utf8"
    );

    vm.runInContext(
        `${appSource}; this.openLevelForTest = openLevel;`,
        context
    );

    await new Promise(
        resolve => setImmediate(resolve)
    );

    await context.openLevelForTest(1);

    const translatableQuestion =
        document.querySelectorAll(
            ".translatable-phrase"
        )[0];

    if (!translatableQuestion) {
        throw new Error(
            "Lesson question is not marked as translatable"
        );
    }

    translatableQuestion.dispatch("click");

    const translationPopover =
        document.querySelectorAll(
            ".translation-popover"
        )[0];

    if (
        !translationPopover ||
        translationPopover.textContent !==
            level.steps[0].question_translation
    ) {
        throw new Error(
            "Question translation did not appear"
        );
    }

    translatableQuestion.dispatch("click");

    const options =
        document.querySelectorAll(
            ".option-button"
        );

    await options[0].onclick();

    const correctionTask =
        document.querySelectorAll(
            ".correction-task"
        )[0];

    if (!correctionTask) {
        throw new Error(
            "Wrong answer did not create a correction task"
        );
    }

    const correctionInput =
        correctionTask.children[1];
    const correctionFeedback =
        correctionTask.children[2];
    const correctionButton =
        correctionTask.children[3];

    correctionInput.value = "anything";
    correctionButton.onclick();

    if (
        findAttachedByText("Continue") ||
        findAttachedByText("Finish")
    ) {
        throw new Error(
            "Arbitrary correction unlocked continuation"
        );
    }

    if (
        !correctionFeedback.classList
            .contains("error")
    ) {
        throw new Error(
            "Wrong correction did not show an error"
        );
    }

    correctionInput.value = "drinks";
    correctionButton.onclick();

    if (!findAttachedByText("Continue")) {
        throw new Error(
            "Correct correction did not unlock continuation"
        );
    }

    console.log(
        "OK wrong correction stays blocked; correct correction continues"
    );
}


run().catch(
    error => {
        console.error(error);
        process.exit(1);
    }
);
