let currentSlide = 0;
const slides = document.querySelectorAll('.carousel-slide');
const totalSlides = slides.length;
const dotContainer = document.querySelector('.dot-container');

let player; // Global player instance for YouTube

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
}

function showNextSlide() {
    currentSlide = (currentSlide + 1) % totalSlides;
    showSlide(currentSlide);
}

function moveSlide(n) {
    clearInterval(slideInterval); // Stop automatic cycling when manually navigating
    pauseVideoIfPlaying(); // Pause the YouTube video if playing
    currentSlide = (currentSlide + n + totalSlides) % totalSlides;
    showSlide(currentSlide);
    slideInterval = setInterval(showNextSlide, 7000); // Restart automatic cycling
}

function moveToSlide(index) {
    clearInterval(slideInterval); // Stop automatic cycling when navigating with dots
    pauseVideoIfPlaying(); // Pause the YouTube video if playing
    showSlide(index);
    slideInterval = setInterval(showNextSlide, 7000); // Restart automatic cycling
}

// Update the dots to reflect the current slide
function updateDots() {
    const dots = document.querySelectorAll('.dot');
    dots.forEach((dot, index) => {
        dot.classList.toggle('active', index === currentSlide);
    });
}

// Pause the YouTube video if it is playing
function pauseVideoIfPlaying() {
    if (player && player.getPlayerState() === YT.PlayerState.PLAYING) {
        player.pauseVideo();
    }
}

// Initialize the first slide
showSlide(currentSlide);

// Add keyboard navigation
document.addEventListener('keydown', (event) => {
    if (event.key === "ArrowLeft") {
        moveSlide(-1); // Navigate to the previous slide
    } else if (event.key === "ArrowRight") {
        moveSlide(1); // Navigate to the next slide
    }
});

// YouTube API Integration
function onYouTubeIframeAPIReady() {
    player = new YT.Player('youtube-player', {
        events: {
            onStateChange: onPlayerStateChange
        }
    });
}

function onPlayerStateChange(event) {
    if (event.data === YT.PlayerState.PLAYING) {
        clearInterval(slideInterval); // Pause slideshow while video plays
    }
}
