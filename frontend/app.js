const state = {

    game: null,

    playerId: null,

    currentLocationId: 1,

    currentLevel: null,

    currentLocation: null,

    heartsSpentThisLevel: 0

};


const elements = {

    loginScreen:
        document.getElementById(
            "loginScreen"
        ),

    loginForm:
        document.getElementById(
            "loginForm"
        ),

    loginPlayerId:
        document.getElementById(
            "loginPlayerId"
        ),

    loginPlayerName:
        document.getElementById(
            "loginPlayerName"
        ),

    loginError:
        document.getElementById(
            "loginError"
        ),

    avatarButton:
        document.getElementById(
            "avatarButton"
        ),

    resetProgressButton:
        document.getElementById(
            "resetProgressButton"
        ),

    mapScreen:
        document.getElementById(
            "mapScreen"
        ),

    mapBackground:
        document.getElementById(
            "mapBackground"
        ),

    mapNagisa:
        document.getElementById(
            "mapNagisa"
        ),

    lessonScreen:
        document.getElementById(
            "lessonScreen"
        ),

    levelNodes:
        document.getElementById(
            "levelNodes"
        ),

    locationLabel:
        document.getElementById(
            "locationLabel"
        ),

    locationName:
        document.getElementById(
            "locationName"
        ),

    locationDescription:
        document.getElementById(
            "locationDescription"
        ),

    locationProgress:
        document.getElementById(
            "locationProgress"
        ),

    worldTitle:
        document.getElementById(
            "worldTitle"
        ),

    previousLocation:
        document.getElementById(
            "prevLocation"
        ),

    nextLocation:
        document.getElementById(
            "nextLocation"
        ),

    xpFill:
        document.getElementById(
            "xpFill"
        ),

    xpText:
        document.getElementById(
            "xpText"
        ),

    playerLevel:
        document.getElementById(
            "playerLevel"
        ),

    playerName:
        document.getElementById(
            "playerName"
        ),

    streak:
        document.getElementById(
            "streak"
        ),

    hearts:
        document.getElementById(
            "hearts"
        ),

    lessonLocation:
        document.getElementById(
            "lessonLocation"
        ),

    lessonProgress:
        document.getElementById(
            "lessonProgress"
        ),

    lessonProgressFill:
        document.getElementById(
            "lessonProgressFill"
        ),

    lessonHearts:
        document.getElementById(
            "lessonHearts"
        ),

    bossBanner:
        document.getElementById(
            "bossBanner"
        ),

    nagisaText:
        document.getElementById(
            "nagisaText"
        ),

    nagisaBubble:
        document.querySelector(
            ".nagisa-bubble"
        ),

    nagisaCharacter:
        document.getElementById(
            "nagisaCharacter"
        ),

    lessonCard:
        document.getElementById(
            "lessonCard"
        ),

    completeModal:
        document.getElementById(
            "completeModal"
        ),

    resultEmoji:
        document.getElementById(
            "resultEmoji"
        ),

    resultLabel:
        document.getElementById(
            "resultLabel"
        ),

    resultTitle:
        document.getElementById(
            "resultTitle"
        ),

    resultScore:
        document.getElementById(
            "resultScore"
        ),

    resultRank:
        document.getElementById(
            "resultRank"
        ),

    rewardText:
        document.getElementById(
            "rewardText"
        ),

    continueButton:
        document.getElementById(
            "continueButton"
        ),

    noHeartsModal:
        document.getElementById(
            "noHeartsModal"
        ),

    restoreHeartsButton:
        document.getElementById(
            "restoreHeartsButton"
        ),

    grammarHelpButton:
        document.getElementById(
            "grammarHelpButton"
        ),

    grammarHelpModal:
        document.getElementById(
            "grammarHelpModal"
        ),

    grammarHelpTitle:
        document.getElementById(
            "grammarHelpTitle"
        ),

    grammarHelpSummary:
        document.getElementById(
            "grammarHelpSummary"
        ),

    grammarHelpRules:
        document.getElementById(
            "grammarHelpRules"
        ),

    grammarHelpExamples:
        document.getElementById(
            "grammarHelpExamples"
        ),

    closeGrammarHelp:
        document.getElementById(
            "closeGrammarHelp"
        ),

    backToMap:
        document.getElementById(
            "backToMap"
        )

};


/* ===================================
   INIT
=================================== */

function apiFetch(
    url,
    options = {}
) {

    const headers = new Headers(
        options.headers || {}
    );


    if (state.playerId) {
        headers.set(
            "X-Player-ID",
            state.playerId
        );
    }


    return fetch(
        url,
        {
            ...options,
            headers
        }
    );

}


function showLogin() {

    elements.loginScreen.classList.remove(
        "hidden"
    );

    elements.loginPlayerId.value =
        state.playerId ||
        localStorage.getItem(
            "englishRpgPlayerId"
        ) || "";

    elements.loginPlayerName.value =
        state.game?.player?.name ||
        localStorage.getItem(
            "englishRpgPlayerName"
        ) || "";

    elements.loginError.textContent = "";

}


async function enterPlayerSession(
    playerId,
    playerName
) {

    const normalizedId =
        playerId.trim().toLowerCase();

    const normalizedName =
        playerName.trim();


    const sessionResponse =
        await fetch(
            "/api/players/session",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify(
                    {
                        player_id: normalizedId,
                        name: normalizedName
                    }
                )
            }
        );


    if (!sessionResponse.ok) {
        throw new Error(
            "Use 4–32 Latin letters, numbers, _ or - for the ID."
        );
    }


    state.playerId = normalizedId;

    localStorage.setItem(
        "englishRpgPlayerId",
        normalizedId
    );
    localStorage.setItem(
        "englishRpgPlayerName",
        normalizedName
    );


    const gameResponse =
        await apiFetch("/api/game");


    if (!gameResponse.ok) {
        throw new Error(
            "Failed to load this player."
        );
    }


    state.game =
        await gameResponse.json();

    elements.loginScreen.classList.add(
        "hidden"
    );

    renderHeader();
    openLocation(
        Math.ceil(
            state.game.progress
                .current_level / 50
        )
    );

}

async function init() {

    const savedPlayerId =
        localStorage.getItem(
            "englishRpgPlayerId"
        );
    const savedPlayerName =
        localStorage.getItem(
            "englishRpgPlayerName"
        );


    if (!savedPlayerId || !savedPlayerName) {
        showLogin();
        return;
    }


    try {
        await enterPlayerSession(
            savedPlayerId,
            savedPlayerName
        );
    } catch (error) {
        console.error(error);
        showLogin();
        elements.loginError.textContent =
            "Could not connect. Please try again.";
    }

}


