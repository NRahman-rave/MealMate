const accountButton =
    document.getElementById(
        "accountButton"
    );


const accountDropdown =
    document.getElementById(
        "accountDropdown"
    );


if (
    accountButton &&
    accountDropdown
) {

    accountButton.addEventListener(
        "click",
        function (event) {

            event.stopPropagation();


            accountDropdown
                .classList
                .toggle(
                    "show"
                );


            accountButton
                .classList
                .toggle(
                    "active"
                );

        }
    );


    document.addEventListener(
        "click",
        function (event) {

            if (
                !accountDropdown.contains(
                    event.target
                )

                &&

                !accountButton.contains(
                    event.target
                )
            ) {

                accountDropdown
                    .classList
                    .remove(
                        "show"
                    );


                accountButton
                    .classList
                    .remove(
                        "active"
                    );

            }

        }
    );

}


/* =========================================================
MOBILE MENU
========================================================= */

const mobileMenuButton =
    document.getElementById(
        "mobileMenuButton"
    );


const mobileMenu =
    document.getElementById(
        "mobileMenu"
    );


if (
    mobileMenuButton &&
    mobileMenu
) {

    mobileMenuButton.addEventListener(
        "click",
        function () {

            mobileMenu
                .classList
                .toggle(
                    "show"
                );


            const icon =
                mobileMenuButton
                    .querySelector(
                        "i"
                    );


            if (!icon) {
                return;
            }


            icon.classList.toggle(
                "fa-bars",
                !mobileMenu.classList.contains(
                    "show"
                )
            );


            icon.classList.toggle(
                "fa-xmark",
                mobileMenu.classList.contains(
                    "show"
                )
            );

        }
    );

}


/* =========================================================
MOBILE ACCOUNT
========================================================= */

const mobileAccountButton =
    document.getElementById(
        "mobileAccountButton"
    );


const mobileAccountOptions =
    document.getElementById(
        "mobileAccountOptions"
    );


if (
    mobileAccountButton &&
    mobileAccountOptions
) {

    mobileAccountButton.addEventListener(
        "click",
        function () {

            mobileAccountOptions
                .classList
                .toggle(
                    "show"
                );

        }
    );

}


/* =========================================================
WAIT
========================================================= */

function wait(ms) {

    return new Promise(
        function (resolve) {

            setTimeout(
                resolve,
                ms
            );

        }
    );

}


function waitForFrames() {

    return new Promise(
        function (resolve) {

            requestAnimationFrame(
                function () {

                    requestAnimationFrame(
                        resolve
                    );

                }
            );

        }
    );

}


/* =========================================================
NEW HERO LETTER CREATOR
========================================================= */

function createAnimatedLetters(
    element,
    text,
    startImmediately = true
) {

    if (!element) {
        return;
    }


    element.innerHTML = "";


    const characters =
        Array.from(
            text
        );


    let visibleLetterIndex =
        0;


    characters.forEach(
        function (character) {


            if (character === " ") {

                const space =
                    document.createElement(
                        "span"
                    );


                space.className =
                    "title-space";


                space.innerHTML =
                    "&nbsp;";


                element.appendChild(
                    space
                );


                return;

            }


            const letter =
                document.createElement(
                    "span"
                );


            letter.className =
                "title-letter";


            letter.textContent =
                character;


            letter.style.setProperty(
                "--letter-index",
                visibleLetterIndex
            );


            /*
            Alternating angle gives the
            exact scattered/reforming feel.
            */

            const angle =
                visibleLetterIndex % 2 === 0
                    ? "-8deg"
                    : "8deg";


            letter.style.setProperty(
                "--letter-angle",
                angle
            );


            element.appendChild(
                letter
            );


            visibleLetterIndex++;

        }
    );


    if (startImmediately) {

        requestAnimationFrame(
            function () {

                element
                    .querySelectorAll(
                        ".title-letter"
                    )
                    .forEach(
                        function (letter) {

                            letter.classList.add(
                                "title-letter-in"
                            );

                        }
                    );

            }
        );

    }

}


/* =========================================================
HERO TITLE REFERENCES
========================================================= */

const heroMainTitle =
    document.getElementById(
        "heroMainTitle"
    );


const changingHeroText =
    document.getElementById(
        "changingHeroText"
    );


