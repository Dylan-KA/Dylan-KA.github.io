Editing your resume
===================

1. Open resume.html in VS Code (or any text editor) and change the text.
   Keep this folder structure: resume.html needs the fonts/ and img/ folders beside it.

2. Open resume.html in Google Chrome to preview. Refresh after each save.

3. Export to PDF: from the repo root run

       npm run resume      (or ./resume/build-pdf.sh)

   This renders resume.html with headless Chrome and overwrites Resume.pdf
   at the repo root. It warns if the result is more than 1 page; if so,
   shorten some text or reduce spacing.

   This folder is listed in .eleventyignore, so it is not published to the site.