elements.loginForm.addEventListener(
    "submit",
    async event => {
        event.preventDefault();
        elements.loginError.textContent = "";

        try {
            await enterPlayerSession(
                elements.loginPlayerId.value,
                elements.loginPlayerName.value
            );
        } catch (error) {
            elements.loginError.textContent =
                error.message;
        }
    }
);


elements.avatarButton.addEventListener(
    "click",
    showLogin
);


elements.resetProgressButton.addEventListener(
    "click",
    async () => {
        if (!state.game) return;
        const confirmed = window.confirm(
            "Ты уверен, что хочешь сбросить прогресс?"
        );
        if (!confirmed) return;

        elements.resetProgressButton.disabled = true;
        try {
            const response = await apiFetch("/api/reset", {
                method: "POST"
            });
            if (!response.ok) {
                throw new Error("Progress reset failed.");
            }
            const data = await response.json();
            state.game.progress = data.progress;
            state.currentLevel = null;
            state.currentLocationId = 1;
            syncPlayerFromProgress();
            elements.lessonScreen.classList.remove("active");
            elements.mapScreen.classList.add("active");
            elements.grammarHelpButton.classList.add("hidden");
            openLocation(1);
            showNagisa("Прогресс сброшен. Начинаем новое путешествие!");
        } catch (error) {
            console.error(error);
            window.alert("Не удалось сбросить прогресс. Попробуйте ещё раз.");
        } finally {
            elements.resetProgressButton.disabled = false;
        }
    }
);


/* ===================================
   HEADER
=================================== */

function renderHeader() {

    if (!state.game) {
        return;
    }


    const player =
        state.game.player;


    elements.playerName.textContent =
        player.name;


    elements.playerLevel.textContent =
        `LV ${player.level}`;


    if (
        player.level >=
        player.max_level
    ) {

        elements.xpText.textContent =
            "MAX LEVEL";

    } else {

        elements.xpText.textContent =
            `${player.level_xp} / ${player.level_xp_required} XP`;

    }


    elements.xpText.title =
        `${player.xp} total XP`;


    elements.xpFill.style.width =
        `${player.level_progress_percent}%`;


    elements.streak.textContent =
        `🔥 ${player.streak}`;


    renderHearts(
        player.hearts,
        player.max_hearts
    );

}


function renderHearts(
    current,
    max
) {

    const full =
        "❤️".repeat(
            current
        );


    const empty =
        "🖤".repeat(
            Math.max(
                0,
                max - current
            )
        );


    const value =
        `${full}${empty}`;


    elements.hearts.textContent =
        value;


    elements.lessonHearts.textContent =
        value;

}


/* ===================================
   LOCATION
=================================== */

function getLocation(
    locationId
) {

    return state.game.locations.find(
        location =>
            location.id === locationId
    );

}


function openLocation(
    locationId
) {

    const location =
        getLocation(
            locationId
        );


    if (!location) {
        return;
    }


    state.currentLocationId =
        locationId;

    state.currentLocation =
        location;


    renderLocation();

}


function renderLocation() {

    const location =
        state.currentLocation;


    if (!location) {
        return;
    }


    const currentLevel =
        state.game.progress
            .current_level;


    const startLevel =
        (
            (location.id - 1)
            * 50
        ) + 1;


    const endLevel =
        location.id * 50;


    const completed =
        state.game.progress
            .completed_levels
            .filter(
                id =>
                    id >= startLevel &&
                    id <= endLevel
            )
            .length;


    elements.locationLabel.textContent =
        `LOCATION ${location.id}`;


    elements.locationName.textContent =
        location.name;


    elements.locationDescription.textContent =
        location.description;


    elements.locationProgress.textContent =
        `${completed} / 50`;


    elements.worldTitle.textContent =
        location.name;


    elements.mapBackground.className =
        `map-background theme-${
            location.theme || "default"
        }`;


    elements.previousLocation.disabled =
        location.id <= 1;


    const nextLocation =
        getLocation(
            location.id + 1
        );


    const nextLocationStart =
        (location.id * 50) + 1;


    const nextUnlocked =
        nextLocation &&
        nextLocation.content_status === "complete" &&
        currentLevel >=
        nextLocationStart;


    elements.nextLocation.disabled =
        !nextUnlocked;


    MapEngine.render(
        elements.levelNodes,
        location,
        state.game.progress,
        openLevel
    );


    const nagisaPosition =
        MapEngine.getNagisaPosition(
            location,
            state.game.progress
        );


    elements.mapNagisa.style.left =
        `${nagisaPosition.x}%`;

    elements.mapNagisa.style.top =
        `${nagisaPosition.y}%`;

    elements.mapNagisa.style.bottom =
        "auto";

    elements.mapNagisa.setAttribute(
        "aria-label",
        `Nagisa is near level ${nagisaPosition.level}`
    );

    const revealCurrentPoint = () => {
        elements.mapNagisa.scrollIntoView?.({
            block: "center",
            behavior: "smooth"
        });
    };
    if (typeof requestAnimationFrame === "function") {
        requestAnimationFrame(revealCurrentPoint);
    } else {
        revealCurrentPoint();
    }

}


/* ===================================
   LOCATION NAVIGATION
=================================== */

elements.previousLocation.onclick =
    () => {

        if (
            state.currentLocationId <= 1
        ) {
            return;
        }


        openLocation(
            state.currentLocationId - 1
        );

    };


elements.nextLocation.onclick =
    () => {

        const location =
            getLocation(
                state.currentLocationId + 1
            );


        if (!location) {
            return;
        }


        const startLevel =
            (
                state.currentLocationId
                * 50
            ) + 1;


        if (
            state.game.progress
                .current_level
            < startLevel
        ) {
            return;
        }


        openLocation(
            state.currentLocationId + 1
        );

    };


/* ===================================
   OPEN LEVEL
=================================== */

async function openLevel(
    levelId
) {

    try {

        const response =
            await apiFetch(
                `/api/levels/${levelId}`
            );


        if (
            response.status === 403
        ) {

            showNagisa(
                "This path is still locked."
            );

            return;
        }


        if (!response.ok) {
            throw new Error(
                "Level loading failed."
            );
        }


        const data =
            await response.json();


        state.currentLevel =
            data.level;


        state.currentLocation =
            data.location;


        if (
            state.currentLevel
                .grammar_help
        ) {
            elements.grammarHelpButton
                .classList.remove(
                    "hidden"
                );
        } else {
            elements.grammarHelpButton
                .classList.add(
                    "hidden"
                );
        }


        state.heartsSpentThisLevel =
            0;


        elements.mapScreen
            .classList.remove(
                "active"
            );


        elements.lessonScreen
            .classList.add(
                "active"
            );


        elements.lessonLocation.textContent =
            state.currentLocation.name;


        if (
            state.currentLevel.boss
        ) {

            elements.bossBanner
                .classList.remove(
                    "hidden"
                );


            showNagisa(
                "Boss time. Let's see what you've learned."
            );

        } else {

            elements.bossBanner
                .classList.add(
                    "hidden"
                );


            showNagisa(
                getIntroMessage()
            );

        }


        LessonEngine.start(
            state.currentLevel
        );


        renderLesson();

        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });


    } catch (error) {

        console.error(
            error
        );

    }

}


