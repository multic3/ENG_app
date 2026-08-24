const CACHE_NAME =
    "english-rpg-v9";


const APP_FILES = [
    "/",
    "/static/index.html",
    "/static/styles.css",
    "/static/app.js",
    "/static/lesson-engine.js",
    "/static/map-engine.js",
    "/static/audio-engine.js",
    "/static/assets/nagisa-pixel.png",
    "/static/manifest.json",
    "/sw.js"
];


self.addEventListener(
    "install",
    event => {

        event.waitUntil(
            caches
                .open(
                    CACHE_NAME
                )
                .then(
                    cache =>
                        cache.addAll(
                            APP_FILES
                        )
                )
        );


        self.skipWaiting();

    }
);


self.addEventListener(
    "activate",
    event => {

        event.waitUntil(

            caches.keys()
                .then(
                    names =>
                        Promise.all(
                            names
                                .filter(
                                    name =>
                                        name !==
                                        CACHE_NAME
                                )
                                .map(
                                    name =>
                                        caches.delete(
                                            name
                                        )
                                )
                        )
                )

        );


        self.clients.claim();

    }
);


self.addEventListener(
    "fetch",
    event => {

    if (
        event.request.method !==
        "GET" ||
        new URL(
            event.request.url
        ).origin !== self.location.origin
        ) {
            return;
        }


        event.respondWith(

            fetch(
                event.request
            )
                .then(
                    response => {

                        if (!response.ok) {
                            return response;
                        }

                        const copy =
                            response.clone();


                        caches.open(
                            CACHE_NAME
                        ).then(
                            cache => {

                                cache.put(
                                    event.request,
                                    copy
                                );

                            }
                        );


                        return response;

                    }
                )
                .catch(
                    () =>
                        caches.match(
                            event.request
                        )
                )

        );

    }
);
