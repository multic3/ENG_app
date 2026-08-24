const LessonEngine = {

    level: null,

    currentStep: 0,

    correctAnswers: 0,

    totalAnswers: 0,

    answered: false,


    start(level) {

        this.level = level;

        this.currentStep = 0;

        this.correctAnswers = 0;

        this.totalAnswers = 0;

        this.answered = false;
    },


    getCurrentStep() {

        if (!this.level) {
            return null;
        }

        return this.level.steps[
            this.currentStep
        ];
    },


    getStepCount() {

        if (!this.level) {
            return 0;
        }

        return this.level.steps.length;
    },


    getCurrentStepNumber() {

        return this.currentStep + 1;
    },


    isLastStep() {

        return (
            this.currentStep
            >=
            this.getStepCount() - 1
        );
    },


    answerChoice(
        selected,
        correct
    ) {

        if (this.answered) {
            return false;
        }

        this.answered = true;

        this.totalAnswers++;

        const success =
            selected === correct;

        if (success) {
            this.correctAnswers++;
        }

        return success;
    },


    answerText(
        value,
        answer,
        acceptedAnswers = []
    ) {

        if (this.answered) {
            return false;
        }

        this.answered = true;

        this.totalAnswers++;

        const success =
            this.isTextAnswerCorrect(
                value,
                answer,
                acceptedAnswers
            );

        if (success) {
            this.correctAnswers++;
        }

        return success;
    },


    isTextAnswerCorrect(
        value,
        answer,
        acceptedAnswers = []
    ) {

        const normalizedValue =
            this.normalizeText(
                value
            );

        const validAnswers = [
            answer,
            ...acceptedAnswers
        ]
            .filter(
                item =>
                    typeof item ===
                    "string"
            )
            .map(
                item =>
                    this.normalizeText(
                        item
                    )
            );

        return validAnswers.includes(
            normalizedValue
        );
    },


    normalizeText(value) {

        return String(
            value ?? ""
        )
            .trim()
            .toLowerCase()
            .replace(/[‘’]/g, "'")
            .replace(/\s+/g, " ")
            .replace(/[.!?]+$/g, "");
    },


    skipCurrentStep() {

        if (this.answered) {
            return false;
        }

        this.answered = true;

        return true;
    },


    answerSpeaking(
        transcript,
        expected
    ) {

        if (this.answered) {
            return false;
        }

        this.answered = true;

        this.totalAnswers++;

        const normalizedTranscript =
            transcript
                .toLowerCase()
                .replace(/[.,!?]/g, "")
                .trim();

        const normalizedExpected =
            expected
                .toLowerCase()
                .replace(/[.,!?]/g, "")
                .trim();

        const transcriptWords =
            normalizedTranscript
                .split(/\s+/)
                .filter(Boolean);

        const expectedWords =
            normalizedExpected
                .split(/\s+/)
                .filter(Boolean);

        if (
            transcriptWords.length === 0 ||
            expectedWords.length === 0
        ) {
            return false;
        }

        const matchingWords =
            expectedWords.filter(
                word =>
                    transcriptWords.includes(word)
            ).length;

        const score =
            matchingWords /
            expectedWords.length;

        const success =
            score >= 0.7;

        if (success) {
            this.correctAnswers++;
        }

        return success;
    },


    next() {

        this.currentStep++;

        this.answered = false;
    },


    getResult() {

        const percentage =
            this.totalAnswers === 0
                ? 0
                : Math.round(
                    (
                        this.correctAnswers /
                        this.totalAnswers
                    ) * 100
                );


        let rank = "F";


        if (percentage >= 95) {
            rank = "S";
        } else if (percentage >= 85) {
            rank = "A";
        } else if (percentage >= 75) {
            rank = "B";
        } else if (percentage >= 70) {
            rank = "C";
        }


        return {

            correct:
                this.correctAnswers,

            total:
                this.totalAnswers,

            percentage,

            rank,

            passed:
                percentage >= 70

        };
    }

};