/* ===================================
   LESSON
=================================== */

let activeTranslationPopover = null;
let translationHideTimer = null;


function hideTranslationPopover() {

    if (translationHideTimer) {
        clearTimeout(
            translationHideTimer
        );

        translationHideTimer = null;
    }


    activeTranslationPopover
        ?.remove?.();

    activeTranslationPopover = null;

}


function makeTranslatable(
    element,
    translation
) {

    if (!translation) {
        return;
    }


    element.classList.add(
        "translatable-phrase"
    );

    element.setAttribute(
        "tabindex",
        "0"
    );

    element.setAttribute(
        "aria-label",
        `${element.textContent}. Нажмите, чтобы увидеть перевод.`
    );


    const showTranslation = event => {

        event?.preventDefault?.();
        event?.stopPropagation?.();


        if (
            activeTranslationPopover
                ?.parentElement === element
        ) {
            hideTranslationPopover();
            return;
        }


        hideTranslationPopover();


        const popover =
            document.createElement(
                "span"
            );

        popover.className =
            "translation-popover";

        popover.textContent =
            translation;

        element.appendChild(popover);

        activeTranslationPopover =
            popover;

        translationHideTimer =
            setTimeout(
                hideTranslationPopover,
                3500
            );

    };


    element.addEventListener(
        "click",
        showTranslation
    );

    element.addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Enter" ||
                event.key === " "
            ) {
                showTranslation(event);
            }

        }
    );

}

function renderLesson() {

    const step =
        LessonEngine
            .getCurrentStep();


    if (!step) {

        completeCurrentLevel();

        return;
    }


    const total =
        LessonEngine.getStepCount();


    const number =
        LessonEngine
            .getCurrentStepNumber();


    elements.lessonProgress.textContent =
        `${number} / ${total}`;


    elements.lessonProgressFill.style.width =
        `${(
            (number - 1)
            / total
        ) * 100}%`;


    hideTranslationPopover();


    elements.lessonCard.innerHTML =
        "";


    const title =
        document.createElement(
            "h2"
        );


    title.className =
        "lesson-title";


    title.textContent =
        state.currentLevel.title;


    elements.lessonCard.appendChild(
        title
    );

    if (step.review_for) {
        const reviewBadge = document.createElement("div");
        reviewBadge.className = "review-badge";
        reviewBadge.textContent = "↻ Повторение прошлой ошибки";
        elements.lessonCard.appendChild(reviewBadge);
    }


    switch (
        step.type
    ) {

        case "choice":

            renderChoice(
                step
            );

            break;


        case "text":

            renderText(
                step
            );

            break;


        case "translation":

            renderTranslation(
                step
            );

            break;


        case "listening":

            renderListening(
                step
            );

            break;


        case "speaking":

            renderSpeechExerciseV2(
                step
            );

            break;


        default:

            renderUnsupportedStep(
                step
            );

    }

}


/* ===================================
   CHOICE
=================================== */

function renderChoice(
    step
) {

    const question =
        document.createElement(
            "div"
        );


    question.className =
        "lesson-question";


    question.textContent =
        step.question;

    makeTranslatable(
        question,
        step.question_translation
    );


    elements.lessonCard.appendChild(
        question
    );


    step.options.forEach(
        (
            option,
            index
        ) => {

            const button =
                document.createElement(
                    "button"
                );


            button.className =
                "option-button";


            button.textContent =
                option;


            button.onclick =
                async () => {

                    if (
                        LessonEngine.answered
                    ) {
                        return;
                    }


                    const correct =
                        LessonEngine.answerChoice(
                            index,
                            step.answer
                        );


                    const buttons =
                        document.querySelectorAll(
                            ".option-button"
                        );


                    buttons.forEach(
                        item => {
                            item.disabled =
                                true;
                        }
                    );


                    if (correct) {

                        button.classList.add(
                            "correct"
                        );


                        showNagisaCorrect();

                        playCorrectSound();

                    } else {

                        button.classList.add(
                            "wrong"
                        );


                        if (
                            buttons[
                                step.answer
                            ]
                        ) {

                            buttons[
                                step.answer
                            ].classList.add(
                                "correct"
                            );

                        }


                        showNagisaWrong();


                        await spendHeart();

                    }


                    addExplanation(
                        step
                    );


                    if (correct) {

                        addNextButton();

                    } else {

                        addCorrectionTask(
                            step.options[
                                step.answer
                            ]
                        );

                    }

                };


            elements.lessonCard
                .appendChild(
                    button
                );

        }
    );

}


/* ===================================
   TEXT
=================================== */

function renderText(
    step
) {

    const question =
        document.createElement(
            "div"
        );


    question.className =
        "lesson-question";


    question.textContent =
        step.question;

    makeTranslatable(
        question,
        step.question_translation
    );


    elements.lessonCard.appendChild(
        question
    );


    if (step.sentence) {

        const sentence =
            document.createElement(
                "div"
            );


        sentence.className =
            "lesson-subtext";


        sentence.textContent =
            step.sentence;

        makeTranslatable(
            sentence,
            step.sentence_translation
        );


        elements.lessonCard.appendChild(
            sentence
        );

    }


    const input =
        document.createElement(
            "input"
        );


    input.className =
        "text-answer";


    input.placeholder =
        "Type your answer";


    elements.lessonCard.appendChild(
        input
    );


    const button =
        document.createElement(
            "button"
        );


    button.className =
        "primary-button";


    button.textContent =
        "Check";


    button.onclick =
        async () => {

            if (
                LessonEngine.answered
            ) {
                return;
            }


            const correct =
                LessonEngine.answerText(
                    input.value,
                    step.answer,
                    step.accepted_answers || []
                );


            input.disabled =
                true;


            button.disabled =
                true;


            if (correct) {

                showNagisaCorrect();

                playCorrectSound();

            } else {

                showNagisaWrong();

                await spendHeart();

            }


            addExplanation(
                step,
                correct
                    ? null
                    : `Correct answer: ${step.answer}`
            );


            if (correct) {

                addNextButton();

            } else {

                addCorrectionTask(
                    step.answer,
                    step.accepted_answers || []
                );

            }

        };


    elements.lessonCard
        .appendChild(
            button
        );

}


