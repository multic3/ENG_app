const fs = require("fs");
const vm = require("vm");


function createElement() {
    const classes = new Set();

    return {
        style: {},
        innerHTML: "",
        attributes: {},
        classList: {
            add(name) {
                classes.add(name);
            },
            contains(name) {
                return classes.has(name);
            }
        },
        setAttribute(name, value) {
            this.attributes[name] = value;
        },
        addEventListener() {}
    };
}


const document = {
    createElement
};
const context = {
    document
};


vm.createContext(context);
vm.runInContext(
    `${fs.readFileSync(
        "frontend/map-engine.js",
        "utf8"
    )}; this.mapEngine = MapEngine;`,
    context
);


const container = {
    innerHTML: "",
    children: [],
    appendChild(child) {
        this.children.push(child);
    }
};


context.mapEngine.render(
    container,
    {id: 2},
    {
        current_level: 11,
        completed_levels: []
    },
    () => {}
);


if (
    !container.children[0]
        .innerHTML.includes("11")
) {
    throw new Error(
        "Location 2 did not start at global level 11"
    );
}


if (
    !container.children[9]
        .innerHTML.includes("20")
) {
    throw new Error(
        "Location 2 boss was not global level 20"
    );
}


if (
    container.children[0]
        .attributes["aria-label"] !==
    "Level 11"
) {
    throw new Error(
        "Global level accessibility label is incorrect"
    );
}


const roadPath = fs.readFileSync(
    "frontend/index.html",
    "utf8"
);

for (
    const position of context.mapEngine.positions
) {
    const x = position.x * 4;
    const y = position.y * 9;
    const endpoint = new RegExp(
        `(?:M|C[^\\n]*\\s)${x}\\s+${y}(?:\\s|$)`
    );

    if (!endpoint.test(roadPath)) {
        throw new Error(
            `Level node ${x},${y} is not anchored to the road`
        );
    }
}


console.log(
    "OK map displays global levels 1-100"
);