/* =========================================================
INITIALISE HERO TITLE LETTERS

They stay hidden until homepage animation starts.
========================================================= */

createAnimatedLetters(
    heroMainTitle,
    "Good Food",
    false
);


createAnimatedLetters(
    changingHeroText,
    "Should Be Shared",
    false
);


/* =========================================================
START A LETTER BUILD
========================================================= */

function animateLettersIn(
    element
) {

    if (!element) {
        return;
    }


    const letters =
        element.querySelectorAll(
            ".title-letter"
        );


    letters.forEach(
        function (letter) {

            letter.classList.remove(
                "title-letter-out"
            );


            letter.classList.remove(
                "title-letter-in"
            );

        }
    );


    void element.offsetWidth;


    letters.forEach(
        function (letter) {

            letter.classList.add(
                "title-letter-in"
            );

        }
    );

}


/* =========================================================
ANIMATE LETTERS OUT
========================================================= */

function animateLettersOut(
    element
) {

    if (!element) {

        return Promise.resolve();

    }


    const letters =
        Array.from(
            element.querySelectorAll(
                ".title-letter"
            )
        );


    letters.forEach(
        function (letter) {

            letter.classList.remove(
                "title-letter-in"
            );


            letter.classList.add(
                "title-letter-out"
            );

        }
    );


    return wait(
        900
    );

}


/* =========================================================
CHANGING HERO TEXT

IMPORTANT:
USER REQUESTED 5000ms
========================================================= */

const heroTexts = [

    "Should Be Shared",

    "With MealMate"

];


let currentHeroText =
    0;


let heroTextTimer =
    null;


let heroTextChanging =
    false;


async function changeHeroText() {

    if (
        !changingHeroText ||
        heroTextChanging
    ) {

        return;

    }


    heroTextChanging =
        true;


    /* OLD LETTERS VANISH */

    await animateLettersOut(
        changingHeroText
    );


    currentHeroText =
        (
            currentHeroText + 1
        )
        %
        heroTexts.length;


    const newText =
        heroTexts[
            currentHeroText
        ];


    changingHeroText
        .classList
        .toggle(
            "sharebite-text",
            currentHeroText === 1
        );


    /* CREATE NEW HIDDEN LETTERS */

    createAnimatedLetters(
        changingHeroText,
        newText,
        false
    );


    await wait(
        50
    );


    /* NEW LETTERS REFORM */

    animateLettersIn(
        changingHeroText
    );


    heroTextChanging =
        false;

}


/* =========================================================
START CHANGING TEXT

5000ms
========================================================= */

function startHeroTextRotation() {

    if (
        !changingHeroText ||
        heroTextTimer
    ) {

        return;

    }


    heroTextTimer =
        setInterval(
            changeHeroText,
            5000
        );

}


/* =========================================================
LOGO FLY
========================================================= */

