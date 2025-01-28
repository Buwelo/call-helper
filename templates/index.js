document.addEventListener('DOMContentLoaded', () => {
	// play audio and disable controls
    const audioPlayer = document.getElementById('audioPlayer');
    
    if (audioPlayer) {
        audioPlayer.addEventListener('play', () => {
            audioPlayer.controls = false;
        });

        // audioPlayer.addEventListener('pause', () => {
        //     audioPlayer.controls = true;
        // });

        audioPlayer.addEventListener('ended', () => {
            audioPlayer.controls = true;
        });
    } else {
        console.error('Audio player element not found');
    }

	console.log('DOM fully loaded and parsed');
	
	// read file contents
	const fileInput = document.getElementById('fileInput');
});