/* ===================================
   TRANSLATION
=================================== */

function renderTranslation(
    step
) {

    const question =
        document.createElement(
            "div"
        );


    question.className =
        "lesson-question";


    question.textContent =
        step.question;

    makeTranslatable(
        question,
        step.question_translation
    );


    elements.lessonCard.appendChild(
        question
    );


    const input =
        document.createElement(
            "input"
        );


    input.className =
        "text-answer";


    input.placeholder =
        "Write in English";


    elements.lessonCard.appendChild(
        input
    );


    const button =
        document.createElement(
            "button"
        );


    button.className =
        "primary-button";


    button.textContent =
        "Check";


    button.onclick =
        async () => {

            if (
                LessonEngine.answered
            ) {
                return;
            }


            const correct =
                LessonEngine.answerText(
                    input.value,
                    step.answer,
                    step.accepted_answers || []
                );


            input.disabled =
                true;


            button.disabled =
                true;


            if (correct) {

                showNagisaCorrect();

                playCorrectSound();

            } else {

                showNagisaWrong();

                await spendHeart();

            }


            addExplanation(
                step,
                correct
                    ? null
                    : `Possible answer: ${step.answer}`
            );


            if (correct) {

                addNextButton();

            } else {

                addCorrectionTask(
                    step.answer,
                    step.accepted_answers || []
                );

            }

        };


    elements.lessonCard
        .appendChild(
            button
        );

}


/* ===================================
   LISTENING
=================================== */

function createSpeechButton(
    text,
    label = "Listen"
) {

    const button =
        document.createElement(
            "button"
        );


    button.className =
        "listening-button";


    button.textContent =
        `🔊 ${label}`;


    button.setAttribute(
        "aria-label",
        `${label}: ${text}`
    );


    const resetButton =
        () => {

            button.classList.remove(
                "speaking",
                "audio-error"
            );


            button.textContent =
                `🔊 ${label}`;

        };


    button.onclick =
        () => {

            const started =
                AudioEngine.speak(
                    text,
                    {
                        onStart: () => {

                            button.classList.add(
                                "speaking"
                            );


                            button.textContent =
                                "🔊 Playing...";

                        },

                        onEnd: resetButton,

                        onError: () => {

                            button.classList.remove(
                                "speaking"
                            );


                            button.classList.add(
                                "audio-error"
                            );


                            button.textContent =
                                "🔇 Audio unavailable";

                        }
                    }
                );


            if (!started) {
                button.disabled = true;
            }

        };


    return button;

}

function renderListening(
    step
) {

    const question =
        document.createElement(
            "div"
        );


    question.className =
        "lesson-question";


    question.textContent =
        step.question;

    makeTranslatable(
        question,
        step.question_translation
    );


    elements.lessonCard.appendChild(
        question
    );


    const listenButton =
        createSpeechButton(
            step.audio_text ||
            step.question,
            "Listen"
        );


    elements.lessonCard.appendChild(
        listenButton
    );


    step.options.forEach(
        (
            option,
            index
        ) => {

            const button =
                document.createElement(
                    "button"
                );


            button.className =
                "option-button";


            button.textContent =
                option;


            button.onclick =
                async () => {

                    if (
                        LessonEngine.answered
                    ) {
                        return;
                    }


                    const correct =
                        LessonEngine.answerChoice(
                            index,
                            step.answer
                        );


                    document
                        .querySelectorAll(
                            ".option-button"
                        )
                        .forEach(
                            item => {
                                item.disabled =
                                    true;
                            }
                        );


                    if (correct) {

                        button.classList.add(
                            "correct"
                        );

                        showNagisaCorrect();

                        playCorrectSound();

                    } else {

                        button.classList.add(
                            "wrong"
                        );


                        const buttons =
                            document
                                .querySelectorAll(
                                    ".option-button"
                                );


                        if (
                            buttons[
                                step.answer
                            ]
                        ) {

                            buttons[
                                step.answer
                            ].classList.add(
                                "correct"
                            );

                        }


                        showNagisaWrong();

                        await spendHeart();

                    }


                    addExplanation(
                        step
                    );


                    if (correct) {

                        addNextButton();

                    } else {

                        addCorrectionTask(
                            step.options[
                                step.answer
                            ]
                        );

                    }

                };


            elements.lessonCard
                .appendChild(
                    button
                );

        }
    );

}


/* ===================================
   SPEAKING
=================================== */

function createSpeechRecorder(settings, transcriptElement, onRecorded) {
    const controls = document.createElement("div");
    controls.className = "speech-controls";

    const startButton = document.createElement("button");
    startButton.className = "speech-control-button speech-start";
    startButton.textContent = "🎙 Start";

    const stopButton = document.createElement("button");
    stopButton.className = "speech-control-button speech-stop";
    stopButton.textContent = "Stop";
    stopButton.disabled = true;

    const retryButton = document.createElement("button");
    retryButton.className = "speech-control-button speech-retry hidden";
    retryButton.textContent = "Record again";

    controls.append(startButton, stopButton, retryButton);
    let recording = false;
    let spokenText = "";

    const setIdle = () => {
        recording = false;
        startButton.disabled = false;
        stopButton.disabled = true;
        startButton.classList.remove("recording");
    };

    const startRecording = () => {
        if (recording) return;
        recording = true;
        spokenText = "";
        startButton.disabled = true;
        stopButton.disabled = false;
        retryButton.classList.add("hidden");
        transcriptElement.textContent = "Listening…";

        const started = SpeechEngine.start(settings, {
            onStart: () => startButton.classList.add("recording"),
            onTranscript: text => {
                spokenText = text;
                transcriptElement.textContent = text ? `“${text}”` : "Listening…";
            },
            onEnd: () => {
                setIdle();
                retryButton.classList.remove("hidden");
                if (spokenText) onRecorded(spokenText);
            },
            onError: error => {
                setIdle();
                retryButton.classList.remove("hidden");
                transcriptElement.textContent = `Microphone error: ${error}`;
            }
        });

        if (!started) setIdle();
    };

    startButton.onclick = startRecording;
    stopButton.onclick = () => {
        if (recording) SpeechEngine.stop();
    };
    retryButton.onclick = () => {
        if (!recording) startRecording();
    };

    return {
        element: controls,
        disable() {
            recording = false;
            startButton.disabled = true;
            stopButton.disabled = true;
            retryButton.disabled = true;
        },
        requireNewRecording() {
            retryButton.classList.remove("hidden");
        }
    };
}