function flyToTarget(
    source,
    target,
    delay = 0,
    duration = 900,
    lift = true,
    startRotation = 0,
    endRotation = 0
) {

    if (
        !source ||
        !target
    ) {

        return null;

    }


    const sourceRect =
        source.getBoundingClientRect();


    const targetRect =
        target.getBoundingClientRect();


    if (
        !sourceRect.width ||
        !sourceRect.height ||
        !targetRect.width ||
        !targetRect.height
    ) {

        return null;

    }


    const sourceX =
        sourceRect.left +
        sourceRect.width / 2;


    const sourceY =
        sourceRect.top +
        sourceRect.height / 2;


    const targetX =
        targetRect.left +
        targetRect.width / 2;


    const targetY =
        targetRect.top +
        targetRect.height / 2;


    const moveX =
        targetX -
        sourceX;


    const moveY =
        targetY -
        sourceY;


    const scale =
        Math.min(

            targetRect.width /
            sourceRect.width,

            targetRect.height /
            sourceRect.height

        );


    const liftAmount =
        lift
            ? -14
            : 0;


    return source.animate(

        [

            {

                offset:
                    0,

                opacity:
                    1,

                transform:
                    `
                    translate(0px,0px)
                    rotate(${startRotation}deg)
                    scale(1)
                    `

            },


            {

                offset:
                    0.2,

                opacity:
                    1,

                transform:
                    `
                    translate(
                        ${moveX * 0.12}px,
                        ${
                            moveY * 0.12 +
                            liftAmount
                        }px
                    )
                    rotate(${startRotation}deg)
                    scale(.96)
                    `

            },


            {

                offset:
                    0.55,

                opacity:
                    1,

                transform:
                    `
                    translate(
                        ${moveX * 0.55}px,
                        ${moveY * 0.55}px
                    )
                    rotate(
                        ${
                            startRotation +
                            (
                                endRotation -
                                startRotation
                            ) *
                            .55
                        }deg
                    )
                    scale(
                        ${
                            1 -
                            (
                                1 -
                                scale
                            ) *
                            .55
                        }
                    )
                    `

            },


            {

                offset:
                    0.82,

                opacity:
                    1,

                transform:
                    `
                    translate(
                        ${moveX * 0.82}px,
                        ${moveY * 0.82}px
                    )
                    rotate(
                        ${
                            startRotation +
                            (
                                endRotation -
                                startRotation
                            ) *
                            .82
                        }deg
                    )
                    scale(
                        ${
                            1 -
                            (
                                1 -
                                scale
                            ) *
                            .82
                        }
                    )
                    `

            },


            {

                offset:
                    1,

                opacity:
                    1,

                transform:
                    `
                    translate(
                        ${moveX}px,
                        ${moveY}px
                    )
                    rotate(${endRotation}deg)
                    scale(${scale})
                    `

            }

        ],

        {

            duration:
                duration,

            delay:
                delay,

            fill:
                "forwards",

            easing:
                "cubic-bezier(.22,.61,.36,1)"

        }

    );

}


/* =========================================================
HOMEPAGE ANIMATION

LOGO
↓
GOOD FOOD LETTER ANIMATION
↓
SHOULD BE SHARED LETTER ANIMATION
↓
PICTURE
↓
SMALL TEXT
↓
DESCRIPTION
↓
BUTTON
========================================================= */

let homepageSequenceStarted =
    false;


function startHomepageSequence() {

    if (homepageSequenceStarted) {

        return;

    }


    homepageSequenceStarted =
        true;


    const heroTitle =
        document.getElementById(
            "heroTitleReveal"
        );


    const heroPicture =
        document.getElementById(
            "heroPictureReveal"
        );


    const heroEyebrow =
        document.getElementById(
            "heroEyebrowReveal"
        );


    const heroDescription =
        document.getElementById(
            "heroDescriptionReveal"
        );


    const heroButtons =
        document.getElementById(
            "heroButtonsReveal"
        );


    const navbarItems =
        document.querySelectorAll(
            ".navbar-reveal"
        );


    setTimeout(
        function () {

            heroTitle
                ?.classList
                .add(
                    "sequence-visible"
                );


            animateLettersIn(
                heroMainTitle
            );


            setTimeout(
                function () {

                    animateLettersIn(
                        changingHeroText
                    );

                },

                650
            );


            setTimeout(
                startHeroTextRotation,
                1450
            );

        },

        100
    );


    setTimeout(
        function () {

            navbarItems.forEach(
                function (
                    item,
                    index
                ) {

                    setTimeout(
                        function () {

                            item.classList.add(
                                "navbar-visible"
                            );

                        },

                        index * 90
                    );

                }
            );

        },

        400
    );


    setTimeout(
        function () {

            heroPicture
                ?.classList
                .add(
                    "sequence-visible"
                );

        },

        1250
    );


    setTimeout(
        function () {

            heroEyebrow
                ?.classList
                .add(
                    "sequence-visible"
                );

        },

        1650
    );


    setTimeout(
        function () {

            heroDescription
                ?.classList
                .add(
                    "sequence-visible"
                );

        },

        1900
    );


    setTimeout(
        function () {

            heroButtons
                ?.classList
                .add(
                    "sequence-visible"
                );

        },

        2200
    );

}


/* =========================================================
SCROLL ANIMATION
========================================================= */

