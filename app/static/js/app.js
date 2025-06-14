document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const audioFile = document.getElementById('audio-file');
    const fileName = document.getElementById('file-name');
    const uploadBtn = document.getElementById('upload-btn');
    const videoUrl = document.getElementById('video-url');
    const processVideoBtn = document.getElementById('process-video-btn');
    const audioPlayerContainer = document.getElementById('audio-player-container');
    const audioPlayer = document.getElementById('audio-player');
    const numSpeakers = document.getElementById('num-speakers');
    const speakerGendersContainer = document.getElementById('speaker-genders-container');
    const targetLanguageSelect = document.getElementById('target-language-select');
    const continueBtn = document.getElementById('continue-btn');
    
    // Step Navigation
    const stepInput = document.getElementById('step-input');
    const stepTranscription = document.getElementById('step-transcription');
    const stepTranslation = document.getElementById('step-translation');
    const stepSynthesis = document.getElementById('step-synthesis');
    const stepValidation = document.getElementById('step-validation');
    
    // Transcription Elements
    const transcriptionContainer = document.getElementById('transcription-container');
    const transcriptionText = document.getElementById('transcription-text');
    const diarizationEditor = document.getElementById('diarization-editor');
    const backToInputBtn = document.getElementById('back-to-input-btn');
    const saveTranscriptionBtn = document.getElementById('save-transcription-btn');
    
    // Translation Elements
    const sourceLanguage = document.getElementById('source-language');
    const targetLanguage = document.getElementById('target-language');
    const translationText = document.getElementById('translation-text');
    const backToTranscriptionBtn = document.getElementById('back-to-transcription-btn');
    const saveTranslationBtn = document.getElementById('save-translation-btn');
    const translationEditor = document.getElementById('translation-editor');
    
    // Synthesis Elements
    const synthesisLanguage = document.getElementById('synthesis-language');
    const synthesisProgress = document.getElementById('synthesis-progress');
    const outputAudioPlayerContainer = document.getElementById('output-audio-player-container');
    const outputAudioPlayer = document.getElementById('output-audio-player');
    const downloadLink = document.getElementById('download-link');
    const backToTranslationBtn = document.getElementById('back-to-translation-btn');
    const synthesizeBtn = document.getElementById('synthesize-btn');
    const validateBtn = document.getElementById('validate-btn');
    
    // Synthesis Options
    // Removed timeAlignedToggle reference
    
    // Validation Elements
    // Removed similarityScore reference as the element no longer exists
    const comparisonInputAudio = document.getElementById('comparison-input-audio');
    const comparisonOutputAudio = document.getElementById('comparison-output-audio');
    const backToSynthesisBtn = document.getElementById('back-to-synthesis-btn');
    const startOverBtn = document.getElementById('start-over-btn');
    let metricsDetails = document.getElementById('metrics-details');
    if (!metricsDetails) {
        metricsDetails = document.createElement('div');
        metricsDetails.id = 'metrics-details';
        const validationContainer = document.getElementById('step-validation');
        if (validationContainer) {
            validationContainer.appendChild(metricsDetails);
        }
    }
    
    // Loading Overlay
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingMessage = document.getElementById('loading-message');
    
    // Global Variables
    let audioBlob;
    let audioUrl;
    let sessionId;
    let detectedLang;
    let hasValidSession = false;  // Flag to track if we have a valid session with content
    
    // Recording-related variables
    let recordBtn = document.getElementById('record-btn');
    let recordingTimer = document.getElementById('recording-timer');
    let recordedChunks = [];
    let recordingSeconds = 0;
    let mediaRecorder;
    
    // Get reliable session ID from multiple sources
    function getReliableSessionId() {
        // Try window.sessionId first (global variable)
        if (sessionId) {
            console.log('Using global sessionId:', sessionId);
            return sessionId;
        }
        
        // Try URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const urlSessionId = urlParams.get('session_id');
        if (urlSessionId) {
            console.log('Using URL sessionId:', urlSessionId);
            // Store it in the global variable for future use
            sessionId = urlSessionId;
            return urlSessionId;
        }
        
        // Try data attributes on elements
        const sessionElement = document.querySelector('[data-session-id]');
        if (sessionElement && sessionElement.dataset.sessionId) {
            console.log('Using DOM sessionId:', sessionElement.dataset.sessionId);
            sessionId = sessionElement.dataset.sessionId;
            return sessionElement.dataset.sessionId;
        }
        
        // Check if it's in the form
        const sessionIdInput = document.querySelector('input[name="session_id"]');
        if (sessionIdInput && sessionIdInput.value) {
            console.log('Using form sessionId:', sessionIdInput.value);
            sessionId = sessionIdInput.value;
            return sessionIdInput.value;
        }
        
        console.error('No session ID found from any source');
        return null;
    }
    
    // Initialize
    function init() {
        console.log('Initializing application');
        
        // Generate session ID
        sessionId = generateSessionId();
        console.log('Generated session ID:', sessionId);
        
        // Set up event listeners
        setupEventListeners();
        
        // Check if diarization editor container exists
        const diarizationEditor = document.getElementById('diarization-editor');
        if (diarizationEditor) {
            console.log('Diarization editor container found in DOM');
        } else {
            console.warn('Diarization editor container not found in DOM');
        }
        
        // Initialize speaker genders
        updateSpeakerGenders();
        
        // Load voice options for default language
        loadVoiceOptions(targetLanguageSelect.value);
        
        // Disable continue button until file is uploaded
        continueBtn.disabled = true;
        
        // Set up download session button
        const downloadSessionBtn = document.getElementById('download-session-btn');
        if (downloadSessionBtn) {
            downloadSessionBtn.addEventListener('click', function(e) {
                e.preventDefault();
                downloadSessionFiles();
            });
        }
        
        // Initialize with no valid session
        hasValidSession = false;
        
        // Hide download button initially (no session yet)
        updateSessionDownloadButton();
    }
    
    // Generate a random session ID
    function generateSessionId() {
        return 'session_' + Math.random().toString(36).substring(2, 15);
    }
    
    // Set up event listeners
    function setupEventListeners() {
        // File input change
        audioFile.addEventListener('change', handleFileSelect);
        
        // Upload button click
        uploadBtn.addEventListener('click', uploadAudio);
        
        // Process video button click
        processVideoBtn.addEventListener('click', processVideoUrl);
        
        // Video URL input enter key
        videoUrl.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                processVideoUrl();
            }
        });
        
        // Number of speakers change
        numSpeakers.addEventListener('change', updateSpeakerGenders);
        
        // Target language change
        targetLanguageSelect.addEventListener('change', function() {
            loadVoiceOptions(this.value);
        });
        
        // Navigation buttons
        continueBtn.addEventListener('click', function() {
            console.log('Continue button clicked');
            
            // First show the transcription step
            showStep(stepTranscription);
            
            // Disable interactive elements while processing
            disableTranscriptionEditing();
            
            // Show loading animation
            showLoading('Processing your audio...');
            
            // Start the language detection process
            detectLanguageAndProcess();
        });
        
        backToInputBtn.addEventListener('click', function() {
            console.log('Back to input button clicked');
            showStep(stepInput);
        });
        
        saveTranscriptionBtn.addEventListener('click', function() {
            console.log('Save transcription button clicked');
            saveTranscription();
            // Note: showStep(stepTranslation) will be called by saveTranscription after saving
        });
        
        backToTranscriptionBtn.addEventListener('click', function() {
            console.log('Back to transcription button clicked');
            showStep(stepTranscription);
        });
        
        saveTranslationBtn.addEventListener('click', function() {
            console.log('Save translation button clicked');
            saveTranslation();
            // Note: showStep(stepSynthesis) will be called by saveTranslation after saving
        });
        
        backToTranslationBtn.addEventListener('click', function() {
            console.log('Back to translation button clicked');
            showStep(stepTranslation);
        });
        
        synthesizeBtn.addEventListener('click', function() {
            console.log('Synthesize button clicked');
            synthesizeSpeech();
        });
        
        validateBtn.addEventListener('click', function() {
            console.log('Validate button clicked');
            showStep(stepValidation);
            validateOutput();
        });
        
        backToSynthesisBtn.addEventListener('click', function() {
            console.log('Back to synthesis button clicked');
            showStep(stepSynthesis);
        });
        
        startOverBtn.addEventListener('click', function() {
            console.log('Start over button clicked');
            resetApplication();
        });
        
        // Diarization save button click
        const saveDiarizationBtn = document.getElementById('save-diarization-btn');
        if (saveDiarizationBtn) {
            saveDiarizationBtn.addEventListener('click', function() {
                console.log('Save diarization button clicked');
                showLoading('Saving diarization edits...');
                
                saveDiarizationEdits()
                    .then(result => {
                        hideLoading();
                        if (result.success) {
                            showNotification('Diarization edits saved successfully', 'success');
                        } else {
                            showNotification('Error saving diarization edits: ' + (result.error || 'Unknown error'), 'error');
                        }
                    })
                    .catch(error => {
                        hideLoading();
                        showNotification('Error saving diarization edits: ' + error.message, 'error');
                    });
            });
        }
        
        // Translation editor save button click
        const saveTranslationEditsBtn = document.getElementById('save-translation-edits-btn');
        if (saveTranslationEditsBtn) {
            saveTranslationEditsBtn.addEventListener('click', function() {
                console.log('Save translation edits button clicked');
                showLoading('Saving translation edits...');
                
                saveTranslationEdits()
                    .then(result => {
                        hideLoading();
                        if (result.success) {
                            showNotification('Translation edits saved successfully', 'success');
                        } else {
                            showNotification('Error saving translation edits: ' + (result.error || 'Unknown error'), 'error');
                        }
                    })
                    .catch(error => {
                        hideLoading();
                        showNotification('Error saving translation edits: ' + error.message, 'error');
                    });
            });
        }
    }
    
    // Handle file selection
    function handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            fileName.textContent = file.name;
            uploadBtn.disabled = false;
            
            // Create object URL for preview
            audioUrl = URL.createObjectURL(file);
            audioPlayer.src = audioUrl;
            audioPlayerContainer.classList.remove('hidden');
            
            // Store the file as blob
            audioBlob = file;
            
            // Note: We don't enable the continue button here
            // It will only be enabled after successful upload
        } else {
            // Reset if no file selected
            fileName.textContent = 'No file selected';
            uploadBtn.disabled = true;
            continueBtn.disabled = true;
            audioPlayerContainer.classList.add('hidden');
        }
    }
    
    // Upload audio file
    function uploadAudio() {
        if (!audioFile.files[0]) {
            showNotification('Please select a file.', 'error');
            return;
        }
        
        // Create form data
        const formData = new FormData();
        formData.append('audio', audioFile.files[0]);
        
        // Add target language if selected
        if (targetLanguageSelect.value) {
            formData.append('target_language', targetLanguageSelect.value);
        }
        
        // Show loading overlay
        showLoading('Uploading audio...');
        
        // Send request to upload endpoint
        fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Store session ID
                sessionId = data.session_id;
                
                // Mark as valid session with content
                hasValidSession = true;
                
                // Update download button visibility
                updateSessionDownloadButton();
                
                // Enable continue button
                continueBtn.disabled = false;
                
                // Proceed to language detection
                detectLanguageAndProcess();
            } else {
                hideLoading();
                showNotification(data.error || 'Error uploading audio.', 'error');
            }
        })
        .catch(error => {
            hideLoading();
            showNotification('Error uploading audio: ' + error.message, 'error');
        });
    }
    
    // Process video URL
    function processVideoUrl() {
        const url = videoUrl.value.trim();
        
        if (!url) {
            showNotification('Please enter a YouTube or Instagram URL.', 'error');
            return;
        }
        
        // Disable the button and add success indicator
        processVideoBtn.disabled = true;
        processVideoBtn.innerHTML = '<i class="fas fa-download"></i> Upload Video <i class="fas fa-check" style="color: #00FF00; margin-left: 8px; font-size: 1.2em; font-weight: bold;"></i>';
        
        // Add target language if selected
        const targetLang = targetLanguageSelect.value || 'english';
        
        // Show loading overlay
        showLoading('Processing video URL...');
        
        // Send request to process video URL endpoint
        fetch('/api/process_video_url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                video_url: url,
                target_language: targetLang
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Store session ID
                sessionId = data.session_id;
                
                // Mark as valid session with content
                hasValidSession = true;
                
                // Update download button visibility
                updateSessionDownloadButton();
                
                // Start polling for status updates
                pollProcessingStatus(sessionId);
                
                // Update UI to show success
                showNotification(`Successfully extracted audio from video.`, 'success');
                
                // Display audio player if path is provided
                if (data.audio_path) {
                    const audioUrl = `/outputs/${sessionId}/audio/${sessionId}.mp3`;
                    audioPlayer.src = audioUrl;
                    audioPlayerContainer.classList.remove('hidden');
                }
                
                // Enable continue button
                continueBtn.disabled = false;
                
                // Proceed to language detection
                detectLanguageAndProcess();
            } else {
                hideLoading();
                showNotification(data.error || 'Error processing video URL.', 'error');
                // Keep the button disabled but change the indicator to show an error occurred
                processVideoBtn.innerHTML = '<i class="fas fa-download"></i> Upload Video <i class="fas fa-exclamation-circle" style="color: #FF0000; margin-left: 8px; font-size: 1.2em; font-weight: bold;"></i>';
            }
        })
        .catch(error => {
            hideLoading();
            console.error('Error processing video URL:', error);
            showNotification('Error processing video URL. Please try again.', 'error');
            // Keep the button disabled but change the indicator to show an error occurred
            processVideoBtn.innerHTML = '<i class="fas fa-download"></i> Upload Video <i class="fas fa-exclamation-circle" style="color: #FF0000; margin-left: 8px; font-size: 1.2em; font-weight: bold;"></i>';
        });
    }
    
    // Toggle recording
    function toggleRecording() {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            // Stop recording
            stopRecording();
        } else {
            // Start recording
            startRecording();
        }
    }
    
    // Start recording
    function startRecording() {
        // Request microphone access
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                // Create media recorder
                mediaRecorder = new MediaRecorder(stream);
                recordedChunks = [];
                
                // Handle data available event
                mediaRecorder.addEventListener('dataavailable', e => {
                    if (e.data.size > 0) {
                        recordedChunks.push(e.data);
                    }
                });
                
                // Handle recording stop event
                mediaRecorder.addEventListener('stop', () => {
                    // Create blob from recorded chunks
                    audioBlob = new Blob(recordedChunks, { type: 'audio/webm' });
                    audioUrl = URL.createObjectURL(audioBlob);
                    
                    // Update audio player
                    audioPlayer.src = audioUrl;
                    audioPlayerContainer.classList.remove('hidden');
                    
                    // Upload the recorded audio
                    uploadRecordedAudio();
                });
                
                // Start recording
                mediaRecorder.start();
                
                // Update UI
                recordBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Recording';
                recordBtn.classList.add('recording');
                recordingTimer.classList.remove('hidden');
                
                // Start timer
                recordingSeconds = 0;
                updateRecordingTimer();
                recordingInterval = setInterval(updateRecordingTimer, 1000);
            })
            .catch(error => {
                showNotification('Error accessing microphone: ' + error.message, 'error');
            });
    }
    
    // Stop recording
    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            
            // Stop all tracks in the stream
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
            
            // Update UI
            recordBtn.innerHTML = '<i class="fas fa-microphone"></i> Start Recording';
            recordBtn.classList.remove('recording');
            
            // Stop timer
            clearInterval(recordingInterval);
        }
    }
    
    // Update recording timer
    function updateRecordingTimer() {
        recordingSeconds++;
        const minutes = Math.floor(recordingSeconds / 60).toString().padStart(2, '0');
        const seconds = (recordingSeconds % 60).toString().padStart(2, '0');
        recordingTimer.textContent = `${minutes}:${seconds}`;
    }
    
    // Upload recorded audio
    function uploadRecordedAudio() {
        showLoading('Uploading recorded audio...');
        
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        formData.append('session_id', sessionId);
        
        fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                showNotification('Recording uploaded successfully', 'success');
                continueBtn.disabled = false; // Enable continue button after successful upload
            } else {
                showNotification('Error uploading recording: ' + data.error, 'error');
            }
        })
        .catch(error => {
            hideLoading();
            showNotification('Error uploading recording: ' + error.message, 'error');
        });
    }
    
    // Update speaker genders based on number of speakers
    function updateSpeakerGenders() {
        const count = parseInt(numSpeakers.value);
        const language = targetLanguageSelect.value;
        
        // Clear container
        document.getElementById('speaker-details-container').innerHTML = '';
        
        // Add speaker details for each speaker
        for (let i = 1; i <= count; i++) {
            const div = document.createElement('div');
            div.className = 'speaker-detail';
            div.setAttribute('data-speaker-id', `speaker_${i}`);
            div.innerHTML = `
                <h4>Speaker ${i}</h4>
                <div class="form-group">
                    <label for="speaker-gender-${i}">Gender:</label>
                    <select id="speaker-gender-${i}" class="form-control speaker-gender-select" data-speaker="${i}">
                        <option value="M">Male</option>
                        <option value="F">Female</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="speaker-name-${i}">Name (Optional):</label>
                    <input type="text" id="speaker-name-${i}" class="form-control speaker-name-input" data-speaker="${i}" placeholder="Enter name">
                </div>
                <div class="form-group">
                    <label for="speaker-voice-${i}">Voice (Optional):</label>
                    <select id="speaker-voice-${i}" class="form-control speaker-voice-select" data-speaker="${i}">
                        <option value="">Loading voices...</option>
                    </select>
                </div>
            `;
            document.getElementById('speaker-details-container').appendChild(div);
        }
        
        // Load voices for the current language
        loadVoiceOptions(language);
    }
    
    // Load voice options based on selected language
    function loadVoiceOptions(language) {
        // Show loading state
        document.querySelectorAll('.speaker-voice-select').forEach(select => {
            select.innerHTML = '<option value="">Loading voices...</option>';
        });
        
        // Fetch available voices based on language
        fetch(`/api/get-voices-by-language?language=${language}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const voices = data.voices;
                    
                    // Update all voice selects
                    document.querySelectorAll('.speaker-voice-select').forEach(select => {
                        // Clear existing options
                        select.innerHTML = '';
                        
                        // Add default option
                        const defaultOption = document.createElement('option');
                        defaultOption.value = '';
                        defaultOption.textContent = 'Select a voice (optional)';
                        select.appendChild(defaultOption);
                        
                        // Add voice options
                        voices.forEach(voice => {
                            const option = document.createElement('option');
                            option.value = voice.id;
                            option.textContent = `${voice.name} (${voice.gender})`;
                            select.appendChild(option);
                        });
                    });
                } else {
                    console.error('Error loading voices:', data.error);
                    document.querySelectorAll('.speaker-voice-select').forEach(select => {
                        select.innerHTML = '<option value="">No voices available</option>';
                    });
                }
            })
            .catch(error => {
                console.error('Error fetching voices:', error);
                document.querySelectorAll('.speaker-voice-select').forEach(select => {
                    select.innerHTML = '<option value="">Error loading voices</option>';
                });
            });
    }
    
    // Detect language
    function detectLanguage() {
        console.log('Detecting language for session:', sessionId);
        
        // Check if DOM elements exist before using them
        const detectedLanguageEl = document.getElementById('detected-language');
        const sourceLanguageEl = document.getElementById('source-language');
        
        console.log('DOM elements check:', {
            detectedLanguageEl: !!detectedLanguageEl,
            sourceLanguageEl: !!sourceLanguageEl
        });
        
        return new Promise((resolve, reject) => {
            fetch('/api/detect_language', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log('Language detection API response:', data);
                
                if (data.success) {
                    detectedLang = data.language;
                    
                    // Safely update DOM elements if they exist
                    if (detectedLanguageEl) {
                        detectedLanguageEl.textContent = data.language_name || data.language;
                    } else {
                        console.warn('detectedLanguage element not found in DOM');
                    }
                    
                    if (sourceLanguageEl) {
                        sourceLanguageEl.textContent = data.language_name || data.language;
                    } else {
                        console.warn('sourceLanguage element not found in DOM');
                    }
                    
                    resolve(data);
                } else {
                    console.error('Error detecting language:', data.error);
                    
                    // Safely update DOM element if it exists
                    if (detectedLanguageEl) {
                        detectedLanguageEl.textContent = 'Detection failed';
                    }
                    
                    reject(new Error(data.error || 'Language detection failed'));
                }
            })
            .catch(error => {
                console.error('Error detecting language:', error);
                
                // Safely update DOM element if it exists
                if (detectedLanguageEl) {
                    detectedLanguageEl.textContent = 'Detection failed';
                }
                
                reject(error);
            });
        });
    }
    
    // Fetch transcription
    function fetchTranscription() {
        console.log('Fetching transcription for session:', sessionId);
        
        // Get target language
        const targetLanguage = document.getElementById('target-language-select').value;
        console.log('Target language:', targetLanguage);
        
        // Get background music preference
        const preserveBackgroundMusicElement = document.getElementById('preserve-background-music');
        const preserveBackgroundMusic = preserveBackgroundMusicElement ? preserveBackgroundMusicElement.checked : false;
        console.log('Preserve background music:', preserveBackgroundMusic);
        
        // Create form data
        const formData = new FormData();
        
        // Add session ID
        formData.append('session_id', sessionId);
        
        // Add target language
        formData.append('target_language', targetLanguage);
        
        // Add background music preference - explicitly convert to string 'true' or 'false'
        formData.set('preserve_background_music', preserveBackgroundMusic ? 'true' : 'false');
        console.log('Preserve background music value being sent:', preserveBackgroundMusic ? 'true' : 'false');
        
        // Add speaker information
        const numSpeakers = document.getElementById('num-speakers').value;
        formData.append('num_speakers', numSpeakers);
        
        return fetch('/api/transcribe', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching transcription:', data.error);
                throw new Error(data.error);
            }
            
            console.log('Transcription fetched successfully');
            
            // Store transcription in textarea
            transcriptionText.value = data.transcription;
            console.log('Transcription text set in textarea');
            
            return data;
        });
    }
    
    // Load diarization editor
    function loadDiarizationEditor(sessionId) {
        console.log('Loading diarization editor for session:', sessionId);
        
        // If no session ID provided, use the global one
        if (!sessionId && window.sessionId) {
            sessionId = window.sessionId;
            console.log('Using global session ID:', sessionId);
        }
        
        if (!sessionId) {
            console.error('No session ID available for loading diarization editor');
            return Promise.reject(new Error('No session ID available'));
        }
        
        const editorContainer = document.getElementById('diarization-editor');
        if (!editorContainer) {
            console.error('Diarization editor container not found');
            return Promise.reject(new Error('Editor container not found'));
        }
        
        const editorContent = editorContainer.querySelector('.card-body');
        if (!editorContent) {
            console.error('Diarization editor content container not found');
            return Promise.reject(new Error('Editor content container not found'));
        }
        
        // Clear any existing content
        editorContent.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div><p>Loading diarization data...</p></div>';
        
        return fetch(`/api/get_diarization?session_id=${sessionId}`)
            .then(response => {
                console.log('Diarization fetch response status:', response.status);
                if (!response.ok) {
                    if (response.status === 404) {
                        console.warn('Diarization data not found, showing empty editor');
                        editorContent.innerHTML = '<div class="alert alert-info">No diarization data available yet. Please wait for processing to complete.</div>';
                        return null;
                    }
                    throw new Error(`HTTP error ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Diarization editor data received:', JSON.stringify(data, null, 2));
                if (!data) return null;
                
                if (data.error) {
                    console.error('Error loading diarization data:', data.error);
                    editorContent.innerHTML = `<div class="alert alert-danger">Error loading diarization data: ${data.error}</div>`;
                    return null;
                }
                
                // Check if we have segments
                const segments = data.segments || [];
                if (segments.length === 0) {
                    console.warn('No segments found in diarization data');
                    editorContent.innerHTML = '<div class="alert alert-info">No diarization segments available.</div>';
                    return data;
                }
                
                console.log(`Rendering diarization editor with ${segments.length} segments`);
                
                // Render the diarization editor with the data
                renderDiarizationEditor(segments, editorContent);
                return data;
            })
            .catch(error => {
                console.error('Error loading diarization editor:', error);
                editorContent.innerHTML = `<div class="alert alert-danger">Error loading diarization editor: ${error.message}</div>`;
                return null;
            });
    }
    
    // Render diarization editor with segments
    function renderDiarizationEditor(segments, container) {
        console.log('Rendering diarization editor with segments:', segments ? segments.length : 0);
        
        if (!container) {
            container = document.querySelector('#diarization-editor .card-body');
        }
        
        if (!segments || segments.length === 0) {
            container.innerHTML = '<div class="alert alert-info">No diarization segments available.</div>';
            return;
        }
        
        // Clear container
        container.innerHTML = '';
        
        // Create timeline visualization
        const timelineEl = document.createElement('div');
        timelineEl.className = 'diarization-timeline mb-4';
        
        // Calculate total duration
        const totalDuration = segments.reduce((max, seg) => 
            Math.max(max, parseFloat(seg.end_time || seg.end || 0)), 0);
        
        console.log('Total duration calculated:', totalDuration);
        
        // Create segments in timeline
        segments.forEach((segment, index) => {
            console.log(`Processing segment ${index}:`, JSON.stringify(segment));
            
            try {
                const start = parseFloat(segment.start_time || segment.start || 0);
                const end = parseFloat(segment.end_time || segment.end || 0);
                const duration = end - start;
                const width = (duration / totalDuration) * 100;
                const left = (start / totalDuration) * 100;
                
                console.log(`Segment ${index} calculated values:`, { start, end, duration, width, left });
                
                const segmentEl = document.createElement('div');
                segmentEl.className = 'timeline-segment';
                segmentEl.style.width = `${width}%`;
                segmentEl.style.left = `${left}%`;
                segmentEl.setAttribute('data-segment-id', segment.segment_id);
                segmentEl.setAttribute('data-start', start);
                segmentEl.setAttribute('data-end', end);
                
                // Assign a color based on speaker
                const speakerId = segment.speaker || 'unknown';
                segmentEl.classList.add(`speaker-${speakerId.replace(/[^a-zA-Z0-9]/g, '-')}`);
                
                timelineEl.appendChild(segmentEl);
            } catch (error) {
                console.error(`Error processing segment ${index}:`, error, segment);
            }
        });
        
        container.appendChild(timelineEl);
        
        // Create segment editors
        segments.forEach((segment, index) => {
            try {
                console.log(`Creating editor for segment ${index}:`, JSON.stringify(segment));
                
                const start = parseFloat(segment.start_time || segment.start || 0);
                const end = parseFloat(segment.end_time || segment.end || 0);
                const text = segment.text || '';
                const speakerId = segment.speaker || 'unknown';
                
                const segmentRow = document.createElement('div');
                segmentRow.className = 'segment-row mb-3';
                segmentRow.setAttribute('data-segment-id', segment.segment_id);
                
                // Format time as MM:SS
                const formatTime = (seconds) => {
                    const mins = Math.floor(seconds / 60);
                    const secs = Math.floor(seconds % 60);
                    return `${mins}:${secs.toString().padStart(2, '0')}`;
                };
                
                segmentRow.innerHTML = `
                    <div class="segment-header mb-2">
                        <span class="segment-time">#${index + 1} | ${formatTime(start)}-${formatTime(end)}</span>
                        <select class="speaker-select form-select form-select-sm" data-segment-id="${segment.segment_id}">
                            <option value="SPEAKER_00" ${speakerId === 'SPEAKER_00' ? 'selected' : ''}>SPEAKER_00</option>
                            <option value="SPEAKER_01" ${speakerId === 'SPEAKER_01' ? 'selected' : ''}>SPEAKER_01</option>
                            <option value="SPEAKER_02" ${speakerId === 'SPEAKER_02' ? 'selected' : ''}>SPEAKER_02</option>
                            <option value="SPEAKER_03" ${speakerId === 'SPEAKER_03' ? 'selected' : ''}>SPEAKER_03</option>
                            <option value="SPEAKER_04" ${speakerId === 'SPEAKER_04' ? 'selected' : ''}>SPEAKER_04</option>
                        </select>
                    </div>
                    <textarea class="segment-text form-control" data-segment-id="${segment.segment_id}" rows="2">${text}</textarea>
                `;
                
                container.appendChild(segmentRow);
                
                // Apply transliteration to the newly created textarea
                const textArea = segmentRow.querySelector('.segment-text');
                if (textArea && detectedLang && detectedLang !== 'english') {
                    console.log(`Applying transliteration to segment ${index} with language: ${detectedLang}`);
                    applyTransliteration(textArea, detectedLang);
                }
            } catch (error) {
                console.error(`Error creating editor for segment ${index}:`, error, segment);
            }
        });
        
        // Add save button if not already present
        if (!document.getElementById('save-diarization-btn')) {
            const saveRow = document.createElement('div');
            saveRow.className = 'd-flex justify-content-end mt-3';
            saveRow.innerHTML = `
                <button id="save-diarization-btn" class="btn btn-primary btn-sm">
                    Save Edits
                </button>
                <span class="ms-2 text-muted">Changes will also be saved when you click "Save & Continue"</span>
            `;
            container.appendChild(saveRow);
            
            // Add event listener to save button
            const saveDiarizationBtn = document.getElementById('save-diarization-btn');
            if (saveDiarizationBtn) {
                saveDiarizationBtn.addEventListener('click', function() {
                    console.log('Save diarization button clicked');
                    showLoading('Saving diarization edits...');
                    
                    saveDiarizationEdits()
                        .then(result => {
                            hideLoading();
                            if (result.success) {
                                showNotification('Diarization edits saved successfully', 'success');
                            } else {
                                showNotification('Error saving diarization edits: ' + (result.error || 'Unknown error'), 'error');
                            }
                        })
                        .catch(error => {
                            hideLoading();
                            showNotification('Error saving diarization edits: ' + error.message, 'error');
                        });
                });
            }
        }
    }
    
    // Load translation editor
    function loadTranslationEditor(sessionId) {
        console.log('Loading translation editor...');
        
        const reliableSessionId = getReliableSessionId();
        if (!reliableSessionId) {
            console.error('No session ID available for loading translation editor');
            showNotification('Error loading translation editor: No session ID available', 'error');
            return;
        }
        
        console.log('Loading translation editor with session ID:', reliableSessionId);
        
        // Clear any existing content
        const editorContainer = document.getElementById('translation-editor-container');
        if (!editorContainer) {
            console.error('Translation editor container not found');
            return;
        }
        
        editorContainer.innerHTML = '<div class="loading">Loading translation data...</div>';
        
        // Fetch translation data
        fetch(`/api/get_translation?session_id=${reliableSessionId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Translation data loaded:', data);
                
                // Render the translation editor
                renderTranslationEditor(data.segments, editorContainer);
                
                // Set up the save button handler
                setupSaveTranslationHandler();
            })
            .catch(error => {
                console.error('Error loading translation data:', error);
                editorContainer.innerHTML = `<div class="error">Error loading translation data: ${error.message}</div>`;
            });
    }
    
    // Set up save translation handler
    function setupSaveTranslationHandler() {
        const saveEditsBtn = document.getElementById('save-translation-edits');
        if (!saveEditsBtn) {
            console.error('Save translation edits button not found');
            return;
        }
        
        // Remove any existing event listeners by cloning and replacing
        const newSaveBtn = saveEditsBtn.cloneNode(true);
        saveEditsBtn.parentNode.replaceChild(newSaveBtn, saveEditsBtn);
        
        // Add event listener to the new button
        newSaveBtn.addEventListener('click', function(event) {
            event.preventDefault();
            console.log('Save Translation Edits button clicked');
            saveTranslationEdits();
        });
        
        console.log('Save translation handler set up');
    }
    
    // Render translation editor with segments
    function renderTranslationEditor(segments, container) {
        console.log('Rendering translation editor with segments:', segments ? segments.length : 0);
        
        if (!container) {
            container = document.querySelector('#translation-editor-container');
        }
        
        if (!segments || segments.length === 0) {
            container.innerHTML = '<div class="alert alert-info">No translation segments available.</div>';
            return;
        }
        
        // Create editor content
        let html = '<div class="translation-timeline">';
        
        // Add timeline visualization
        segments.forEach((segment, index) => {
            const startPercent = (segment.start_time / segments[segments.length - 1].end_time) * 100;
            const widthPercent = ((segment.end_time - segment.start_time) / segments[segments.length - 1].end_time) * 100;
            const speakerClass = `speaker-${segment.speaker.replace('SPEAKER_', '')}`;
            
            html += `<div class="timeline-segment ${speakerClass}" 
                        style="left: ${startPercent}%; width: ${widthPercent}%;" 
                        title="Speaker ${segment.speaker.replace('SPEAKER_', '')}: ${segment.start_time.toFixed(1)}s - ${segment.end_time.toFixed(1)}s">
                    </div>`;
        });
        
        html += '</div>';
        
        // Add segments for editing
        segments.forEach((segment, index) => {
            const speakerClass = `speaker-${segment.speaker.replace('SPEAKER_', '')}`;
            const segmentId = segment.segment_id;
            const originalText = segment.text || '';
            const translatedText = segment.translated_text || '';
            
            html += `
            <div class="translation-segment ${speakerClass}" data-segment-id="${segmentId}">
                <div class="segment-header">
                    <span class="segment-number">#${index + 1} | ${segment.start_time.toFixed(1)}-${segment.end_time.toFixed(1)}</span>
                    <span class="segment-speaker">${segment.speaker}</span>
                </div>
                <div class="segment-content">
                    <div class="original-text">
                        <label>Original:</label>
                        <div class="original-text-content">${originalText}</div>
                    </div>
                    <div class="translation-container">
                        <label>Translation:</label>
                        <textarea class="translation-text" data-original-text="${translatedText}" data-language="${targetLanguageSelect.value}">${translatedText}</textarea>
                    </div>
                </div>
            </div>`;
        });
        
        // Add save button
        html += `
        <div class="translation-editor-actions">
            <button id="save-translation-edits" class="btn btn-primary">Save Edits</button>
            <span class="save-note">Changes will also be saved when you click "Save & Continue"</span>
        </div>`;
        
        // Set the HTML content
        container.innerHTML = html;
        
        // Set up transliteration for all translation text areas
        setupTransliteration();
    }
    
    // Set up transliteration for translation text areas
    function setupTransliteration() {
        console.log('Setting up transliteration for translation text areas');
        const textareas = document.querySelectorAll('.translation-text');
        console.log(`Found ${textareas.length} translation text areas`);
        
        textareas.forEach((textarea, index) => {
            const language = textarea.dataset.language;
            console.log(`Textarea ${index}: Language = ${language}`);
            
            if (language && language !== 'english') {
                // Use the existing applyTransliteration function
                applyTransliteration(textarea, language);
                
                // Add event listener for updating the full translation text
                textarea.addEventListener('input', function() {
                    // Update the full translation text when individual segments are edited
                    updateFullTranslationText();
                });
            } else {
                console.log(`Skipping transliteration for textarea ${index} with language ${language}`);
            }
        });
    }
    
    // Update the full translation text based on segment translations
    function updateFullTranslationText() {
        const translationTextarea = document.getElementById('translation-text');
        if (!translationTextarea) {
            console.error('Translation textarea not found');
            return;
        }
        
        const segments = [];
        document.querySelectorAll('.translation-text').forEach(textarea => {
            segments.push(textarea.value.trim());
        });
        
        translationTextarea.value = segments.join(' ');
        console.log('Updated full translation text with segment edits');
    }
    
    // Save translation edits
    function saveTranslationEdits() {
        const reliableSessionId = getReliableSessionId();
        if (!reliableSessionId) {
            showNotification('Error saving translation edits: No session ID available', 'error');
            return;
        }
        
        console.log('Saving translation edits with session ID:', reliableSessionId);
        
        // Get all edited translations
        const updates = {};
        document.querySelectorAll('.translation-segment').forEach(segment => {
            const segmentId = segment.dataset.segmentId;
            const translationInput = segment.querySelector('.translation-text');
            
            if (translationInput && translationInput.dataset.originalText !== translationInput.value) {
                updates[segmentId] = {
                    translated_text: translationInput.value
                };
            }
        });
        
        if (Object.keys(updates).length === 0) {
            console.log('No changes to save');
            return;
        }
        
        showLoading('Saving translation edits...');
        
        fetch('/api/save_translation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: reliableSessionId,
                updates: updates
            })
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                showNotification('Translation edits saved successfully', 'success');
                
                // Update the full translation text
                updateFullTranslationText();
                
                // Mark all inputs as having their original text updated
                document.querySelectorAll('.translation-segment .translation-text').forEach(input => {
                    input.dataset.originalText = input.value;
                });
            } else {
                showNotification('Error saving translation edits: ' + data.error, 'error');
            }
        })
        .catch(error => {
            hideLoading();
            showNotification('Error saving translation edits: ' + error.message, 'error');
        });
    }
    
    // Save translation
    function saveTranslation() {
        console.log('Saving translation...');
        showLoading('Saving translation...');
        
        // First save translation edits if available
        const translationEditorContent = document.querySelector('#translation-editor-container');
        if (translationEditorContent && translationEditorContent.querySelector('.segment-row')) {
            // Save translation edits first
            saveTranslationEdits().then(result => {
                continueTranslationSave();
            }).catch(error => {
                hideLoading();
                showNotification('Error saving translation edits: ' + error.message, 'error');
            });
        } else {
            // No translation edits to save, proceed with normal save
            continueTranslationSave();
        }
    }
    
    // Continue with translation save after edits are saved
    function continueTranslationSave() {
        console.log('Continuing to synthesis step after saving translation edits');
        
        // Skip the redundant API call - edits are already saved by saveTranslationEdits()
        
        // Hide the loading overlay first
        hideLoading();
        
        // Show a success message and proceed to the synthesis step
        showNotification('Translation saved successfully', 'success');
        showStep(stepSynthesis);
        prepareSynthesis();
    }
    
    // Transliterate text from Roman script to the specified language script
    function transliterateText(text, language, callback) {
        console.log(`Transliteration request - Text: "${text}", Language: ${language}`);
        
        if (!text || text.trim() === '') {
            console.log('Empty text, skipping transliteration');
            if (callback) callback(text);
            return;
        }
        
        fetch('/api/transliterate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: text,
                language: language
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.transliterated_text) {
                console.log(`Transliteration success - Original: "${text}", Result: "${data.transliterated_text}"`);
                if (callback) callback(data.transliterated_text);
            } else {
                console.error('Transliteration error:', data.error);
                console.error('API Response:', data);
                if (callback) callback(text); // Return original text on error
            }
        })
        .catch(error => {
            console.error('Error calling transliteration API:', error);
            if (callback) callback(text); // Return original text on error
        });
    }
    
    // Apply transliteration to a text area with debounce
    function applyTransliteration(textArea, language) {
        let typingTimer;
        const doneTypingInterval = 500; // ms - time to wait after user stops typing
        const contextWindow = 50; // characters to consider before cursor
        let previousValue = textArea.value;
        const wordBoundaryChars = [' ', ',', '.', '!', '?', '|'];
        
        textArea.addEventListener('input', function(event) {
            clearTimeout(typingTimer);
            const newText = this.value;
            const cursorPosition = this.selectionStart;
            // Only proceed if something changed
            if (newText !== previousValue) {
                // Determine the window to transliterate
                const windowStart = Math.max(0, cursorPosition - contextWindow);
                const textBeforeWindow = newText.substring(0, windowStart);
                const textWindow = newText.substring(windowStart, cursorPosition);
                const textAfterCursor = newText.substring(cursorPosition);
                // Check if the last typed character is a word boundary
                const lastChar = newText[cursorPosition - 1];
                if (wordBoundaryChars.includes(lastChar)) {
                    // Immediate transliteration on word boundary
                    transliterateText(textWindow, language, (transliteratedWindow) => {
                        const lengthDiff = transliteratedWindow.length - textWindow.length;
                        this.value = textBeforeWindow + transliteratedWindow + textAfterCursor;
                        const newCursorPos = cursorPosition + lengthDiff;
                        this.selectionStart = this.selectionEnd = newCursorPos;
                        previousValue = this.value;
                    });
                } else {
                    // Debounced transliteration
                    typingTimer = setTimeout(() => {
                        if (textWindow.length > 0) {
                            transliterateText(textWindow, language, (transliteratedWindow) => {
                                const lengthDiff = transliteratedWindow.length - textWindow.length;
                                this.value = textBeforeWindow + transliteratedWindow + textAfterCursor;
                                const newCursorPos = cursorPosition + lengthDiff;
                                this.selectionStart = this.selectionEnd = newCursorPos;
                                previousValue = this.value;
                            });
                        }
                    }, doneTypingInterval);
                }
            }
        });
    }
    
    // Save diarization edits
    function saveDiarizationEdits() {
        console.log('Saving diarization edits');
        showLoading('Saving changes...');
        
        const updates = {};
        document.querySelectorAll('.segment-row').forEach(row => {
            const segId = row.dataset.segmentId;
            const speakerId = row.querySelector('.speaker-select').value;
            const textContent = row.querySelector('.segment-text').value;
            
            console.log(`Segment ${segId} - Speaker: ${speakerId}, Text: "${textContent}"`);
            
            // Ensure speaker ID is in the correct format (SPEAKER_XX)
            // This maintains compatibility with the standardized speaker ID format
            let formattedSpeakerId = speakerId;
            if (speakerId && !speakerId.startsWith('SPEAKER_')) {
                // Extract number from UI format (e.g., "speaker_1" → "1")
                const match = speakerId.match(/(\d+)$/);
                if (match) {
                    // Format as diarization speaker_id (e.g., "1" → "SPEAKER_00")
                    const num = parseInt(match[1], 10);
                    formattedSpeakerId = `SPEAKER_${num.toString().padStart(2, '0')}`;
                    console.log(`Converted speaker ID: ${speakerId} → ${formattedSpeakerId}`);
                }
            }
            
            updates[segId] = {
                speaker: formattedSpeakerId,
                text: textContent
            };
        });
        
        console.log('Diarization updates:', updates);
        console.log('Complete updates payload:', JSON.stringify({
            session_id: sessionId,
            updates: updates
        }));
        
        return fetch('/api/api_save_diarization', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                session_id: sessionId,
                updates: updates
            })
        })
        .then(response => response.json())
        .catch(error => {
            console.error('Save failed:', error);
            return {success: false, error: 'Network error'};
        });
    }
    
    // Save transcription
    function saveTranscription() {
        console.log('Saving transcription...');
        showLoading('Saving transcription...');
        
        // First save diarization edits if available
        const diarizationEditorContent = document.querySelector('#diarization-editor .card-body');
        if (diarizationEditorContent && diarizationEditorContent.querySelector('.segment-row')) {
            // Save diarization edits first
            saveDiarizationEdits().then(result => {
                if (result.success) {
                    // Continue with normal transcription save
                    continueTranscriptionSave();
                } else {
                    hideLoading();
                    showNotification('Error saving diarization edits: ' + (result.error || 'Unknown error'), 'error');
                }
            }).catch(error => {
                hideLoading();
                showNotification('Error saving diarization edits: ' + error.message, 'error');
            });
        } else {
            // No diarization edits, proceed with normal save
            continueTranscriptionSave();
        }
    }
    
    // Continue with normal transcription save
    function continueTranscriptionSave() {
        console.log('Continuing with transcription save...');
        
        // The /api/transcribe endpoint is used for both fetching and saving transcription
        fetch('/api/transcribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                transcription: transcriptionText.value
            })
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                showNotification('Transcription saved', 'success');
                
                // Proceed to translation step
                console.log('Proceeding to translation step');
                showStep(stepTranslation);
                prepareTranslation();
            } else {
                showNotification('Error saving transcription: ' + data.error, 'error');
            }
        })
        .catch(error => {
            hideLoading();
            showNotification('Error saving transcription: ' + error.message, 'error');
        });
    }
    
    // Prepare translation
    function prepareTranslation() {
        console.log('Preparing translation step...');
        
        // Update the language display
        sourceLanguage.textContent = detectedLang ? detectedLang.charAt(0).toUpperCase() + detectedLang.slice(1) : 'Auto';
        targetLanguage.textContent = targetLanguageSelect.value.charAt(0).toUpperCase() + targetLanguageSelect.value.slice(1);
        
        // Load the translation editor
        loadTranslationEditor(sessionId);
        
        // Call translateText to get the translation
        translateText();
    }
    
    // Translate text
    function translateText() {
        console.log('Translating text...');
        showLoading('Translating...');
        
        fetch('/api/translate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                session_id: sessionId,
                target_language: targetLanguageSelect.value
            })
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.success) {
                translationText.value = data.translation;
                showNotification('Translation complete', 'success');
                
                // Load the translation editor with the translated data
                loadTranslationEditor(sessionId);
                
                // Update synthesis language
                synthesisLanguage.textContent = targetLanguageSelect.value.charAt(0).toUpperCase() + targetLanguageSelect.value.slice(1);
            } else {
                showNotification('Translation failed: ' + data.error, 'error');
            }
        })
        .catch(error => {
            hideLoading();
            showNotification('Translation error: ' + error.message, 'error');
        });
    }
    
    // Prepare synthesis
    function prepareSynthesis() {
        // Update UI
        synthesisProgress.classList.add('hidden');
        outputAudioPlayerContainer.classList.add('hidden');
        validateBtn.classList.add('hidden');
    }
    
    // Synthesize speech
    function synthesizeSpeech() {
        showLoading('Synthesizing speech...');
        synthesisProgress.classList.remove('hidden');
        
        // Get speaker details
        const speakerDetails = [];
        document.querySelectorAll('.speaker-detail').forEach(speakerDiv => {
            const speakerId = speakerDiv.getAttribute('data-speaker-id');
            const speakerNum = speakerId.split('_')[1];
            
            speakerDetails.push({
                speaker_id: speakerId,
                gender: document.getElementById(`speaker-gender-${speakerNum}`).value,
                name: document.getElementById(`speaker-name-${speakerNum}`).value || null,
                voice_id: document.getElementById(`speaker-voice-${speakerNum}`).value || null
            });
        });
        
        // Always use time-aligned endpoint
        const endpoint = '/api/synthesize-time-aligned';
        
        fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                target_language: targetLanguageSelect.value,
                num_speakers: parseInt(numSpeakers.value),
                speaker_details: speakerDetails,
                options: {
                    bit_rate: 128000,
                    sample_rate: 44100
                }
            })
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            synthesisProgress.classList.add('hidden');
            
            if (data.success) {
                if (!sessionId) {
                    showNotification('Session ID not found. Cannot play or download audio.', 'error');
                    return;
                }
                const targetLang = targetLanguageSelect.value.toLowerCase();
                const fileExtension = targetLang === 'hindi' ? 'mp3' : 'wav';
                const audioUrl = `/outputs/${sessionId}/tts/final_output_${targetLang}_${sessionId}.${fileExtension}`;
                console.log('sessionId:', sessionId, 'targetLang:', targetLang, 'audioUrl:', audioUrl);
                outputAudioPlayer.src = audioUrl;
                outputAudioPlayerContainer.classList.remove('hidden');
                downloadLink.href = audioUrl;
                downloadLink.download = `translated_audio_${targetLang}.${fileExtension}`;
                validateBtn.classList.remove('hidden');
                showNotification('Speech synthesized successfully', 'success');
            } else {
                showNotification('Error synthesizing speech: ' + data.error, 'error');
            }
        })
        .catch(error => {
            hideLoading();
            synthesisProgress.classList.add('hidden');
            showNotification('Error synthesizing speech: ' + error.message, 'error');
        });
    }
    
    // Validate output
    function validateOutput() {
        showLoading('Validating output...');
        
        fetch('/api/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.success) {
                // Removed similarity score update since the element no longer exists
                
                // Update audio extraction metrics
                const audioExtractionScore = Math.round(data.validation_result.audio_extraction_score || 0);
                const bertScore = Math.round(data.validation_result.metrics.bert_segment_weighted || 0);
                const bleuScore = Math.round(data.validation_result.metrics.bleu_segment_weighted || 0);
                
                // Update the DOM elements
                document.getElementById('audio-extraction-score').textContent = audioExtractionScore;
                document.getElementById('bert-score').textContent = bertScore + '/100';
                document.getElementById('bleu-score').textContent = bleuScore + '/100';
                
                // Update progress bars
                document.getElementById('bert-progress').style.width = bertScore + '%';
                document.getElementById('bleu-progress').style.width = bleuScore + '%';
                
                // Update the score circle color based on the score
                const audioExtractionScoreCircle = document.getElementById('audio-extraction-score').parentElement;
                if (audioExtractionScore >= 80) {
                    audioExtractionScoreCircle.style.backgroundColor = '#10b981'; // Green for good score
                } else if (audioExtractionScore >= 60) {
                    audioExtractionScoreCircle.style.backgroundColor = '#f59e0b'; // Yellow for medium score
                } else {
                    audioExtractionScoreCircle.style.backgroundColor = '#ef4444'; // Red for low score
                }

                // Removed composite score section and definitions as requested
                
                // Update audio players
                // --- Audio player source path fix (robust) ---
                // Determine file extension based on target language (default: wav, Hindi: mp3)
                const targetLang = targetLanguageSelect.value ? targetLanguageSelect.value.toLowerCase() : 'unknown';
                const fileExtension = targetLang === 'hindi' ? 'mp3' : 'wav';
                // Input audio path: /outputs/session_id/audio/session_id.<filetype>
                // Fallback: If not found, try .wav as default
                let inputAudioPath = `/outputs/${sessionId}/audio/${sessionId}.${fileExtension}`;
                fetch(inputAudioPath, { method: 'HEAD' })
                  .then(resp => {
                    if (!resp.ok && fileExtension !== 'wav') {
                      // fallback to wav if not found and not already wav
                      inputAudioPath = `/outputs/${sessionId}/audio/${sessionId}.wav`;
                    }
                    comparisonInputAudio.src = inputAudioPath;
                  })
                  .catch(() => {
                    // fallback to wav if fetch fails
                    comparisonInputAudio.src = `/outputs/${sessionId}/audio/${sessionId}.wav`;
                  });
                // Output audio path: /outputs/session_id/tts/final_output_<target_language>_session_id.<filetype>
                comparisonOutputAudio.src = `/outputs/${sessionId}/tts/final_output_${targetLang}_${sessionId}.${fileExtension}`;
                // --- End audio player source path fix (robust) ---
                
                // Removed color update for similarity score circle
            } else {
                showNotification('Error validating output: ' + data.error, 'error');
            }
        })
        .catch(error => {
            hideLoading();
            showNotification('Error validating output: ' + error.message, 'error');
        });
    }
    
    // Show step
    function showStep(step) {
        console.log('Showing step:', step ? step.id : 'none');
        
        // Hide all steps
        [stepInput, stepTranscription, stepTranslation, stepSynthesis, stepValidation].forEach(s => {
            if (s) {
                s.style.display = 'none';
                console.log('Hiding step:', s.id);
            }
        });
        
        // Show the requested step
        if (step) {
            console.log('Setting display to block for step:', step.id);
            step.style.display = 'block';
            
            // If showing transcription step, load diarization editor
            if (step === stepTranscription && sessionId) {
                console.log('Transcription step shown, loading diarization editor');
                loadDiarizationEditor(sessionId);
            }
            
            // If showing translation step, load translation editor
            if (step === stepTranslation && sessionId) {
                console.log('Translation step shown, loading translation editor');
                loadTranslationEditor(sessionId);
            }
        }
    }
    
    // Show loading overlay
    // Variable to store the status polling interval
    let statusPollingInterval = null;
    
    /**
     * Poll the server for processing status updates
     * @param {string} sessionId - The session ID to check status for
     */
    function pollProcessingStatus(sessionId) {
        // Clear any existing polling interval
        if (statusPollingInterval) {
            clearInterval(statusPollingInterval);
        }
        
        // Set up polling interval (every 1 second)
        statusPollingInterval = setInterval(() => {
            if (!sessionId) {
                console.warn('No session ID available for status polling');
                clearInterval(statusPollingInterval);
                return;
            }
            
            fetch(`/api/processing_status/${sessionId}`)
                .then(response => response.json())
                .then(status => {
                    console.log('Processing status update:', status);
                    
                    // Update loading overlay with status information
                    const loadingOverlay = document.getElementById('loading-overlay');
                    const loadingStage = document.getElementById('loading-stage');
                    const loadingMessage = document.getElementById('loading-message');
                    const progressBar = document.getElementById('loading-progress-bar');
                    
                    // Only update if the loading overlay is visible and all elements exist
                    if (loadingOverlay && !loadingOverlay.classList.contains('hidden') && 
                        loadingStage && loadingMessage && progressBar) {
                        
                        // Format the stage name for display (convert snake_case to Title Case)
                        const formattedStage = status.stage
                            .split('_')
                            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                            .join(' ');
                            
                        loadingStage.textContent = formattedStage;
                        loadingMessage.textContent = status.message;
                        progressBar.style.width = `${status.progress}%`;
                        
                        // If we reach 100% progress or encounter an error, stop polling
                        if (status.progress === 100 || status.stage === 'error' || status.stage === 'completed') {
                            console.log('Stopping status polling - process complete or error occurred');
                            clearInterval(statusPollingInterval);
                            
                            // If there was an error, we'll let the error handler in the fetch response handle it
                            // Otherwise, we'll keep the loading overlay visible until the main process completes
                        }
                    } else if (loadingOverlay && loadingOverlay.classList.contains('hidden')) {
                        // If the loading overlay is hidden, stop polling
                        console.log('Loading overlay is hidden, stopping status polling');
                        clearInterval(statusPollingInterval);
                    }
                })
                .catch(error => {
                    console.error('Error polling for status:', error);
                    // Don't stop polling on network errors - it might be temporary
                });
        }, 1000); // Poll every second
    }
    
    function showLoading(message) {
        console.log('SHOW LOADING CALLED:', message);
        const loadingOverlay = document.getElementById('loading-overlay');
        const loadingMessage = document.getElementById('loading-message');
        const loadingStage = document.getElementById('loading-stage');
        const progressBar = document.getElementById('loading-progress-bar');
        
        if (loadingOverlay && loadingMessage) {
            // Reset the loading overlay elements
            loadingMessage.textContent = message || 'Loading...';
            loadingStage.textContent = 'Initializing';
            progressBar.style.width = '0%';
            
            // Show the overlay by removing the hidden class
            loadingOverlay.classList.remove('hidden');
        } else {
            console.error('Loading overlay elements not found:', {
                loadingOverlay: !!loadingOverlay,
                loadingMessage: !!loadingMessage
            });
        }
    }
    
    // Hide loading overlay
    function hideLoading() {
        console.log('HIDE LOADING CALLED');
        const loadingOverlay = document.getElementById('loading-overlay');
        
        // Stop any active status polling
        if (statusPollingInterval) {
            clearInterval(statusPollingInterval);
            statusPollingInterval = null;
        }
        
        if (loadingOverlay) {
            // Hide the overlay by adding the hidden class back
            loadingOverlay.classList.add('hidden');
        } else {
            console.error('Loading overlay element not found');
        }
    }
    
    // Show notification
    function showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Add to body
        document.body.appendChild(notification);
        
        // Remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
    
    // Reset application
    function resetApplication() {
        // Reset UI state
        
        // Reset audio
        if (audioPlayer) audioPlayer.src = '';
        if (outputAudioPlayer) outputAudioPlayer.src = '';
        if (comparisonInputAudio) comparisonInputAudio.src = '';
        if (comparisonOutputAudio) comparisonOutputAudio.src = '';
        
        // Reset text
        if (transcriptionText) transcriptionText.value = '';
        if (translationText) translationText.value = '';
        
        // Reset global variables
        if (typeof recordedChunks !== 'undefined') {
            recordedChunks = [];
        }
        
        if (typeof recordingSeconds !== 'undefined') {
            recordingSeconds = 0;
        }
        
        audioBlob = null;
        audioUrl = null;
        sessionId = generateSessionId();
        
        // Reset session validity flag
        hasValidSession = false;
        
        // Update download button visibility (will hide it)
        updateSessionDownloadButton();
        
        // Show input step
        showStep(stepInput);
    }
    
    // Functions to disable/enable editing
    function disableTranscriptionEditing() {
        console.log('Disabling transcription editing');
        
        // Disable textarea
        if (transcriptionText) transcriptionText.disabled = true;
        
        // Disable diarization editor inputs
        const inputs = document.querySelectorAll('#diarization-editor textarea, #diarization-editor select');
        inputs.forEach(input => input.disabled = true);
        
        // Disable save buttons
        if (saveTranscriptionBtn) saveTranscriptionBtn.disabled = true;
        const saveDiarizationBtn = document.getElementById('save-diarization-btn');
        if (saveDiarizationBtn) saveDiarizationBtn.disabled = true;
    }

    function enableTranscriptionEditing() {
        console.log('Enabling transcription editing');
        
        // Enable textarea
        if (transcriptionText) transcriptionText.disabled = false;
        
        // Enable diarization editor inputs
        const inputs = document.querySelectorAll('#diarization-editor textarea, #diarization-editor select');
        inputs.forEach(input => input.disabled = false);
        
        // Enable save buttons
        if (saveTranscriptionBtn) saveTranscriptionBtn.disabled = false;
        const saveDiarizationBtn = document.getElementById('save-diarization-btn');
        if (saveDiarizationBtn) saveDiarizationBtn.disabled = false;
    }
    
    // Sequential processing function
    function detectLanguageAndProcess() {
        console.log('Starting sequential processing');
        
        // Add a safety timeout to ensure loading is hidden even if something goes wrong
        const safetyTimeoutId = setTimeout(() => {
            console.log('Safety timeout triggered - forcing loading to hide');
            hideLoading();
            enableTranscriptionEditing();
            showNotification('Processing took longer than expected, but you can continue', 'warning');
        }, 60000); // 1 minute timeout
        
        // Skip language detection step and go straight to transcription
        // This will also handle language detection in the backend
        showLoading('Transcribing audio and detecting language...');
        
        fetchTranscription()
            .then(data => {
                console.log('Transcription and language detection completed:', data);
                
                // Update language display elements with data from transcription response
                detectedLang = data.language;
                
                const detectedLanguageEl = document.getElementById('detected-language');
                const sourceLanguageEl = document.getElementById('source-language');
                
                if (detectedLanguageEl) {
                    detectedLanguageEl.textContent = data.language_name || data.language;
                } else {
                    console.warn('detectedLanguage element not found in DOM');
                }
                
                if (sourceLanguageEl) {
                    sourceLanguageEl.textContent = data.language_name || data.language;
                } else {
                    console.warn('sourceLanguage element not found in DOM');
                }
                
                // Step 3: Wait for diarization to be ready
                showLoading('Processing speaker information...');
                return waitForDiarizationData();
            })
            .then(data => {
                console.log('Diarization processing completed:', data);
                
                // All data is ready
                clearTimeout(safetyTimeoutId);
                hideLoading();
                enableTranscriptionEditing();
            })
            .catch(error => {
                console.error('Error in sequential processing:', error);
                
                // Ensure timeout is cleared
                clearTimeout(safetyTimeoutId);
                
                // Always hide loading and enable editing on error
                hideLoading();
                enableTranscriptionEditing();
                showNotification('Error: ' + error.message, 'error');
            });
    }
    
    // Function to fetch transcription data
    function fetchTranscriptionData() {
        console.log('Fetching transcription data');
        
        return fetch('/api/transcribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching transcription:', data.error);
                throw new Error(data.error);
            }
            
            console.log('Transcription fetched successfully');
            
            // Store transcription in textarea
            transcriptionText.value = data.transcription;
            console.log('Transcription text set in textarea');
            
            return data;
        });
    }
    
    // Function to wait for diarization data to be ready
    function waitForDiarizationData() {
        console.log('Waiting for diarization data');
        
        return new Promise((resolve, reject) => {
            let attempts = 0;
            const maxAttempts = 10;
            
            function checkDiarization() {
                console.log(`Checking diarization data (attempt ${attempts + 1}/${maxAttempts})`);
                
                fetch(`/api/get_diarization?session_id=${sessionId}`)
                    .then(response => {
                        console.log(`Diarization API response status: ${response.status}`);
                        if (!response.ok && response.status !== 404) {
                            throw new Error(`HTTP error ${response.status}`);
                        }
                        return response.json().catch(e => {
                            // Handle case where response is not JSON
                            console.log('Response is not JSON, handling error:', e);
                            if (response.status === 404) {
                                return { error: 'Not found' };
                            }
                            throw e;
                        });
                    })
                    .then(data => {
                        console.log('RAW DIARIZATION DATA:', JSON.stringify(data, null, 2));
                        
                        // The API doesn't always include a success field, so check for segments directly
                        if (data.segments && data.segments.length > 0) {
                            // Diarization data is ready
                            console.log('Diarization data is ready, loading editor');
                            
                            // Add proper error handling to the nested Promise
                            return loadDiarizationEditor(sessionId)
                                .then(() => {
                                    console.log('Diarization editor loaded successfully');
                                    resolve(data);
                                })
                                .catch(error => {
                                    console.error('Error loading diarization editor, but continuing:', error);
                                    // Still resolve to continue the flow
                                    resolve(data);
                                });
                        } else if (attempts < maxAttempts) {
                            // Try again after delay
                            attempts++;
                            console.log(`Diarization data not ready, retrying in 2 seconds (attempt ${attempts}/${maxAttempts})`);
                            setTimeout(checkDiarization, 2000); // Check every 2 seconds
                        } else {
                            // Give up after max attempts
                            console.log('Max attempts reached, proceeding without diarization data');
                            resolve({ segments: [], error: 'Timeout waiting for diarization data' });
                        }
                    })
                    .catch(error => {
                        console.error('Error checking diarization:', error);
                        
                        // Try again after delay
                        if (attempts < maxAttempts) {
                            attempts++;
                            console.log(`Error checking diarization, retrying in 2 seconds (attempt ${attempts}/${maxAttempts})`);
                            setTimeout(checkDiarization, 2000);
                        } else {
                            console.log('Max attempts reached after errors, proceeding without diarization data');
                            resolve({ segments: [], error: error.message });
                        }
                    });
            }
            
            // Start checking
            checkDiarization();
        });
    }
    
    // Format time as MM:SS
    function formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    // Get color for speaker
    function getSpeakerColor(speakerNum) {
        const colors = ['#4285F4', '#EA4335', '#FBBC05', '#34A853', '#8F44AD', '#3498DB'];
        return colors[parseInt(speakerNum) % colors.length];
    }
    
    // Update the download button visibility based on session ID and validity
    function updateSessionDownloadButton() {
        const sessionId = getReliableSessionId();
        const sessionDownloadContainer = document.getElementById('session-download-container');
        
        if (sessionId && hasValidSession && sessionDownloadContainer) {
            // Show the download container only if we have a valid session with content
            sessionDownloadContainer.classList.remove('hidden');
        } else if (sessionDownloadContainer) {
            // Hide the download container
            sessionDownloadContainer.classList.add('hidden');
        }
    }
    
    // Handle the download session files action
    function downloadSessionFiles() {
        const sessionId = getReliableSessionId();
        if (!sessionId) {
            showNotification('No active session found', 'error');
            return;
        }
        
        // Determine if we're running locally or on Cloud Run
        const isLocalhost = window.location.hostname === 'localhost' || 
                          window.location.hostname === '127.0.0.1';
        
        let baseUrl;
        if (isLocalhost) {
            // Local development
            baseUrl = `${window.location.protocol}//${window.location.host}`;
        } else {
            // Cloud Run deployment
            baseUrl = 'https://indic-translator-869773419490.asia-south1.run.app';
        }
        
        // Construct the download URL
        const downloadUrl = `${baseUrl}/api/download_session?session_id=${sessionId}`;
        
        // Open the download URL in a new tab
        window.open(downloadUrl, '_blank');
    }
    
    // Initialize the application
    init();
});