function renderSpeechExerciseV2(step) {
    const wrapper = document.createElement("div");
    wrapper.className = "speaking-box";

    const question = document.createElement("div");
    question.className = "lesson-question";
    question.textContent = step.question;
    makeTranslatable(question, step.question_translation);
    wrapper.appendChild(question);

    const settings = step.speech_settings || {};
    if (step.phrase && settings.show_model_before_attempt !== false) {
        const target = document.createElement("div");
        target.className = "lesson-subtext";
        target.textContent = step.phrase;
        makeTranslatable(target, step.phrase_translation);
        wrapper.appendChild(target);
        wrapper.appendChild(createSpeechButton(step.phrase, "Hear phrase"));
    }

    const transcript = document.createElement("div");
    transcript.className = "speaking-transcript";
    transcript.textContent = "Press Start and speak. Words and meaning are checked; pronunciation is not.";

    const checkButton = document.createElement("button");
    checkButton.className = "primary-button speech-check hidden";
    checkButton.textContent = "Check answer";
    let spokenText = "";

    const recorder = createSpeechRecorder(settings, transcript, text => {
        spokenText = text;
        checkButton.classList.remove("hidden");
    });

    wrapper.appendChild(recorder.element);
    wrapper.appendChild(transcript);
    wrapper.appendChild(checkButton);
    elements.lessonCard.appendChild(wrapper);

    if (!SpeechEngine.isSupported()) {
        recorder.disable();
        transcript.textContent = "Voice recognition is unavailable on this device. Practice aloud and continue.";
        const continueButton = document.createElement("button");
        continueButton.className = "primary-button";
        continueButton.textContent = "I practised aloud";
        continueButton.onclick = () => {
            if (!LessonEngine.skipCurrentStep()) return;
            continueButton.disabled = true;
            addExplanation(step, "Voice check skipped: this browser has no recognition provider.");
            addNextButton();
        };
        wrapper.appendChild(continueButton);
        return;
    }

    checkButton.onclick = async () => {
        if (!spokenText || LessonEngine.answered) return;
        const result = SpeechEngine.evaluate(spokenText, step);
        LessonEngine.answerSpeakingResult(result.correct);
        recorder.disable();
        checkButton.disabled = true;
        transcript.textContent = `“${spokenText}” — ${result.message}`;
        if (result.correct) {
            showNagisaCorrect();
            playCorrectSound();
            addExplanation(step, result.message);
            addNextButton();
        } else {
            showNagisaWrong();
            await spendHeart();
            addExplanation(step, result.message);
            addSpeechCorrectionTask(step);
        }
    };
}


function addSpeechCorrectionTask(step) {
    const task = document.createElement("div");
    task.className = "correction-task speech-correction-task";

    const title = document.createElement("div");
    title.className = "correction-title";
    title.textContent = "Повтори правильный ответ голосом, чтобы продолжить:";
    task.appendChild(title);

    const model = step.phrase || step.accepted_answers?.[0] || "";
    if (model) {
        const phrase = document.createElement("div");
        phrase.className = "lesson-subtext";
        phrase.textContent = model;
        task.appendChild(phrase);
        task.appendChild(createSpeechButton(model, "Hear correction"));
    }

    const transcript = document.createElement("div");
    transcript.className = "speaking-transcript";
    transcript.textContent = "Запиши исправление голосом.";

    const checkButton = document.createElement("button");
    checkButton.className = "primary-button speech-check hidden";
    checkButton.textContent = "Check correction";
    let spokenText = "";
    let completed = false;

    const recorder = createSpeechRecorder(step.speech_settings || {}, transcript, text => {
        spokenText = text;
        checkButton.disabled = false;
        checkButton.classList.remove("hidden");
    });

    checkButton.onclick = () => {
        if (completed || !spokenText) return;
        const result = SpeechEngine.evaluate(spokenText, step);
        transcript.textContent = `“${spokenText}” — ${result.message}`;
        if (!result.correct) {
            checkButton.classList.add("hidden");
            spokenText = "";
            recorder.requireNewRecording();
            return;
        }
        completed = true;
        recorder.disable();
        checkButton.disabled = true;
        showNagisaCorrect();
        playCorrectSound();
        addNextButton();
    };

    task.appendChild(recorder.element);
    task.appendChild(transcript);
    task.appendChild(checkButton);
    elements.lessonCard.appendChild(task);
}

function renderSpeechExercise(step) {
    const wrapper = document.createElement("div");
    wrapper.className = "speaking-box";

    const question = document.createElement("div");
    question.className = "lesson-question";
    question.textContent = step.question;
    makeTranslatable(question, step.question_translation);
    wrapper.appendChild(question);

    const settings = step.speech_settings || {};
    if (step.phrase && settings.show_model_before_attempt !== false) {
        const target = document.createElement("div");
        target.className = "lesson-subtext";
        target.textContent = step.phrase;
        makeTranslatable(target, step.phrase_translation);
        wrapper.appendChild(target);
        wrapper.appendChild(createSpeechButton(step.phrase, "Hear phrase"));
    }

    const controls = document.createElement("div");
    controls.className = "speech-controls";
    const startButton = document.createElement("button");
    startButton.className = "mic-button";
    startButton.textContent = "🎙️ Start";
    const stopButton = document.createElement("button");
    stopButton.className = "option-button speech-stop";
    stopButton.textContent = "Stop";
    stopButton.disabled = true;
    const retryButton = document.createElement("button");
    retryButton.className = "option-button speech-retry hidden";
    retryButton.textContent = "Record again";
    controls.append(startButton, stopButton, retryButton);
    wrapper.appendChild(controls);

    const transcript = document.createElement("div");
    transcript.className = "speaking-transcript";
    transcript.textContent = "Press Start and speak. The app checks words and meaning, not pronunciation.";
    wrapper.appendChild(transcript);

    const checkButton = document.createElement("button");
    checkButton.className = "primary-button hidden";
    checkButton.textContent = "Check answer";
    wrapper.appendChild(checkButton);
    elements.lessonCard.appendChild(wrapper);

    let spokenText = "";

    if (!SpeechEngine.isSupported()) {
        startButton.disabled = true;
        transcript.textContent = "Voice recognition is unavailable on this device. Practice aloud and continue.";
        const continueButton = document.createElement("button");
        continueButton.className = "primary-button";
        continueButton.textContent = "I practised aloud";
        continueButton.onclick = () => {
            if (!LessonEngine.skipCurrentStep()) return;
            continueButton.disabled = true;
            addExplanation(step, "Voice check skipped: this browser has no recognition provider.");
            addNextButton();
        };
        wrapper.appendChild(continueButton);
        return;
    }

    const startRecording = () => {
        spokenText = "";
        checkButton.classList.add("hidden");
        retryButton.classList.add("hidden");
        transcript.textContent = "Listening…";
        SpeechEngine.start(settings, {
            onStart: () => {
                startButton.disabled = true;
                stopButton.disabled = false;
                startButton.classList.add("recording");
            },
            onTranscript: text => {
                spokenText = text;
                transcript.textContent = text ? `“${text}”` : "Listening…";
            },
            onEnd: () => {
                startButton.disabled = false;
                stopButton.disabled = true;
                startButton.classList.remove("recording");
                if (spokenText) {
                    checkButton.classList.remove("hidden");
                    retryButton.classList.remove("hidden");
                }
            },
            onError: error => {
                startButton.disabled = false;
                stopButton.disabled = true;
                startButton.classList.remove("recording");
                transcript.textContent = `Microphone error: ${error}`;
                retryButton.classList.remove("hidden");
            }
        });
    };

    startButton.onclick = startRecording;
    stopButton.onclick = () => SpeechEngine.stop();
    retryButton.onclick = startRecording;
    checkButton.onclick = async () => {
        const result = SpeechEngine.evaluate(spokenText, step);
        LessonEngine.answerSpeakingResult(result.correct);
        startButton.disabled = true;
        stopButton.disabled = true;
        retryButton.disabled = true;
        checkButton.disabled = true;
        transcript.textContent = `“${spokenText}” — ${result.message}`;
        if (result.correct) {
            showNagisaCorrect();
            playCorrectSound();
            addExplanation(step, result.message);
            addNextButton();
        } else {
            showNagisaWrong();
            await spendHeart();
            addExplanation(step, result.message);
            addCorrectionTask(step.phrase || step.accepted_answers?.[0] || "Please try again");
        }
    };
}

