(() => {

    const workspace =
        document.getElementById(
            "careergrid-workspace"
        );


    const workspaceKey =
        workspace?.dataset.workspaceKey
        ||
        "default";


    const storageKey =
        `careergrid-simulation-state-${workspaceKey}`;


    // =========================================
    // HELPERS
    // =========================================

    function clone(value) {

        return JSON.parse(
            JSON.stringify(value)
        );

    }


    function normalizePath(path = "/") {

        let normalized =
            String(path)
                .replaceAll("\\", "/")
                .replace(/\/+/g, "/");


        if (!normalized.startsWith("/")) {

            normalized =
                "/" + normalized;

        }


        if (
            normalized.length > 1
            &&
            normalized.endsWith("/")
        ) {

            normalized =
                normalized.slice(
                    0,
                    -1
                );

        }


        return normalized;

    }


    function splitPath(path) {

        return normalizePath(path)
            .split("/")
            .filter(Boolean);

    }


    function baseName(path) {

        const parts =
            splitPath(path);

        return (
            parts[
                parts.length - 1
            ]
            ||
            "/"
        );

    }


    function parentPath(path) {

        const parts =
            splitPath(path);

        parts.pop();

        return (
            "/"
            +
            parts.join("/")
        )
            .replace(
                /^$/,
                "/"
            );

    }


    // =========================================
    // ATTACHMENT CATALOG
    //
    // These are the REAL simulated resources
    // behind Avery's attachments.
    // =========================================

    const attachmentCatalog = {

        "checkout-project": {

            id:
                "checkout-project",

            name:
                "checkout-service.zip",

            type:
                "archive",

            fileType:
                "ZIP archive",

            size:
                "18 KB",

            archiveEntries: {

                "checkout-service/README.md": {

                    type:
                        "file",

                    fileType:
                        "Markdown",

                    size:
                        "2 KB",

                    content:
`# Checkout Service

This service prepares and sends checkout requests to the commerce API.

## Running the project

Run the application and use the checkout endpoint to reproduce the reported failure.

## Testing

Tests are located in the tests directory.

Investigate the current checkout failure before changing unrelated code.`
                },


                "checkout-service/app.py": {

                    type:
                        "file",

                    fileType:
                        "Python",

                    size:
                        "3 KB",

                    content:
`from flask import Flask
from services.checkout_service import CheckoutService

app = Flask(__name__)

checkout_service = CheckoutService()


@app.route("/checkout", methods=["POST"])
def checkout():
    return checkout_service.checkout()


if __name__ == "__main__":
    app.run(debug=True)
`
                },


                "checkout-service/services/checkout_service.py": {

                    type:
                        "file",

                    fileType:
                        "Python",

                    size:
                        "4 KB",

                    content:
`class CheckoutService:

    def checkout(self):
        cart = self.get_cart()

        payload = {
            "user_id": cart["user_id"],
            "product": cart["product_id"],
            "quantity": cart["quantity"]
        }

        response = self.send_checkout_request(payload)

        return response


    def get_cart(self):
        return {
            "user_id": 1842,
            "product_id": 783,
            "quantity": 1
        }


    def send_checkout_request(self, payload):
        # Simulated external commerce API request
        return {
            "status": 400,
            "payload": payload
        }
`
                },


                "checkout-service/tests/test_checkout.py": {

                    type:
                        "file",

                    fileType:
                        "Python",

                    size:
                        "3 KB",

                    content:
`from services.checkout_service import CheckoutService


def test_cart_contains_product():
    service = CheckoutService()

    cart = service.get_cart()

    assert "product_id" in cart
    assert cart["quantity"] > 0
`
                },


                "checkout-service/.gitignore": {

                    type:
                        "file",

                    fileType:
                        "Git ignore",

                    size:
                        "1 KB",

                    content:
`.env
venv/
__pycache__/
*.pyc
`
                }

            }

        },


        "checkout-logs": {

            id:
                "checkout-logs",

            name:
                "checkout-error.log",

            type:
                "file",

            fileType:
                "Log file",

            size:
                "4 KB",

            content:
`2026-08-16 08:39:41 INFO  POST /checkout
2026-08-16 08:39:41 INFO  user_id=1842
2026-08-16 08:39:41 INFO  Sending request to commerce API

2026-08-16 08:39:42 ERROR Commerce API responded with 400 Bad Request
2026-08-16 08:39:42 ERROR Response body:
{
    "error": "validation_error",
    "message": "product_id is required"
}

2026-08-16 08:39:42 ERROR Checkout failed for user_id=1842
`
        }

    };


    // =========================================
    // INITIAL FILESYSTEM
    // =========================================

    function createInitialState() {

        return {

            version:
                1,

            filesystem: {

                Desktop: {

                    name:
                        "Desktop",

                    type:
                        "folder",

                    children:
                        {}

                },


                Downloads: {

                    name:
                        "Downloads",

                    type:
                        "folder",

                    children:
                        {}

                },


                Documents: {

                    name:
                        "Documents",

                    type:
                        "folder",

                    children:
                        {}

                },


                Projects: {

                    name:
                        "Projects",

                    type:
                        "folder",

                    children:
                        {}

                }

            }

        };

    }


    function loadState() {

        try {

            const stored =
                localStorage.getItem(
                    storageKey
                );


            if (stored) {

                const parsed =
                    JSON.parse(stored);


                if (
                    parsed
                    &&
                    parsed.filesystem
                ) {

                    return parsed;

                }

            }

        }
        catch (error) {

            console.warn(
                "Could not load CareerGrid simulation state:",
                error
            );

        }


        return createInitialState();

    }


    let state =
        loadState();


    // =========================================
    // SAVE / EVENT
    // =========================================

    function emitChange() {

        window.dispatchEvent(
            new CustomEvent(
                "careergrid:filesystem-changed",
                {
                    detail: {
                        workspaceKey:
                            workspaceKey
                    }
                }
            )
        );

    }


    function saveState() {

        localStorage.setItem(
            storageKey,
            JSON.stringify(state)
        );


        emitChange();

    }


    // =========================================
    // NODE ACCESS
    // =========================================

    function getRoot() {

        return {

            name:
                "Home",

            type:
                "folder",

            children:
                state.filesystem

        };

    }


    function getNode(path = "/") {

        const normalized =
            normalizePath(path);


        if (normalized === "/") {

            return getRoot();

        }


        const parts =
            splitPath(normalized);


        let current =
            getRoot();


        for (
            const part
            of parts
        ) {

            if (
                current.type !== "folder"
                ||
                !current.children
                ||
                !current.children[part]
            ) {

                return null;

            }


            current =
                current.children[part];

        }


        return current;

    }


    function ensureFolder(
        path,
        persist = true
    ) {

        const parts =
            splitPath(path);


        let current =
            getRoot();


        for (
            const part
            of parts
        ) {

            if (!current.children) {

                current.children =
                    {};

            }


            if (!current.children[part]) {

                current.children[part] =
                    {
                        name:
                            part,

                        type:
                            "folder",

                        children:
                            {}
                    };

            }


            current =
                current.children[part];


            if (
                current.type
                !== "folder"
            ) {

                throw new Error(
                    `${part} is not a folder`
                );

            }

        }


        if (persist) {

            saveState();

        }


        return current;

    }


    function writeNode(
        path,
        node,
        persist = true
    ) {

        const normalized =
            normalizePath(path);


        const parent =
            ensureFolder(
                parentPath(
                    normalized
                ),
                false
            );


        const name =
            baseName(
                normalized
            );


        parent.children[name] =
            {
                ...clone(node),

                name:
                    name,

                modifiedAt:
                    node.modifiedAt
                    ||
                    new Date()
                        .toISOString()
            };


        if (persist) {

            saveState();

        }


        return parent.children[name];

    }


    // =========================================
    // PUBLIC FILE OPERATIONS
    // =========================================

    function exists(path) {

        return (
            getNode(path)
            !==
            null
        );

    }


    function list(path = "/") {

        const folder =
            getNode(path);


        if (
            !folder
            ||
            folder.type
            !== "folder"
        ) {

            return [];

        }


        return Object
            .entries(
                folder.children
                ||
                {}
            )
            .map(
                ([name, node]) => {

                    const childPath =
                        normalizePath(
                            `${path}/${name}`
                        );


                    return {

                        ...clone(node),

                        path:
                            childPath

                    };

                }
            );

    }


    function read(path) {

        const node =
            getNode(path);


        return node
            ?
            clone(node)
            :
            null;

    }


    // =========================================
    // OUTLOOK ATTACHMENTS
    // =========================================

    function saveAttachmentById(
        attachmentId
    ) {

        const attachment =
            attachmentCatalog[
                attachmentId
            ];


        if (!attachment) {

            console.warn(
                "Unknown attachment:",
                attachmentId
            );

            return false;

        }


        const destination =
            `/Downloads/${attachment.name}`;


        if (exists(destination)) {

            return true;

        }


        writeNode(
            destination,
            attachment
        );


        return true;

    }


    function hasDownloadedAttachment(
        attachmentId
    ) {

        const attachment =
            attachmentCatalog[
                attachmentId
            ];


        if (!attachment) {

            return false;

        }


        return exists(
            `/Downloads/${attachment.name}`
        );

    }


    // =========================================
    // ARCHIVE EXTRACTION
    // =========================================

    function extractArchive(
        archivePath,
        destination = "/Projects"
    ) {

        const archive =
            getNode(
                archivePath
            );


        if (
            !archive
            ||
            archive.type
            !== "archive"
            ||
            !archive.archiveEntries
        ) {

            return {
                success:
                    false,

                message:
                    "This file cannot be extracted."
            };

        }


        const entries =
            Object.entries(
                archive.archiveEntries
            );


        entries.forEach(
            ([relativePath, entry]) => {

                const fullPath =
                    normalizePath(
                        `${destination}/${relativePath}`
                    );


                writeNode(
                    fullPath,
                    entry,
                    false
                );

            }
        );


        saveState();


        const firstEntry =
            entries[0]?.[0]
            ||
            "";


        const projectRoot =
            firstEntry
                .split("/")[0];


        return {

            success:
                true,

            projectPath:
                normalizePath(
                    `${destination}/${projectRoot}`
                )

        };

    }


    // =========================================
    // EXPOSE API
    // =========================================

    window.CareerGridSimulationState = {

        workspaceKey:
            workspaceKey,

        storageKey:
            storageKey,

        list:
            list,

        read:
            read,

        exists:
            exists,

        ensureFolder:
            ensureFolder,

        writeNode:
            writeNode,

        saveAttachmentById:
            saveAttachmentById,

        hasDownloadedAttachment:
            hasDownloadedAttachment,

        extractArchive:
            extractArchive

    };

})();