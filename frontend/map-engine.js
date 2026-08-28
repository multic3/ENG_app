const MapEngine = {
    pointsPerLocation: 50,

    positions: Array.from({ length: 50 }, (_, index) => {
        const row = Math.floor(index / 5);
        const slot = index % 5;
        const xSlots = row % 2 === 0
            ? [50, 34, 22, 34, 50]
            : [50, 66, 78, 66, 50];
        return {
            x: xSlots[slot],
            y: 97 - (index * (94 / 49))
        };
    }),

    getNagisaPosition(location, progress) {
        const startPoint =
            ((location.id - 1) * this.pointsPerLocation) + 1;
        const currentPoint = progress.current_level || 1;
        const localIndex = Math.min(
            this.pointsPerLocation - 1,
            Math.max(0, currentPoint - startPoint)
        );
        const pointPosition = this.positions[localIndex];
        return {
            x: pointPosition.x + (pointPosition.x >= 50 ? -10 : 10),
            y: pointPosition.y,
            level: startPoint + localIndex
        };
    },

    addMapPath(container) {
        const map = container.parentElement;
        const width = map?.clientWidth || 400;
        const height = map?.clientHeight || 2600;
        const namespace = "http://www.w3.org/2000/svg";
        const svg = document.createElementNS(namespace, "svg");
        const path = document.createElementNS(namespace, "polyline");
        const points = this.positions
            .map(position => (
                `${position.x * width / 100},${position.y * height / 100}`
            ))
            .join(" ");

        svg.classList.add("map-path-svg");
        svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
        svg.setAttribute("preserveAspectRatio", "none");
        svg.setAttribute("aria-hidden", "true");
        path.setAttribute("points", points);
        svg.appendChild(path);
        container.appendChild(svg);
    },

    addStageLabels(container) {
        const labels = [
            "1–10 · Знакомство",
            "11–20 · Практика",
            "21–30 · Контекст",
            "31–40 · Самостоятельно",
            "41–50 · Повторение"
        ];
        labels.forEach((text, stageIndex) => {
            const label = document.createElement("span");
            label.className = "map-stage-label";
            label.textContent = text;
            label.style.top = `${this.positions[stageIndex * 10].y}%`;
            container.appendChild(label);
        });
    },

    render(container, location, progress, onLevelClick) {
        container.innerHTML = "";
        const completed = progress.completed_levels || [];
        const currentPoint = progress.current_level || 1;
        const startPoint = ((location.id - 1) * this.pointsPerLocation) + 1;

        this.addMapPath(container);
        this.addStageLabels(container);

        for (let index = 0; index < this.pointsPerLocation; index++) {
            const localPoint = index + 1;
            const globalPoint = startPoint + index;
            const position = this.positions[index];
            const node = document.createElement("button");
            const completedPoint = completed.includes(globalPoint);
            const current = globalPoint === currentPoint;
            const unlocked = globalPoint <= currentPoint;

            node.className = "level-node";
            node.style.left = `${position.x}%`;
            node.style.top = `${position.y}%`;
            if (completedPoint) node.classList.add("completed");
            if (current && !completedPoint) node.classList.add("current");
            if (!unlocked) node.classList.add("locked");
            if (localPoint === this.pointsPerLocation) node.classList.add("boss");
            node.setAttribute(
                "aria-label",
                `Point ${globalPoint}${!unlocked ? ", locked" : completedPoint ? ", completed" : ""}`
            );

            const icon = localPoint === this.pointsPerLocation
                ? "👑"
                : completedPoint ? "⭐" : !unlocked ? "🔒" : "";
            node.innerHTML = `
                <span class="level-number">${localPoint}</span>
                ${icon ? `<span class="level-icon">${icon}</span>` : ""}
            `;
            if (unlocked) {
                node.addEventListener("click", () => onLevelClick(globalPoint));
            }
            container.appendChild(node);
        }
    }
};