function renderSpeaking(
    step
) {

    const wrapper =
        document.createElement(
            "div"
        );


    wrapper.className =
        "speaking-box";


    const question =
        document.createElement(
            "div"
        );


    question.className =
        "lesson-question";


    question.textContent =
        step.question;

    makeTranslatable(
        question,
        step.question_translation
    );


    wrapper.appendChild(
        question
    );


    const target =
        document.createElement(
            "div"
        );


    target.className =
        "lesson-subtext";


    target.textContent =
        step.phrase;

    makeTranslatable(
        target,
        step.phrase_translation
    );


    wrapper.appendChild(
        target
    );


    const hearButton =
        createSpeechButton(
            step.phrase,
            "Hear phrase"
        );


    wrapper.appendChild(
        hearButton
    );


    const mic =
        document.createElement(
            "button"
        );


    mic.className =
        "mic-button";


    mic.textContent =
        "🎙️";


    wrapper.appendChild(
        mic
    );


    const transcript =
        document.createElement(
            "div"
        );


    transcript.className =
        "speaking-transcript";


    transcript.textContent =
        "Tap the microphone and speak.";


    wrapper.appendChild(
        transcript
    );


    elements.lessonCard.appendChild(
        wrapper
    );


    if (
        !AudioEngine
            .isSpeechRecognitionSupported()
    ) {

        transcript.textContent =
            "Voice checking is not available. Say the phrase aloud, then continue.";


        const continueButton =
            document.createElement(
                "button"
            );


        continueButton.className =
            "primary-button";


        continueButton.textContent =
            "I practiced the phrase";


        continueButton.onclick =
            () => {

                if (
                    !LessonEngine
                        .skipCurrentStep()
                ) {
                    return;
                }


                continueButton.disabled =
                    true;


                addExplanation(
                    step,
                    "Voice check skipped on this device."
                );


                addNextButton();

            };


        wrapper.appendChild(
            continueButton
        );


        return;
    }


    mic.onclick =
        () => {

            if (
                AudioEngine.isListening
            ) {
                return;
            }


            mic.classList.add(
                "recording"
            );


            transcript.textContent =
                "Listening...";


            AudioEngine.listen(

                async spokenText => {

                    transcript.textContent =
                        `"${spokenText}"`;


                    const correct =
                        LessonEngine
                            .answerSpeaking(
                                spokenText,
                                step.phrase
                            );


                    mic.disabled =
                        true;


                    if (correct) {

                        showNagisaCorrect();

                        playCorrectSound();

                    } else {

                        showNagisaWrong();

                        await spendHeart();

                    }


                    addExplanation(
                        step,
                        correct
                            ? null
                            : `Try saying: "${step.phrase}"`
                    );


                    if (correct) {

                        addNextButton();

                    } else {

                        addCorrectionTask(
                            step.phrase
                        );

                    }

                },


                () => {

                    mic.classList.add(
                        "recording"
                    );

                    transcript.textContent =
                        "Listening...";

                },


                () => {

                    mic.classList.remove(
                        "recording"
                    );

                },


                error => {

                    mic.classList.remove(
                        "recording"
                    );

                    transcript.textContent =
                        `Microphone error: ${error}`;

                }

            );

        };

}


/* ===================================
   UNSUPPORTED
=================================== */

function renderUnsupportedStep(
    step
) {

    elements.lessonCard.innerHTML += `
        <div class="lesson-question">
            Exercise type "${step.type}" is not implemented yet.
        </div>
    `;

}


/* ===================================
   EXPLANATION
=================================== */

function addExplanation(
    step,
    extra = null
) {

    const explanation =
        document.createElement(
            "div"
        );


    explanation.className =
        "explanation";


    explanation.innerHTML = `
        ${step.explanation || ""}

        ${
            extra
                ? `<br><br>${extra}`
                : ""
        }
    `;


    elements.lessonCard
        .appendChild(
            explanation
        );

}


/* ===================================
   CORRECTION TASK
=================================== */

