module.exports = function (eleventyConfig) {
    eleventyConfig.addPassthroughCopy("Images");
    eleventyConfig.addPassthroughCopy("Scripts");
    eleventyConfig.addPassthroughCopy("stylesheet.css");
    eleventyConfig.addPassthroughCopy("Resume.pdf");
    eleventyConfig.addPassthroughCopy("css");

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