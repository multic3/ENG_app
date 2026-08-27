const MapEngine = {

    positions: [
        { x: 50, y: 92 },
        { x: 34, y: 82 },
        { x: 34, y: 71 },
        { x: 60, y: 62 },
        { x: 65, y: 51 },
        { x: 43, y: 45 },
        { x: 42, y: 34 },
        { x: 58, y: 28 },
        { x: 55, y: 17 },
        { x: 50, y: 7 }
    ],


    getNagisaPosition(
        location,
        progress
    ) {

        const startLevel =
            ((location.id - 1) * 10) + 1;

        const currentLevel =
            progress.current_level || 1;

        const localIndex = Math.min(
            9,
            Math.max(
                0,
                currentLevel - startLevel
            )
        );

        const levelPosition =
            this.positions[localIndex];

        const sideOffset =
            levelPosition.x >= 50
                ? -11
                : 11;


        return {
            x: levelPosition.x + sideOffset,
            y: levelPosition.y,
            level: startLevel + localIndex
        };

    },


    render(
        container,
        location,
        progress,
        onLevelClick
    ) {

        container.innerHTML = "";


        const completed =
            progress.completed_levels || [];


        const currentLevel =
            progress.current_level || 1;


        for (
            let index = 0;
            index < 10;
            index++
        ) {

            const localLevel =
                index + 1;


            const globalLevel =
                (
                    (location.id - 1) * 10
                ) + localLevel;


            const position =
                this.positions[index];


            const node =
                document.createElement(
                    "button"
                );


            node.className =
                "level-node";


            node.style.left =
                `${position.x}%`;

            node.style.top =
                `${position.y}%`;


            const completedLevel =
                completed.includes(
                    globalLevel
                );


            const current =
                globalLevel ===
                currentLevel;


            const unlocked =
                globalLevel <=
                currentLevel;


            if (
                completedLevel
            ) {

                node.classList.add(
                    "completed"
                );

            }


            if (
                current &&
                !completedLevel
            ) {

                node.classList.add(
                    "current"
                );

            }


            if (!unlocked) {

                node.classList.add(
                    "locked"
                );

            }


            node.setAttribute(
                "aria-label",
                `Level ${globalLevel}${
                    !unlocked
                        ? ", locked"
                        : completedLevel
                            ? ", completed"
                            : ""
                }`
            );


            if (localLevel === 10) {

                node.classList.add(
                    "boss"
                );

            }


            let icon = "";


            if (localLevel === 10) {

                icon = "👑";

            } else if (
                completedLevel
            ) {

                icon = "⭐";

            } else if (
                !unlocked
            ) {

                icon = "🔒";

            }


            node.innerHTML = `
                <span class="level-number">
                    ${globalLevel}
                </span>

                ${
                    icon
                        ? `
                            <span
                                class="level-icon"
                            >
                                ${icon}
                            </span>
                        `
                        : ""
                }
            `;


            if (unlocked) {

                node.addEventListener(
                    "click",
                    () => {

                        onLevelClick(
                            globalLevel
                        );

                    }
                );

            }


            container.appendChild(
                node
            );

        }

    }

};