function addCorrectionTask(
    answer,
    acceptedAnswers = []
) {

    const task =
        document.createElement(
            "div"
        );


    task.className =
        "correction-task";


    const title =
        document.createElement(
            "div"
        );


    title.className =
        "correction-title";


    title.textContent =
        "Type the correct answer to continue:";


    const input =
        document.createElement(
            "input"
        );


    input.className =
        "text-answer correction-input";


    input.placeholder =
        "Correct answer";


    input.autocomplete =
        "off";


    const feedback =
        document.createElement(
            "div"
        );


    feedback.className =
        "correction-feedback";


    const button =
        document.createElement(
            "button"
        );


    button.className =
        "primary-button";


    button.textContent =
        "Check correction";


    let completed = false;


    const checkCorrection =
        () => {

            if (completed) {
                return;
            }


            const correct =
                LessonEngine
                    .isTextAnswerCorrect(
                        input.value,
                        answer,
                        acceptedAnswers
                    );


            feedback.classList.remove(
                "error",
                "success"
            );


            input.classList.remove(
                "wrong",
                "correct"
            );


            if (!correct) {

                feedback.textContent =
                    "Not yet. Enter the correct answer shown above.";


                feedback.classList.add(
                    "error"
                );


                input.classList.add(
                    "wrong"
                );


                input.focus();


                input.select();


                return;
            }


            completed = true;


            input.disabled =
                true;


            button.disabled =
                true;


            input.classList.add(
                "correct"
            );


            feedback.textContent =
                "Correct. Now you can continue.";


            feedback.classList.add(
                "success"
            );


            showNagisaCorrect();


            playCorrectSound();


            addNextButton();

        };


    button.onclick =
        checkCorrection;


    input.addEventListener(
        "keydown",
        event => {

            if (event.key === "Enter") {

                event.preventDefault();

                checkCorrection();

            }

        }
    );


    task.appendChild(
        title
    );


    task.appendChild(
        input
    );


    task.appendChild(
        feedback
    );


    task.appendChild(
        button
    );


    elements.lessonCard.appendChild(
        task
    );


    input.focus();

}


/* ===================================
   NEXT
=================================== */

function addNextButton() {

    const button =
        document.createElement(
            "button"
        );


    button.className =
        "primary-button";


    button.textContent =
        LessonEngine.isLastStep()
            ? "Finish"
            : "Continue";


    button.onclick =
        () => {

            if (
                LessonEngine.isLastStep()
            ) {

                completeCurrentLevel();

            } else {

                LessonEngine.next();

                renderLesson();

            }

        };


    elements.lessonCard
        .appendChild(
            button
        );

}


/* ===================================
   HEARTS
=================================== */

async function spendHeart() {

    if (
        state.game.player.hearts
        <= 0
    ) {

        showNoHeartsModal();

        return;

    }


    try {

        const response =
            await apiFetch(
                "/api/player/hearts/spend",
                {
                    method: "POST"
                }
            );


        if (!response.ok) {
            return;
        }


        const data =
            await response.json();


        state.game.progress =
            data.progress;


        state.game.player.hearts =
            data.progress.hearts;


        renderHeader();


        if (
            state.game.player.hearts
            <= 0
        ) {

            showNoHeartsModal();

        }

    } catch (error) {

        console.error(
            error
        );

    }

}


function showNoHeartsModal() {

    elements.noHeartsModal
        .classList.remove(
            "hidden"
        );

}


elements.restoreHeartsButton.onclick =
    async () => {

        try {

            const response =
                await apiFetch(
                    "/api/player/hearts/restore",
                    {
                        method: "POST"
                    }
                );


            const data =
                await response.json();


            state.game.progress =
                data.progress;


            state.game.player.hearts =
                data.progress.hearts;


            renderHeader();


            elements.noHeartsModal
                .classList.add(
                    "hidden"
                );

        } catch (error) {

            console.error(
                error
            );

        }

    };


/* ===================================
   COMPLETE
=================================== */

async function completeCurrentLevel() {

    const result =
        LessonEngine.getResult();


    if (
        state.currentLevel.boss
    ) {

        await completeBoss(
            result
        );

        return;

    }


    try {

        const response =
            await apiFetch(
                `/api/levels/${state.currentLevel.id}/complete`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        attempts: LessonEngine.getAttempts()
                    })
                }
            );


        if (!response.ok) {
            throw new Error(
                "Level completion failed."
            );
        }


        const data =
            await response.json();


        state.game.progress =
            data.progress;


        syncPlayerFromProgress();


        showResultModal(
            result,
            state.currentLevel.xp,
            false
        );


    } catch (error) {

        console.error(
            error
        );

    }

}


/* ===================================
   BOSS
=================================== */

async function completeBoss(
    result
) {

    try {

        const response =
            await apiFetch(
                `/api/levels/${state.currentLevel.id}/boss-result`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            {
                                correct_answers:
                                    result.correct,

                                total_answers:
                                    result.total,

                                attempts:
                                    LessonEngine.getAttempts()
                            }
                        )
                }
            );


        const data =
            await response.json();


        if (
            !data.success
        ) {

            showBossFailure(
                data.result
            );

            return;

        }


        state.game.progress =
            data.progress;


        syncPlayerFromProgress();


        showResultModal(
            data.result,
            state.currentLevel.xp,
            true
        );


    } catch (error) {

        console.error(
            error
        );

    }

}


function showBossFailure(
    result
) {

    elements.resultEmoji.textContent =
        "😾";


    elements.resultLabel.textContent =
        "BOSS DEFEATED YOU";


    elements.resultTitle.textContent =
        "Try again.";


    elements.resultScore.textContent =
        `${result.correct_answers} / ${result.total_answers}`;


    elements.resultRank.textContent =
        result.rank;


    elements.rewardText.textContent =
        `${result.percentage}% — you need 70%`;


    elements.continueButton.textContent =
        "Try Again";


    elements.completeModal
        .classList.remove(
            "hidden"
        );


    elements.continueButton.onclick =
        () => {

            elements.completeModal
                .classList.add(
                    "hidden"
                );


            state.heartsSpentThisLevel =
                0;


            LessonEngine.start(
                state.currentLevel
            );


            showNagisa(
                "One more try. I know you can do it."
            );


            renderLesson();

        };

}


/* ===================================
   RESULT MODAL
=================================== */

function showResultModal(
    result,
    xp,
    boss
) {

    const correct =
        result.correct ??
        result.correct_answers ??
        0;


    const total =
        result.total ??
        result.total_answers ??
        0;

    elements.resultEmoji.textContent =
        boss
            ? getRankEmoji(
                result.rank
            )
            : "😺";


    elements.resultLabel.textContent =
        boss
            ? "BOSS DEFEATED"
            : "LEVEL COMPLETE";


    elements.resultTitle.textContent =
        getResultTitle(
            result,
            boss
        );


    elements.resultScore.textContent =
        `${correct} / ${total}`;


    elements.resultRank.textContent =
        result.rank;


    elements.rewardText.textContent =
        `+${xp} XP`;


    elements.continueButton.textContent =
        "Continue";


    elements.completeModal
        .classList.remove(
            "hidden"
        );


    elements.continueButton.onclick =
        () => {

            elements.completeModal
                .classList.add(
                    "hidden"
                );


            closeLesson();

        };

}


