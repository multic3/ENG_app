const assert = require("assert");
const fs = require("fs");
const path = require("path");


const root = path.resolve(__dirname, "../..");
const levelsData = JSON.parse(
    fs.readFileSync(
        path.join(root, "backend/app/levels.json"),
        "utf8"
    )
);

const availableLevels = levelsData.locations
    .flatMap(location => location.levels);


assert.strictEqual(
    availableLevels.length,
    20,
    "The MVP should expose grammar help for levels 1-20"
);


availableLevels.forEach(level => {
    const help = level.grammar_help;

    assert.ok(help, `Level ${level.id} has no grammar help`);
    assert.ok(help.title, `Level ${level.id} has no help title`);
    assert.ok(help.summary, `Level ${level.id} has no help summary`);
    assert.ok(
        Array.isArray(help.rules) && help.rules.length >= 2,
        `Level ${level.id} needs at least two short rules`
    );
    assert.ok(
        Array.isArray(help.examples) && help.examples.length >= 2,
        `Level ${level.id} needs at least two examples`
    );

    help.examples.forEach(example => {
        assert.ok(example.en && example.ru);
    });
});


const indexHtml = fs.readFileSync(
    path.join(root, "frontend/index.html"),
    "utf8"
);
const manifest = JSON.parse(
    fs.readFileSync(
        path.join(root, "frontend/manifest.json"),
        "utf8"
    )
);


assert.match(indexHtml, /id="grammarHelpButton"/);
assert.match(indexHtml, /nagisa-app-icon-180\.png/);
assert.ok(
    manifest.icons.every(icon =>
        icon.src.includes("nagisa-app-icon-")
    ),
    "The PWA manifest must use the Nagisa icon set"
);


for (const size of [180, 192, 512, 1024]) {
    const icon = fs.readFileSync(
        path.join(
            root,
            `frontend/assets/nagisa-app-icon-${size}.png`
        )
    );

    assert.strictEqual(
        icon.readUInt32BE(16),
        size,
        `Icon width must be ${size}`
    );
    assert.strictEqual(
        icon.readUInt32BE(20),
        size,
        `Icon height must be ${size}`
    );
}


console.log(
    "OK levels 1-20 have Russian grammar help and Nagisa icons"
);
