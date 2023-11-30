// https://www.yourjs.com/bookmarklet/
(function () {
    const overlayStyle = {
        position: "fixed",
        top: "0",
        left: "0",
        right: "0",
        bottom: "0",
        backgroundColor: "rgba(0,0,0,0.8)",
        zIndex: "9999",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        "--bg": "#eee",
        "--bg2": "#fff",
        "--bg3": "#ddd",
        "--fg": "#111",
        "--fg2": "#333",
    };
    const formStyle = {
        padding: "32px",
        color: "var(--fg)",
        backgroundColor: "var(--bg)",
        borderRadius: "10px",
        width: "400px",
        height: "auto",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-around",
        alignItems: "left",
        boxShadow: "0 0 10px rgba(0,0,0,0.5)",
    };
    const inpstyle = {
        padding: "8px",
        color: "var(--fg)",
        backgroundColor: "var(--bg2)",
        width: "100%",
    };
    const btnStyle = {
        padding: "8px",
        color: "var(--fg)",
        backgroundColor: "var(--bg3)",
    };

    // helper function to create dom elements
    function dom(tag, attrs, children) {
        var elem = document.createElement(tag);
        for (var attr in attrs) {
            // handle special attributes: style, events, innerHTML
            if (attr == "style") {
                for (var style in attrs[attr]) {
                    // if style starts with --
                    if (style.indexOf("--") == 0) {
                        elem.style.setProperty(style, attrs[attr][style]);
                        continue;
                    }
                    elem.style[style] = attrs[attr][style];
                }
                continue;
            }
            if (attr == "events") {
                for (var event in attrs[attr]) {
                    elem.addEventListener(event, attrs[attr][event]);
                }
                continue;
            }
            if (attr == "innerHTML") {
                elem.innerHTML = attrs[attr];
                continue;
            }
            // handle boolean attributes
            if (attrs[attr] === true || attrs[attr] === false) {
                if (attrs[attr]) {
                    elem.setAttribute(attr, "");
                }
                continue;
            }
            // handle other attributes
            elem.setAttribute(attr, attrs[attr]);
        }
        children &&
            children.forEach((child) => child && elem.appendChild(child));
        return elem;
    }

    function close() {
        setTimeout(() => {
            document.addEventListener("keydown", handleKeyDown);
            document.body.removeChild(overlay);
        }, 1000);
    }

    // create a helper function to create a label and input field
    function formField({
        name,
        label,
        value,
        placeholder,
        type = "text",
        required = false,
        hidden = false,
    }) {
        return dom("div", {}, [
            hidden && dom("label", { for: name, innerHTML: label || name }),
            !hidden && dom("label", { for: name, innerHTML: label || name }),
            !hidden &&
                dom("input", {
                    type,
                    name,
                    value,
                    placeholder,
                    required,
                    style: inpstyle,
                }),
        ]);
    }

    // create a form
    var form = dom(
        "form",
        {
            action: "bookmarks://",
            method: "get",
            target: "_blank",
            events: { submit: close },
            style: formStyle,
        },
        [
            // title
            dom("h2", {
                innerHTML: "Add Bookmark",
                style: { color: "var(--fg)" },
            }),
            // fields
            formField({
                label: "Title",
                name: "title",
                value: document.title,
                required: true,
            }),
            formField({ label: "URI", name: "uri", value: document.URL }),
            formField({
                label: "Category",
                name: "category",
                value: "unsorted",
                required: true,
            }),
            formField({
                label: "Tags",
                name: "tags",
                value: "",
                placeholder: "Separate tags with commas",
            }),
            // buttons
            dom(
                "div",
                {
                    style: {
                        display: "flex",
                        justifyContent: "space-around",
                        padding: "8px",
                        paddingTop: "16px",
                        width: "100%",
                    },
                },
                [
                    dom("input", {
                        type: "submit",
                        value: "Save",
                        style: btnStyle,
                    }),
                    dom("input", {
                        type: "button",
                        value: "Cancel",
                        style: btnStyle,
                        events: { click: close },
                    }),
                ]
            ),
        ]
    );

    var overlay = dom(
        "div",
        {
            style: overlayStyle,
        },
        [form]
    );

    function handleKeyDown(e) {
        if (e.key == "Escape") {
            close();
            return;
        }
    }
    document.addEventListener("keydown", handleKeyDown);
    document.body.appendChild(overlay);
})();
