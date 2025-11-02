module.exports = function(eleventyConfig) {
    eleventyConfig.addPassthroughCopy("Images");
    eleventyConfig.addPassthroughCopy("Scripts");
    eleventyConfig.addPassthroughCopy("stylesheet.css");
    eleventyConfig.addPassthroughCopy("Resume.pdf");
    eleventyConfig.addPassthroughCopy("css");

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

        return `<div class="project-item-outer">
                    <a href="${link}" style="display: inline-block;">
                        <img src="${img}">
                    </a>
                    <div class="project-item-inner">
                        <h3 class="project-title">
                        <a href="${link}">${title}</a>
                        ${logos}
                        </h3>
                        <p>${description}</p>
                        <a href="${link}" class="project-learn-more">Learn More</a>
                    </div>
                </div>`;
    });

    eleventyConfig.addShortcode("NavigationButtons", function() {
        return `<div>
                    <button onclick="window.location.href='index.html'" class="medium">About Me</button>
                    <div class="dropdown">
                        <button onclick="window.location.href='index.html#projects'" class="dropbtn medium">Projects</button>
                        <div class="dropdown-content">
                            <div class="dropdown-sub">
                                <a href="index.html#game-projects">Game Development</a>
                                <div class="dropdown-sub-content">
                                    <a href="DualWield.html">Dual Wield</a>
                                    <a href="Caved-In.html">Caved In</a>
                                    <a href="PacStudent.html">PacStudent</a>
                                    <a href="Wormy.html">Wormy</a>
                                </div>
                            </div>
                            <div class="dropdown-sub">
                                <a href="index.html#web-projects">Web Development</a>
                                <div class="dropdown-sub-content">
                                    <a href="GroceryStore.html">Online Grocery Store</a>
                                    <a href="CarRentalSystem.html">Online Car Rental</a>
                                </div>
                            </div>
                            <div class="dropdown-sub">
                                <a href="index.html#mobile-projects">Mobile Development</a>
                                <div class="dropdown-sub-content">
                                    <a href="Quiz-App.html">Quiz App</a>
                                    <a href="OnTaskPro.html">Task Tracker App</a>
                                </div>
                            </div>
                            <div class="dropdown-sub">
                                <a href="index.html#3d-projects">Modelling & Animation</a>
                                <div class="dropdown-sub-content">
                                    <a href="Blender.html">3D Modelling Project</a>
                                    <a href="3DAnim.html">Unity 3D Animation</a>
                                </div>
                            </div>
                            <div class="dropdown-sub">
                                <a href="index.html#other-projects">Other Projects</a>
                                <div class="dropdown-sub-content">
                                    <a href="ClashOfCommands.html">Clash of Commands</a>
                                </div>
                            </div>
                        </div>
                    </div>
                    <button onclick="window.location.href='Contact.html'" class="medium">Contact</button>
                </div>`;
    });

    eleventyConfig.addShortcode("Footer", function() {
        const year = new Date().getFullYear();
        return `<footer class="container ">
                    <div>
                    <p>
                        © ${year} Dylan Archer.
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
        return `<nav style="z-index:3;width:300px;" id="mySidebar"><br>
                    <div class="container">
                        <a href="#" onclick="" title="close menu">
                        </i>
                        </a>
                        <img src="Images/ProfilePicture.jpeg" style="width:100%;" ><br><br>
                        <h4>Portfolio</h4>
                    </div>
                    <div>
                        <a href="index.html#about"></i><b>About Me</b></a> 
                        <a href="index.html#game-projects">
                            </i><b>Game Projects</b>
                        </a> 
                        <a href="DualWield.html" class="button nested-link">Dual Wield</a>
                        <a href="Caved-In.html" class="button nested-link">Caved In</a>
                        <a href="PacStudent.html" class="button nested-link">PacStudent</a>
                        <a href="Wormy.html" class="button nested-link">Wormy</a>

                        <a href="index.html#web-projects">
                            </i><b>Web Projects</b>
                        </a>
                        <a href="GroceryStore.html" class="button nested-link">Online Grocery Store</a>
                        <a href="CarRentalSystem.html" class="button nested-link">Online Car Rental</a>

                        <a href="index.html#mobile-projects">
                            </i><b>Mobile Projects</b>
                        </a>
                        <a href="Quiz-App.html" class="button nested-link">Quiz App</a>
                        <a href="OnTaskPro.html" class="button nested-link">Task Tracker App</a>

                        <a href="index.html#3d-projects">
                            </i><b>3D Creative</b>
                        </a>
                        <a href="Blender.html" class="button nested-link">3D Modelling Project</a>
                        <a href="3DAnim.html" class="button nested-link">Unity 3D Animation</a>

                        <a href="index.html#other-projects">
                            </i><b>Other Projects</b>
                        </a>
                        <a href="ClashOfCommands.html" class="button nested-link">Clash of Commands</a>
                        <a href="Contact.html"></i><b>Contact</b></a>
                    </div>
                </nav>`;
    });
    
    eleventyConfig.addShortcode("Contact", function() {
        return `<hr>
                <div class="container">
                    <h4 id="contact"><b>Contact Me</h4>
                    <div  style="margin:0 -16px">
                    <div>
                        <p></i></p>
                        <p><span>dylanka3@gmail.com</span></p>
                    </div>
                    <div>
                        <p></i></p>
                        <p>Sydney, Australia</p>
                    </div>
                    <div>
                        <p></i></p>
                        <p><span>(+61) 468 432 861</span></p>
                    </div>
                    </div>
                    <hr >
                </div>`;
    });

    return {
      dir: {
        input: ".",
        output: "_site"
      }
    };
  };  