function getRankEmoji(
    rank
) {

    switch (rank) {

        case "S":
            return "👑";

        case "A":
            return "😎";

        case "B":
            return "😺";

        case "C":
            return "🙂";

        default:
            return "😾";

    }

}


function getResultTitle(
    result,
    boss
) {

    if (!boss) {

        if (result.percentage >= 90) {
            return "Excellent!";
        }

        if (result.percentage >= 75) {
            return "Great job!";
        }

        return "Nice work!";

    }


    switch (result.rank) {

        case "S":
            return "Perfect victory!";

        case "A":
            return "Amazing battle!";

        case "B":
            return "Strong victory!";

        default:
            return "You survived!";

    }

}


/* ===================================
   GRAMMAR HELP
=================================== */

function closeGrammarHelp() {

    elements.grammarHelpModal
        .classList.add(
            "hidden"
        );


    elements.grammarHelpButton
        .focus?.();

}


function openGrammarHelp() {

    const help =
        state.currentLevel
            ?.grammar_help;


    if (!help) {
        return;
    }


    elements.grammarHelpTitle.textContent =
        help.title;

    elements.grammarHelpSummary.textContent =
        help.summary;

    elements.grammarHelpRules.innerHTML = "";
    elements.grammarHelpExamples.innerHTML = "";


    help.rules.forEach(
        rule => {

            const item =
                document.createElement(
                    "li"
                );

            item.textContent = rule;

            elements.grammarHelpRules
                .appendChild(item);

        }
    );


    help.examples.forEach(
        example => {

            const card =
                document.createElement(
                    "div"
                );

            const english =
                document.createElement(
                    "div"
                );

            const russian =
                document.createElement(
                    "div"
                );


            card.className =
                "grammar-example";

            english.className =
                "grammar-example-en";

            russian.className =
                "grammar-example-ru";

            english.textContent =
                example.en;

            russian.textContent =
                example.ru;

            card.appendChild(english);
            card.appendChild(russian);

            elements.grammarHelpExamples
                .appendChild(card);

        }
    );


    elements.grammarHelpModal
        .classList.remove(
            "hidden"
        );


    elements.closeGrammarHelp
        .focus?.();

}


elements.grammarHelpButton.onclick =
    openGrammarHelp;


elements.closeGrammarHelp.onclick =
    closeGrammarHelp;


elements.grammarHelpModal.onclick =
    event => {

        if (
            event.target ===
            elements.grammarHelpModal
        ) {
            closeGrammarHelp();
        }

    };


/* ===================================
   NAVIGATION
=================================== */

function closeLesson() {

    AudioEngine.stop();

    closeGrammarHelp();


    elements.lessonScreen
        .classList.remove(
            "active"
        );


    elements.mapScreen
        .classList.add(
            "active"
        );


    const progressLocationId =
        Math.ceil(
            state.game.progress
                .current_level / 50
        );


    openLocation(
        getLocation(progressLocationId)
            ? progressLocationId
            : state.currentLocation.id
    );


    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });

}


elements.backToMap.onclick =
    closeLesson;


/* ===================================
   NAGISA
=================================== */

function showNagisa(
    message
) {

    elements.nagisaText.textContent =
        message;


    elements.nagisaBubble
        ?.animate?.(
            [
                {
                    opacity: 0,
                    transform:
                        "translateY(5px)"
                },
                {
                    opacity: 1,
                    transform:
                        "translateY(0)"
                }
            ],
            {
                duration: 220,
                easing: "ease-out"
            }
        );

}


function showNagisaCorrect() {

    const messages = [
        "Nice! 😺",
        "Correct!",
        "Very good!",
        "You got it!",
        "My whiskers approve.",
        "That's the one!"
    ];


    showNagisa(
        messages[
            Math.floor(
                Math.random() *
                messages.length
            )
        ]
    );


    elements.nagisaCharacter
        .classList.remove(
            "wrong"
        );


    elements.nagisaCharacter
        .classList.add(
            "correct"
        );


    setTimeout(
        () => {

            elements.nagisaCharacter
                .classList.remove(
                    "correct"
                );

        },
        600
    );

}


function showNagisaWrong() {

    const messages = [
        "Hmm... nope.",
        "Almost!",
        "English is weird.",
        "Let's learn from that.",
        "My whiskers are disappointed.",
        "Not quite."
    ];


    showNagisa(
        messages[
            Math.floor(
                Math.random() *
                messages.length
            )
        ]
    );


    elements.nagisaCharacter
        .classList.remove(
            "correct"
        );


    elements.nagisaCharacter
        .classList.add(
            "wrong"
        );


    setTimeout(
        () => {

            elements.nagisaCharacter
                .classList.remove(
                    "wrong"
                );

        },
        450
    );

}


function getIntroMessage() {

    const messages = [
        "Let's do this!",
        "Okay, human. Impress me.",
        "English time!",
        "Don't panic. I have snacks.",
        "Let's see what you've got."
    ];


    return messages[
        Math.floor(
            Math.random() *
            messages.length
        )
    ];

}


/* ===================================
   SOUND
=================================== */

function playCorrectSound() {

    if (
        !("AudioContext" in window) &&
        !("webkitAudioContext" in window)
    ) {
        return;
    }


    try {

        const AudioContext =
            window.AudioContext ||
            window.webkitAudioContext;


        const context =
            new AudioContext();


        const oscillator =
            context.createOscillator();


        const gain =
            context.createGain();


        oscillator.type =
            "sine";


        oscillator.frequency.value =
            720;


        gain.gain.setValueAtTime(
            0.0001,
            context.currentTime
        );


        gain.gain.exponentialRampToValueAtTime(
            0.08,
            context.currentTime + 0.01
        );


        gain.gain.exponentialRampToValueAtTime(
            0.0001,
            context.currentTime + 0.16
        );


        oscillator.connect(
            gain
        );


        gain.connect(
            context.destination
        );


        oscillator.start();

        oscillator.stop(
            context.currentTime + 0.17
        );

    } catch (error) {

        console.debug(
            "Audio unavailable",
            error
        );

    }

}


/* ===================================
   SYNC
=================================== */

function syncPlayerFromProgress() {

    state.game.player.xp =
        state.game.progress.xp;


    state.game.player.streak =
        state.game.progress.streak;


    state.game.player.hearts =
        state.game.progress.hearts;


    state.game.player.level =
        state.game.progress.player_level;


    state.game.player.level_xp =
        state.game.progress.level_xp;


    state.game.player.level_xp_required =
        state.game.progress
            .level_xp_required;


    state.game.player.level_progress_percent =
        state.game.progress
            .level_progress_percent;


    renderHeader();

}


/* ===================================
   START
=================================== */

init();
