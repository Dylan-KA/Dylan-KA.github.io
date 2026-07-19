const fs = require("fs");
const path = require("path");

const CSS_BUNDLE_FILES = [
    "css/base.css",
    "css/header-and-profile.css",
    "css/buttons-and-dropdowns.css",
    "css/projects.css",
    "css/footer.css",
    "css/utilities.css"
];

function bundleCss() {
    const bundled = CSS_BUNDLE_FILES
        .map((file) => fs.readFileSync(path.join(__dirname, file), "utf8"))
        .join("\n");
    fs.writeFileSync(path.join(__dirname, "stylesheet.css"), bundled);
}

module.exports = function (eleventyConfig) {
    eleventyConfig.addPassthroughCopy("Images");
    eleventyConfig.addPassthroughCopy("Scripts");
    eleventyConfig.addPassthroughCopy("stylesheet.css");
    eleventyConfig.addPassthroughCopy("Resume.pdf");
    eleventyConfig.addPassthroughCopy("robots.txt");
    eleventyConfig.addWatchTarget("css");
    eleventyConfig.on("eleventy.before", bundleCss);

    eleventyConfig.addFilter("encodeUri", (value) => encodeURI(value));

    return {
        dir: {
            input: ".",
            output: "_site",
            includes: "_includes",
            data: "_data"
        },
        templateFormats: ["html", "njk", "md"],
        markdownTemplateEngine: "njk",
        htmlTemplateEngine: "njk",
        dataTemplateEngine: "njk"
    };
};