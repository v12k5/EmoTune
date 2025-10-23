let player;
let currentEmotion = "";
let isPlayerReady = false;

const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const predictButton = document.getElementById('predict-song');
const languageSelect = document.getElementById('language');

const emotionEmojis = {
    happy: '😄',
    sad: '😢',
    angry: '😠',
    surprise: '😮',
    neutral: '😐',
    fear: '😨'
};

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

    fetch('/process_image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: dataURL })
    })
    .then(response => response.json())
    .then(data => {
        const emotion = data.emotion;
        const emoji = emotionEmojis[emotion.toLowerCase()] || '';
        document.getElementById("emotion").innerText = `${emotion} ${emoji}`;

        if (emotion && emotion !== "Model not found") {
            currentEmotion = emotion;
            const lang = languageSelect.value;
            fetch(`/get_song/${emotion}?lang=${lang}`)
                .then(response => response.json())
                .then(songData => {
                    if (songData.video_id) {
                        if (isPlayerReady && player) {
                            player.loadVideoById({
                                'videoId': songData.video_id,
                                'startSeconds': 0
                            });
                            setTimeout(() => {
                                player.playVideo();
                            }, 1000);
                        } else {
                            createPlayer(songData.video_id);
                        }
                    } else {
                        alert("Could not find a suitable video. Try a different emotion or language!");
                    }
                });
        }
    });
});

function createPlayer(videoId) {
    player = new YT.Player('player', {
        height: '315',
        width: '560',
        videoId: videoId,
        playerVars: {
            'autoplay': 1,
            'controls': 1,
            'disablekb': 0,
            'enablejsapi': 1,
            'fs': 1,
            'modestbranding': 1,
            'origin': window.location.origin,
            'rel': 0
        },
        events: {
            'onReady': onPlayerReady,
            'onStateChange': onPlayerStateChange,
            'onError': onPlayerError
        }
    });
}

function onYouTubeIframeAPIReady() {
    isPlayerReady = true;
}

function onPlayerReady(event) {
    isPlayerReady = true;
}

function onPlayerStateChange(event) {
    // Placeholder for future enhancements.
}

function onPlayerError(event) {
    alert("Error loading video. Please try again or predict a new emotion!");
}
