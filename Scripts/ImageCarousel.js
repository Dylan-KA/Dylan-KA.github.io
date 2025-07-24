let currentSlide = 0;
const slides = document.querySelectorAll('.carousel-slide');
const totalSlides = slides.length;
const dotContainer = document.querySelector('.dot-container');

// Create dots for each slide
for (let i = 0; i < totalSlides; i++) {
    const dot = document.createElement('span');
    dot.classList.add('dot');
    dot.onclick = () => {
        moveToSlide(i);
    };
    dotContainer.appendChild(dot);
}

// Initialize the dots
updateDots();

let slideInterval = setInterval(showNextSlide, 7000); // Change every 7 seconds

function showSlide(index) {
    slides.forEach((slide, i) => {
        slide.style.display = i === index ? 'block' : 'none';
    });
    currentSlide = index;
    updateDots(); // Update the dots when the slide changes

    // Sync FullView image if it is open
    const fullView = document.getElementById("FullImageView");
    if (fullView.style.display === "block") {
        document.getElementById("FullImage").src = slides[currentSlide].src;
    }
}

function showNextSlide() {
    currentSlide = (currentSlide + 1) % totalSlides;
    showSlide(currentSlide);
}

function moveSlide(n) {
    clearInterval(slideInterval); // Stop automatic cycling when manually navigating
    currentSlide = (currentSlide + n + totalSlides) % totalSlides;
    showSlide(currentSlide);
    slideInterval = setInterval(showNextSlide, 7000); // Restart automatic cycling
}

function moveToSlide(index) {
    clearInterval(slideInterval); // Stop automatic cycling when navigating with dots
    showSlide(index);
    slideInterval = setInterval(showNextSlide, 7000); // Restart automatic cycling
}

// Update the dots to reflect the current slides
function updateDots() {
    const dots = document.querySelectorAll('.dot');
    dots.forEach((dot, index) => {
        dot.classList.toggle('active', index === currentSlide);
    });
}

// Initialize the first slide
showSlide(currentSlide);

// Add keyboard navigation
document.addEventListener('keydown', (event) => {
    if (event.key === "ArrowLeft") {
        moveSlide(-1); // Navigate to theious slide
    } else if (event.key === "ArrowRight") {
        moveSlide(1); // Navigate to the slide
    } else if(event.key === "Escape") {
        CloseFullView();
    }
});

function FullView() {
    const currentImage = slides[currentSlide].src;
    document.getElementById("FullImage").src = currentImage;
    document.getElementById("FullImageView").style.display = "block";
    clearInterval(slideInterval); // Pause the timer
}

function CloseFullView() {
    document.getElementById("FullImageView").style.display = "none";
    slideInterval = setInterval(showNextSlide, 7000); // Resume the timer
}