function setupScrollAnimations() {

    const elements =
        Array.from(
            document.querySelectorAll(
                ".scroll-reveal"
            )
        );


    elements.forEach(
        function (
            element,
            index
        ) {

            element.style.setProperty(
                "--scroll-delay",
                (
                    index % 3
                ) *
                90 +
                "ms"
            );

        }
    );


    const observer =
        new IntersectionObserver(

            function (
                entries,
                observerInstance
            ) {

                entries.forEach(
                    function (entry) {

                        if (
                            entry.isIntersecting
                        ) {

                            entry.target
                                .classList
                                .add(
                                    "scroll-visible"
                                );


                            observerInstance
                                .unobserve(
                                    entry.target
                                );

                        }

                    }
                );

            },

            {

                threshold:
                    0.13,

                rootMargin:
                    "0px 0px -45px 0px"

            }

        );


    elements.forEach(
        function (element) {

            observer.observe(
                element
            );

        }
    );

}


/* =========================================================
MAIN LOGO INTRO
========================================================= */

window.addEventListener(
    "load",
    async function () {


        const intro =
            document.getElementById(
                "logoIntro"
            );


        const introLogo =
            document.getElementById(
                "introLogo"
            );


        const navbarBrand =
            document.getElementById(
                "navbarBrand"
            );


        const introIcon =
            document.getElementById(
                "introLogoIcon"
            );


        const targetIcon =
            document.getElementById(
                "targetLogoIcon"
            );


        const introTagline =
            document.getElementById(
                "introTagline"
            );


        const targetTagline =
            document.getElementById(
                "targetTagline"
            );


        const introLetters =
            Array.from(
                document.querySelectorAll(
                    "[data-intro-letter]"
                )
            );


        const targetLetters =
            Array.from(
                document.querySelectorAll(
                    "[data-target-letter]"
                )
            );


        setupScrollAnimations();


        if (
            !intro ||
            !introLogo ||
            !navbarBrand ||
            introLetters.length !==
            targetLetters.length
        ) {

            document.body.classList.remove(
                "intro-active"
            );


            document.body.classList.add(
                "logo-arrived",
                "show-interface"
            );


            startHomepageSequence();


            return;

        }


        await wait(
            1750
        );


        introLogo.classList.add(
            "letters-finished"
        );


        await wait(
            220
        );


        intro.classList.add(
            "logo-moving"
        );


        introLetters.forEach(
            function (letter) {

                letter
                    .getAnimations()
                    .forEach(
                        function (animation) {

                            animation.cancel();

                        }
                    );


                letter.style.opacity =
                    "1";


                letter.style.transform =
                    "none";

            }
        );


        if (introIcon) {

            introIcon
                .getAnimations()
                .forEach(
                    function (animation) {

                        animation.cancel();

                    }
                );


            introIcon.style.opacity =
                "1";


            introIcon.style.transform =
                "rotate(-15deg)";

        }


        if (introTagline) {

            introTagline
                .getAnimations()
                .forEach(
                    function (animation) {

                        animation.cancel();

                    }
                );


            introTagline.style.opacity =
                "1";


            introTagline.style.transform =
                "none";

        }


        await waitForFrames();


        const animations =
            [];


        if (
            introIcon &&
            targetIcon
        ) {

            const animation =
                flyToTarget(

                    introIcon,

                    targetIcon,

                    0,

                    920,

                    true,

                    -15,

                    -15

                );


            if (animation) {

                animations.push(
                    animation
                );

            }

        }


        introLetters.forEach(
            function (
                letter,
                index
            ) {

                const target =
                    targetLetters[
                        index
                    ];


                const animation =
                    flyToTarget(

                        letter,

                        target,

                        70 +
                        index *
                        66,

                        900,

                        true,

                        0,

                        0

                    );


                if (animation) {

                    animations.push(
                        animation
                    );

                }

            }
        );


        if (
            introTagline &&
            targetTagline
        ) {

            const animation =
                flyToTarget(

                    introTagline,

                    targetTagline,

                    150 +
                    introLetters.length *
                    66,

                    780,

                    false,

                    0,

                    0

                );


            if (animation) {

                animations.push(
                    animation
                );

            }

        }


        await Promise.all(

            animations.map(
                function (animation) {

                    return animation
                        .finished
                        .catch(
                            function () {

                                return null;

                            }
                        );

                }
            )

        );


        document.body.classList.add(
            "logo-arrived",
            "show-interface"
        );


        await waitForFrames();


        await wait(
            30
        );


        intro.classList.add(
            "intro-finished"
        );


        await wait(
            260
        );


        document.body.classList.remove(
            "intro-active"
        );


        startHomepageSequence();


    }
);