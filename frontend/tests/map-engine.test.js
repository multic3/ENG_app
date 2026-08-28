const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

function createElement() {
    const classes = new Set();
    return {
        style: {},
        innerHTML: "",
        textContent: "",
        className: "",
        attributes: {},
        classList: {
            add(name) { classes.add(name); },
            contains(name) { return classes.has(name); }
        },
        setAttribute(name, value) { this.attributes[name] = value; },
        children: [],
        addEventListener() {},
        appendChild(child) { this.children.push(child); }
    };
}

const context = {
    document: {
        createElement,
        createElementNS() { return createElement(); }
    }
};
vm.createContext(context);
vm.runInContext(
    `${fs.readFileSync("frontend/map-engine.js", "utf8")}; this.mapEngine = MapEngine;`,
    context
);

const container = {
    innerHTML: "",
    children: [],
    appendChild(child) { this.children.push(child); }
};
context.mapEngine.render(
    container,
    { id: 2 },
    { current_level: 51, completed_levels: [] },
    () => {}
);

const nodes = container.children.filter(child => child.className === "level-node");
const paths = container.children.filter(child => child.classList.contains("map-path-svg"));
const labels = container.children.filter(child => child.className === "map-stage-label");

assert.strictEqual(context.mapEngine.positions.length, 50);
assert.strictEqual(nodes.length, 50);
assert.strictEqual(paths.length, 1);
assert.strictEqual(paths[0].children.length, 1);
assert.strictEqual(labels.length, 5);
assert.match(nodes[0].innerHTML, />1</);
assert.match(nodes[49].innerHTML, />50</);
assert.strictEqual(nodes[0].attributes["aria-label"], "Point 51");
assert.strictEqual(nodes[49].attributes["aria-label"], "Point 100, locked");
assert.ok(nodes[49].classList.contains("boss"));

const start = context.mapEngine.getNagisaPosition({ id: 2 }, { current_level: 51 });
const later = context.mapEngine.getNagisaPosition({ id: 2 }, { current_level: 76 });
assert.strictEqual(start.level, 51);
assert.strictEqual(later.level, 76);
assert.notDeepStrictEqual({ x: start.x, y: start.y }, { x: later.x, y: later.y });

const html = fs.readFileSync("frontend/index.html", "utf8");
assert.ok(html.includes("beach-decoration"));

console.log("OK map displays 50 points, five stages, road and moving Nagisa");
