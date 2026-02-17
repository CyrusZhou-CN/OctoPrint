const {test, expect} = require("../fixtures");

const USER_AGENTS = [
    {ua: "", browser_name: true, browser_version: true, os_name: true}, // default
    {
        ua: "Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0",
        browser_name: "Firefox",
        browser_version: "147.0",
        os_name: "Linux"
    },
    {
        ua: "PrusaSlicer/2.9.4 (Windows)",
        browser_name: "PrusaSlicer",
        browser_version: "2.9.4",
        os_name: "Windows"
    }, // see # 5235
    {
        ua: "PrusaSlicer/2.9.4 (Linux)",
        browser_name: "PrusaSlicer",
        browser_version: "2.9.4",
        os_name: "Linux"
    }, // see # 5235
    {ua: "curl/1.2.3", browser_name: false, browser_version: false, os_name: false},
    {ua: "something weird", browser_name: false, browser_version: false, os_name: false}
];

const checkStringValue = (expected, actual) => {
    if (typeof expected == "boolean") {
        if (expected) {
            expect(actual).toBeTruthy();
        } else {
            expect(actual).toBe("?");
        }
    } else {
        expect(actual).toBe(expected);
    }
};

USER_AGENTS.forEach(({ua, browser_name, browser_version, os_name}) => {
    test.describe(`User Agent: ${ua ? ua : "default"}`, () => {
        test.use({userAgent: ua});

        test("error free page load", async ({page, ui}) => {
            const errors = [];
            page.on("pageerror", (error) => {
                errors.push(`[${error.name}] ${error.message}`);
            });
            page.on("console", (msg) => {
                if (msg.type() === "error") {
                    errors.push(`[${msg.type()}] ${msg.text()}`);
                }
            });

            await ui.gotoLoggedInCore();

            await expect(errors).toStrictEqual([]);
        });

        test("browser detection", async ({page, ui}) => {
            await ui.gotoLoggedInCore();

            const reportedBrowserInfo = await page.evaluate(() => {
                return window.OctoPrint.coreui.browser;
            });
            console.log("Browser:", reportedBrowserInfo);

            checkStringValue(browser_name, reportedBrowserInfo.browser_name);
            checkStringValue(browser_version, reportedBrowserInfo.browser_version);
            checkStringValue(os_name, reportedBrowserInfo.os_name);
        });
    });
});
