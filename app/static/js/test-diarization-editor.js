/**
 * Test script for diarization editor functionality
 */

// Standalone version of the diarization editor functions
// This allows us to test the editor without depending on the full app.js

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

// Render diarization editor
function renderDiarizationEditor(data) {
    console.log('Rendering diarization editor with data:', data);
    
    // Find the correct container
    const diarizationEditorContent = document.querySelector('#diarization-editor .card-body');
    if (!diarizationEditorContent) {
        console.error('Diarization editor container not found');
        return;
    }
    
    // Clear previous content
    diarizationEditorContent.innerHTML = '';
    
    // Create timeline visualization
    const timeline = document.createElement('div');
    timeline.className = 'diarization-timeline';
    
    // Calculate total duration for timeline scaling
    const totalDuration = Math.max(...data.segments.map(seg => seg.end_time));
    console.log('Total duration:', totalDuration);
    
    // Create segments in timeline
    data.segments.forEach(segment => {
        const segmentEl = document.createElement('div');
        segmentEl.className = 'timeline-segment';
        segmentEl.style.left = `${(segment.start_time / totalDuration) * 100}%`;
        segmentEl.style.width = `${((segment.end_time - segment.start_time) / totalDuration) * 100}%`;
        segmentEl.dataset.speaker = segment.speaker;
        segmentEl.title = `${segment.speaker}: ${segment.text}`;
        
        // Color based on speaker
        const speakerNum = segment.speaker.split('_')[1];
        segmentEl.style.backgroundColor = getSpeakerColor(speakerNum);
        
        timeline.appendChild(segmentEl);
        console.log('Added timeline segment:', segment.speaker, segment.start_time, segment.end_time);
    });
    
    diarizationEditorContent.appendChild(timeline);
    
    // Create editable segments
    const segmentsContainer = document.createElement('div');
    segmentsContainer.className = 'segments-container';
    
    // Get unique speakers
    const speakers = [...new Set(data.segments.map(seg => seg.speaker))];
    console.log('Unique speakers:', speakers);
    
    data.segments.forEach((segment, index) => {
        const segmentEl = document.createElement('div');
        segmentEl.className = 'segment-row';
        segmentEl.dataset.segmentId = segment.segment_id;
        
        // Create segment header
        const header = document.createElement('div');
        header.className = 'segment-header';
        
        // Add segment metadata
        const meta = document.createElement('span');
        meta.className = 'segment-meta';
        meta.textContent = `#${index+1} | ${formatTime(segment.start_time)}-${formatTime(segment.end_time)}`;
        header.appendChild(meta);
        
        // Add speaker selector
        const speakerSelect = document.createElement('select');
        speakerSelect.className = 'speaker-select';
        speakers.forEach(speaker => {
            const option = document.createElement('option');
            option.value = speaker;
            option.textContent = speaker;
            option.selected = speaker === segment.speaker;
            speakerSelect.appendChild(option);
        });
        header.appendChild(speakerSelect);
        
        segmentEl.appendChild(header);
        
        // Add editable text
        const textArea = document.createElement('textarea');
        textArea.className = 'segment-text';
        textArea.value = segment.text;
        segmentEl.appendChild(textArea);
        
        segmentsContainer.appendChild(segmentEl);
        console.log('Added segment row:', segment.segment_id);
    });
    
    diarizationEditorContent.appendChild(segmentsContainer);
    console.log('Diarization editor rendering complete');
}

// Initialize test when the page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Test script loaded');
    
    // Load sample data
    const sampleDataElement = document.getElementById('sample-diarization-data');
    if (sampleDataElement) {
        try {
            const sampleData = JSON.parse(sampleDataElement.textContent);
            console.log('Sample data loaded:', sampleData);
            
            // Set transcription text
            const transcriptionText = document.getElementById('transcription-text');
            if (transcriptionText) {
                transcriptionText.value = sampleData.transcript;
            }
            
            // Render diarization editor
            renderDiarizationEditor(sampleData);
        } catch (e) {
            console.error('Error loading sample data:', e);
        }
    } else {
        console.error('Sample data element not found');
    }
    
    // Test save button
    const saveButton = document.getElementById('test-save-btn');
    if (saveButton) {
        saveButton.addEventListener('click', function() {
            console.log('Testing save functionality');
            
            // Collect edits
            const updates = {};
            document.querySelectorAll('.segment-row').forEach(row => {
                const segId = row.dataset.segmentId;
                updates[segId] = {
                    speaker: row.querySelector('.speaker-select').value,
                    text: row.querySelector('.segment-text').value
                };
            });
            
            console.log('Collected updates:', updates);
            
            // Display in debug panel
            const debugOutput = document.getElementById('debug-output');
            if (debugOutput) {
                const timestamp = new Date().toLocaleTimeString();
                debugOutput.textContent = `[${timestamp}] Save button clicked\n${JSON.stringify(updates, null, 2)}\n\n` + debugOutput.textContent;
            }
        });
    }
});
