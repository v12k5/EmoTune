let player;
let currentEmotion = "";
let isPlayerReady = false;

function onYouTubeIframeAPIReady() {
    console.log("YouTube API is ready.");
    player = new YT.Player('player', {
        height: '390',
        width: '640',
        playerVars: {
            'autoplay': 0,          // Don't autoplay initially
            'controls': 1,          // Show controls
            'disablekb': 0,         // Enable keyboard controls
            'enablejsapi': 1,       // Enable JS API
            'fs': 1,                // Allow fullscreen
            'modestbranding': 1,    // Modest branding
            'origin': window.location.origin
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
    document.getElementById("predict-song").disabled = false;
    document.getElementById("play-pause").disabled = false;
}

function onPlayerStateChange(event) {
    console.log("Player state changed:", event.data);
    if (event.data == YT.PlayerState.ENDED) {
        console.log("Video ended.");
        // Automatically get next emotion-based song when current ends
        setTimeout(() => {
            getEmotionAndPlaySong();
        }, 1000);
    }
}

function onPlayerError(event) {
    console.log("Player error:", event.data);
    alert("Error loading video. Please try again.");
}

function getEmotionAndPlaySong() {
    if (!isPlayerReady) {
        console.log("Player not ready yet.");
        return;
    }

    fetch("/emotion")
        .then((response) => response.json())
        .then((data) => {
            console.log("Emotion data:", data);
            document.getElementById("emotion").innerText = data.emotion;
            
            if (data.emotion && data.emotion !== "Model not found") {
                console.log("Detected emotion:", data.emotion);
                currentEmotion = data.emotion;
                
                fetch(`/get_song/${data.emotion}`)
                    .then((response) => response.json())
                    .then((songData) => {
                        console.log("Song data:", songData);
                        if (songData.video_id) {
                            // Load and play the video
                            player.loadVideoById({
                                'videoId': songData.video_id,
                                'startSeconds': 0
                            });
                            
                            // Try to play after loading (with user interaction)
                            setTimeout(() => {
                                player.playVideo();
                            }, 1000);
                        }
                    })
                    .catch((error) => {
                        console.error("Error fetching song:", error);
                    });
            } else {
                console.log("No valid emotion detected or model not found.");
                document.getElementById("emotion").innerText = "No emotion detected";
            }
        })
        .catch((error) => {
            console.error("Error fetching emotion:", error);
        });
}

// Manual play/pause button
document.getElementById("play-pause").addEventListener("click", () => {
    if (!isPlayerReady) {
        console.log("Player not ready yet.");
        return;
    }

    try {
        const playerState = player.getPlayerState();
        console.log("Current player state:", playerState);
        
        if (playerState === YT.PlayerState.PLAYING) {
            player.pauseVideo();
            document.getElementById("play-pause").textContent = "Play";
        } else if (playerState === YT.PlayerState.PAUSED || 
                   playerState === YT.PlayerState.ENDED || 
                   playerState === YT.PlayerState.CUED) {
            player.playVideo();
            document.getElementById("play-pause").textContent = "Pause";
        }
    } catch (error) {
        console.error("Error controlling playback:", error);
    }
});

// Detect emotion and play song button
document.getElementById("predict-song").addEventListener("click", () => {
    console.log("Detect Emotion & Play Song button clicked.");
    currentEmotion = ""; // Reset current emotion to force a new song
    getEmotionAndPlaySong();
});


// Update play/pause button text based on player state
function updatePlayPauseButton() {
    if (!isPlayerReady) return;
    
    try {
        const playerState = player.getPlayerState();
        const button = document.getElementById("play-pause");
        
        if (playerState === YT.PlayerState.PLAYING) {
            button.textContent = "Pause";
        } else {
            button.textContent = "Play";
        }
    } catch (error) {
        console.error("Error updating button:", error);
    }
}

// Update button state every second
setInterval(updatePlayPauseButton, 1000);

// Add volume control function
function setVolume(volume) {
    if (isPlayerReady) {
        player.setVolume(volume);
    }
}