// Add a <style> block for responsive layout (column on small screens)
const style = document.createElement('style');
style.innerHTML = `
@media (max-width: 700px) {
  .cascade-validation-metrics-flex { flex-direction: column !important; gap: 16px !important; }
  .cascade-validation-metrics-list { min-width: 0 !important; width: 100% !important; }
  .cascade-validation-metrics-circle { margin: 0 auto 8px auto !important; }
}
`;
document.head.appendChild(style);

// Render the composite score circle left, metrics breakdown right, using a flex row that stacks on mobile
function validateOutput() {
  showLoading('Validating output...');
  
  fetch('/api/validate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      session_id: sessionId
    })
  })
  .then(response => response.json())
  .then(data => {
    hideLoading();
    
    if (data.success) {
      // Removed similarity score update since the element no longer exists

      // --- Begin progress bar layout for validation scores ---
      // Add responsive style block for progress bars if not present
      if (!document.getElementById('cascade-validation-metrics-progress-style')) {
        const style = document.createElement('style');
        style.id = 'cascade-validation-metrics-progress-style';
        style.innerHTML = `
        .cascade-metric-bar-container { width: 100%; background: #e5e7eb; border-radius: 8px; height: 20px; margin: 8px 0 16px 0; }
        .cascade-metric-bar { height: 100%; border-radius: 8px; transition: width 0.5s; }
        .cascade-metric-label { display: flex; justify-content: space-between; font-size: 1em; font-weight: 500; margin-bottom: 2px; }
        @media (max-width: 700px) {
          .cascade-validation-metrics-progress-outer { padding: 0 0.5em !important; }
        }
        `;
        document.head.appendChild(style);
      }
      // Build progress bars for each metric
      function metricBar(label, value, color, scoreText, weight) {
        return `
          <div>
            <div class="cascade-metric-label">${label} <span>${scoreText}</span></div>
            <div class="cascade-metric-bar-container">
              <div class="cascade-metric-bar" style="width:${value}%;background:${color};"></div>
            </div>
            <div style="color:#888;font-size:0.95em;margin-bottom:8px;">Weight: ${weight}</div>
          </div>
        `;
      }
      const metricColors = ['#10b981', '#6366f1', '#f59e0b', '#ef4444'];
      const barsHtml = [
        metricBar('Semantic Similarity', Math.round((data.validation_result.metrics.semantic || 0) * 100), metricColors[0], `${Math.round((data.validation_result.metrics.semantic || 0) * 100)}/100`, 0.4),
        metricBar('Transcription Accuracy', Math.round((1 - (data.validation_result.metrics.transcription_edit || 0)) * 100), metricColors[1], `${Math.round((1 - (data.validation_result.metrics.transcription_edit || 0)) * 100)}/100`, 0.2),
        metricBar('Diarization Accuracy', Math.round((data.validation_result.metrics.diarization || 0) * 100), metricColors[2], `${Math.round((data.validation_result.metrics.diarization || 0) * 100)}/100`, 0.2),
        metricBar('Translation Accuracy', Math.round((1 - (data.validation_result.metrics.translation_edit || 0)) * 100), metricColors[3], `${Math.round((1 - (data.validation_result.metrics.translation_edit || 0)) * 100)}/100`, 0.2),
      ].join('');
      // Definitions block (technical)
      const definitionsHtml = `
        <div style="margin-top:18px;font-size:0.97em;line-height:1.6;"><b>Metric Definitions:</b><br>
        <ul style="margin:8px 0 0 18px;padding:0;">
          <li><b>Semantic Similarity:</b> Cosine similarity between TF-IDF vectors of the original and output transcript. <br>Formula: <i>similarity = cos(V<sub>src</sub>, V<sub>out</sub>)</i>, range [0,1].</li>
          <li><b>Transcription Accuracy:</b> 1 minus Word Error Rate (WER) between reference and ASR output.<br>Formula: <i>WER = (S + D + I) / N</i>, where S=substitutions, D=deletions, I=insertions, N=number of words in reference.</li>
          <li><b>Diarization Accuracy:</b> Ratio of correctly predicted speaker change points to total reference change points.<br>Formula: <i>accuracy = (# correct changes) / (# reference changes)</i>.</li>
          <li><b>Translation Accuracy:</b> 1 minus WER between reference translation and system output. Formula as above.</li>
        </ul>
        Composite Score: Weighted sum of all metrics.
        </div>
      `;
      metricsDetails.innerHTML = `
        <div class="cascade-validation-metrics-progress-outer" style="width:100%;max-width:600px;margin:0 auto;">
          <div style="text-align:center;font-size:2.3em;font-weight:700;margin-bottom:8px;">${compositeScore}/100</div>
          <div style="text-align:center;color:#666;font-weight:500;margin-bottom:24px;">Composite Score</div>
          ${barsHtml}
          ${definitionsHtml}
        </div>
      `;
      // --- End progress bar layout for validation scores ---
      
      // Update audio players
      // --- Audio player source path fix (robust) ---
      // Determine file extension based on target language (default: wav, Hindi: mp3)
      const targetLang = targetLanguageSelect.value ? targetLanguageSelect.value.toLowerCase() : 'unknown';
      const fileExtension = targetLang === 'hindi' ? 'mp3' : 'wav';
      // Input audio path: /outputs/session_id/audio/session_id.<filetype>
      // Fallback: If not found, try .wav as default
      let inputAudioPath = `/outputs/${sessionId}/audio/${sessionId}.${fileExtension}`;
      fetch(inputAudioPath, { method: 'HEAD' })
        .then(resp => {
          if (!resp.ok && fileExtension !== 'wav') {
            // fallback to wav if not found and not already wav
            inputAudioPath = `/outputs/${sessionId}/audio/${sessionId}.wav`;
          }
          comparisonInputAudio.src = inputAudioPath;
        })
        .catch(() => {
          // fallback to wav if fetch fails
          comparisonInputAudio.src = `/outputs/${sessionId}/audio/${sessionId}.wav`;
        });
      // Output audio path: /outputs/session_id/tts/final_output_<target_language>_session_id.<filetype>
      comparisonOutputAudio.src = `/outputs/${sessionId}/tts/final_output_${targetLang}_${sessionId}.${fileExtension}`;
      // --- End audio player source path fix (robust) ---
      
      // Removed color update for similarity score circle since the element no longer exists
    } else {
      showNotification('Error validating output: ' + data.error, 'error');
    }
  })
  .catch(error => {
    hideLoading();
    showNotification('Error validating output: ' + error.message, 'error');
  });
}
