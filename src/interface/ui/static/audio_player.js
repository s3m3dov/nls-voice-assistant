/**
 * Web Audio API player for streaming TTS audio chunks.
 * 
 * This module handles queuing and sequential playback of audio chunks
 * that are embedded in the DOM as base64-encoded WAV data.
 */

(function() {
    'use strict';

    // Suppress Gradio's "Too many arguments" warning
    const originalWarn = console.warn;
    console.warn = function(...args) {
        if (args[0] && args[0].includes && args[0].includes('Too many arguments')) {
            return; // Suppress this specific warning
        }
        originalWarn.apply(console, args);
    };

    // Audio queue for sequential playback
    const audioQueue = [];
    let isPlaying = false;
    let lastProcessedChunkId = 0;
    let audioContext = null;

    /**
     * Get or create a reusable AudioContext.
     * Handles browser autoplay policy by resuming suspended contexts.
     */
    function getAudioContext() {
        if (!audioContext || audioContext.state === 'closed') {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioContext.state === 'suspended') {
            audioContext.resume();
        }
        return audioContext;
    }

    /**
     * Decode base64 string to Uint8Array.
     */
    function base64ToBytes(base64) {
        const binaryString = atob(base64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return bytes;
    }

    /**
     * Play the next audio chunk in the queue.
     */
    async function playNext() {
        if (audioQueue.length === 0) {
            isPlaying = false;
            return;
        }

        isPlaying = true;
        const { audioData, chunkId } = audioQueue.shift();
        console.log('[AudioPlayer] Playing chunk:', chunkId, 'remaining:', audioQueue.length);

        try {
            const bytes = base64ToBytes(audioData);
            const ctx = getAudioContext();
            
            // Create a copy of the buffer to avoid detachment issues
            const audioBuffer = await ctx.decodeAudioData(bytes.buffer.slice(0));

            const source = ctx.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(ctx.destination);
            source.onended = playNext;
            source.start(0);
        } catch (error) {
            console.error('[AudioPlayer] Playback error:', error);
            playNext();
        }
    }

    /**
     * Scan the DOM for unprocessed audio chunks and queue them.
     */
    function scanForAudioChunks() {
        const container = document.getElementById('audio_data');
        if (!container) return;

        const chunks = container.querySelectorAll('.audio-chunk[data-chunk-id]');
        
        chunks.forEach(chunk => {
            const chunkId = parseInt(chunk.getAttribute('data-chunk-id'), 10);
            
            if (chunkId > lastProcessedChunkId) {
                const audioData = chunk.getAttribute('data-audio');
                
                if (audioData) {
                    lastProcessedChunkId = chunkId;
                    audioQueue.push({ audioData, chunkId });
                    console.log('[AudioPlayer] Queued chunk:', chunkId);
                }
            }
        });

        if (audioQueue.length > 0 && !isPlaying) {
            playNext();
        }
    }

    /**
     * Initialize the audio player and start observing for new chunks.
     */
    function initialize() {
        const observer = new MutationObserver(scanForAudioChunks);

        function startObserver() {
            const target = document.getElementById('audio_data');
            
            if (target) {
                observer.observe(target, {
                    childList: true,
                    subtree: true,
                    characterData: true
                });
                console.log('[AudioPlayer] Observer started');
                
                // Poll as backup for any missed mutations
                setInterval(scanForAudioChunks, 50);
            } else {
                setTimeout(startObserver, 100);
            }
        }

        // Enable audio context on first user interaction (autoplay policy)
        document.addEventListener('click', () => getAudioContext(), { once: true });

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', startObserver);
        } else {
            startObserver();
        }
    }

    // Start the audio player
    initialize();
})();
