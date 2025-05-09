module.exports = function(eleventyConfig) {
    eleventyConfig.addPassthroughCopy("Images");
    eleventyConfig.addPassthroughCopy("Scripts");
    eleventyConfig.addPassthroughCopy("stylesheet.css");

    eleventyConfig.addShortcode("ProjectCard", function(link, img, title, logo1, logo2, logo3, description) {
        let logos = '';
        if (logo3) {
            logos = `
            <img src="${logo3}" style="width:30px; float:right; margin-left: 5px; margin-top: 2px; border-radius: 10px;">
            <img src="${logo2}" style="width:30px; float:right; margin-left: 5px;">
            <img src="${logo1}" style="width:30px; float:right;">
            `;
        } else if (logo2) {
            logos = `
            <img src="${logo2}" style="width:30px; float:right; margin-left: 5px;">
            <img src="${logo1}" style="width:30px; float:right;">
            `;
        } else if (logo1) {
            logos = `
            <img src="${logo1}" style="width:30px; float:right;">
            `;
        }

        return `<div class="w3-third w3-container w3-margin-bottom">
                    <a href="${link}">
                        <img src="${img}" style="width:100%">
                    </a>
                    <div class="w3-container w3-white project-card">
                        <h4>
                        <a href="${link}"><b>${title}</b></a>
                        ${logos}
                        </h4>
                        <p>${description}</p>
                        <a href="${link}"><b>Learn More</b></a>
                    </div>
                </div>`;
    });

    eleventyConfig.addShortcode("Footer", function() {
        return `<footer class="w3-container w3-padding-32 w3-dark-grey">
                    <div class="w3-center w3-margin-top">
                    <p>
                        © 2025 Dylan Archer.
                    </p>
                    <a href="https://github.com/dylan-ka" target="_blank" class="social-icon-white">
                        <img width="30px" class="footer-href" src="Images/Logos/GitHubLogo.png">
                    </a>
                    <a href="https://dylanka.itch.io/" target="_blank" class="social-icon-white">
                        <img width="30px" class="footer-href" src="Images/Logos/ItchLogo.webp">
                    </a>
                    <a href="https://www.linkedin.com/in/dylan-archer-44a783338/" target="_blank" class="social-icon-white">
                        <img width="30px" class="footer-href" src="Images/Logos/LinkedInLogo.webp">
                    </a>
                    </div>
                </footer>`;
    });

    eleventyConfig.addShortcode("Sidebar", function() {
        return `<nav class="w3-sidebar w3-collapse w3-white" style="z-index:3;width:300px;" id="mySidebar"><br>
                    <div class="w3-container">
                        <a href="#" onclick="w3_close()" class="w3-hide-large w3-right w3-jumbo w3-padding w3-hover-grey" title="close menu">
                        <i class="fa fa-remove"></i>
                        </a>
                        <img src="Images/SelfPortrait.png" style="width:100%;" class="w3-round-large"><br><br>
                        <h4><b>Portfolio</b></h4>
                    </div>
                    <div class="w3-bar-block">
                        <a href="index.html#about" class="w3-bar-item w3-button w3-padding"><i class="fa fa-user fa-fw w3-margin-right"></i><b>About Me</b></a> 
                        <a href="index.html#game-projects" class="w3-bar-item w3-button w3-padding">
                            <i class="fa fa-gamepad fa-fw w3-margin-right"></i><b>Game Projects</b>
                        </a> 
                        <a href="DualWield.html" class="w3-bar-item w3-button nested-link">Dual Wield</a>
                        <a href="Caved-In.html" class="w3-bar-item w3-button nested-link">Caved In</a>
                        <a href="PacStudent.html" class="w3-bar-item w3-button nested-link">PacStudent</a>

                        <a href="index.html#web-projects" class="w3-bar-item w3-button w3-padding">
                            <i class="fa fa-globe fa-fw w3-margin-right"></i><b>Web Projects</b>
                        </a>
                        <a href="GroceryStore.html" class="w3-bar-item w3-button nested-link">Online Grocery Store</a>
                        <a href="CarRentalSystem.html" class="w3-bar-item w3-button nested-link">Online Car Rental</a>

                        <a href="index.html#mobile-projects" class="w3-bar-item w3-button w3-padding">
                            <i class="fa fa-apple fa-fw w3-margin-right"></i><b>Mobile Projects</b>
                        </a>
                        <a href="Quiz-App.html" class="w3-bar-item w3-button nested-link">Quiz App</a>
                        <a href="OnTaskPro.html" class="w3-bar-item w3-button nested-link">Task Tracker App</a>

                        <a href="index.html#3d-projects" class="w3-bar-item w3-button w3-padding">
                            <i class="fa fa-cube fa-fw w3-margin-right"></i><b>3D Creative</b>
                        </a>
                        <a href="Blender.html" class="w3-bar-item w3-button nested-link">3D Modelling Project</a>
                        <a href="3DAnim.html" class="w3-bar-item w3-button nested-link">Unity 3D Animation</a>

                        <a href="index.html#other-projects" class="w3-bar-item w3-button w3-padding">
                            <i class="fa fa-wrench fa-fw w3-margin-right"></i><b>Other Projects</b>
                        </a>
                        <a href="ClashOfCommands.html" class="w3-bar-item w3-button nested-link">Clash of Commands</a>
                        <a href="#contact" class="w3-bar-item w3-button w3-padding"><i class="fa fa-envelope fa-fw w3-margin-right"></i><b>Contact</b></a>
                    </div>
                </nav>`;
    });
    
    eleventyConfig.addShortcode("Contact", function() {
        return `<hr>
                <div class="w3-container w3-padding-large w3-grey">
                    <h4 id="contact"><b>Contact Me</b></h4>
                    <div class="w3-row-padding w3-center w3-padding-24" style="margin:0 -16px">
                    <div class="w3-third w3-dark-grey">
                        <p><i class="fa fa-envelope w3-xxlarge w3-text-light-grey"></i></p>
                        <p><span class="numbers">dylanka3@gmail.com</span></p>
                    </div>
                    <div class="w3-third w3-cyan">
                        <p><i class="fa fa-map-marker w3-xxlarge w3-text-light-grey"></i></p>
                        <p>Sydney, Australia</p>
                    </div>
                    <div class="w3-third w3-dark-grey">
                        <p><i class="fa fa-phone w3-xxlarge w3-text-light-grey"></i></p>
                        <p><span class="numbers">+61 468 432 861</span></p>
                    </div>
                    </div>
                    <hr class="w3-opacity">
                </div>`;
    });

    return {
      dir: {
        input: ".",
        output: "_site"
      }
    };
  };  