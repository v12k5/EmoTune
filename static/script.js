let player;
let currentEmotion = "";
let isPlayerReady = false;

const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const predictButton = document.getElementById('predict-song');

const emotionEmojis = {
    happy: '😄',
    sad: '😢',
    angry: '😠',
    surprised: '😮',
    neutral: '😐',
    fear: '😨'
};

// Get access to the webcam
navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        video.srcObject = stream;
    })
    .catch(err => {
        console.error("Error accessing webcam: ", err);
    });

predictButton.addEventListener('click', () => {
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, 640, 480);
    const dataURL = canvas.toDataURL('image/jpeg');

    // Send the image to the server
    fetch('/process_image', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ image: dataURL })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Emotion data:", data);
        const emotion = data.emotion;
        const emoji = emotionEmojis[emotion.toLowerCase()] || ''
        document.getElementById("emotion").innerText = `${emotion} ${emoji}`;

        if (emotion && emotion !== "Model not found") {
            currentEmotion = emotion;
            fetch(`/get_song/${emotion}`)
                .then(response => response.json())
                .then(songData => {
                    console.log("Song data:", songData);
                    if (songData.video_id) {
                        player.loadVideoById({
                            'videoId': songData.video_id,
                            'startSeconds': 0
                        });
                        setTimeout(() => {
                            player.playVideo();
                        }, 1000);
                    }
                });
        }
    });
});

function onYouTubeIframeAPIReady() {
    console.log("YouTube API is ready.");
    player = new YT.Player('player', {
        height: '315',
        width: '560',
        playerVars: {
            'autoplay': 1,          // Autoplay is handled by the script
            'controls': 1,          // Show controls
            'disablekb': 0,         // Enable keyboard controls
            'enablejsapi': 1,       // Enable JS API
            'fs': 1,                // Allow fullscreen
            'modestbranding': 1,    // Modest branding
            'origin': window.location.origin,
            'rel': 0                // Only show related videos from the same channel
        },
        events: {
            'onReady': onPlayerReady,
            'onStateChange': onPlayerStateChange,
            'onError': onPlayerError
        }
    });
}

function onPlayerReady(event) {
    console.log("Player is ready.");
    isPlayerReady = true;
}

function onPlayerStateChange(event) {
    console.log("Player state changed:", event.data);
}

function onPlayerError(event) {
    console.log("Player error:", event.data);
    alert("Error loading video. Please try again.");
}
