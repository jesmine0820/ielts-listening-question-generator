document.addEventListener("DOMContentLoaded", (e) => {
    const progressBar = document.getElementById("progress-bar");
    const progressPercent = document.getElementById("progress-percent");
    const statusTitle = document.getElementById("status-title");
    const statusTask = document.getElementById("status-task");
    const generationStage = document.getElementById("generation-stage");
    const previewContainer = document.getElementById("preview-editor-container");
    const editorContainer = document.getElementById("editor-fields-container");
    const template = document.getElementById("part-template");

    previewContainer.style.display = "none";

    const questionDataStr = localStorage.getItem("questionData");
    const generateWithAudio = localStorage.getItem("generateWithAudio") === "true";
    
    if (!questionDataStr) {
        statusTask.textContent = "No question data found. Please go back to the question generator.";
        return;
    }

    const questionData = JSON.parse(questionDataStr);

    startGeneration(questionData, generateWithAudio);

    function startGeneration(questionData, generateWithAudio) {
        if (generateWithAudio) {
            statusTitle.textContent = "Generating Questions and Audio...";
        } else {
            statusTitle.textContent = "Generating Questions...";
        }

        fetch("/api/generate-questions", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                ...questionData,
                generateWithAudio: generateWithAudio
            })
        })
        .then(response => {
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            function readStream() {
                reader.read().then(({ done, value }) => {
                    if (done) {
                        if (generateWithAudio) {
                            setTimeout(showEditor, 800);
                        } else {
                            showEditor();
                            startBackgroundAudioGeneration();
                        }
                        return;
                    }

                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\n');

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                updateProgress(data);
                            } catch (e) {
                                console.error("Error parsing progress data:", e);
                            }
                        }
                    }

                    readStream();
                });
            }

            readStream();
        })
        .catch(error => {
            console.error("Generation error:", error);
            statusTask.textContent = `Error: ${error.message}`;
        });
    }

    function updateProgress(data) {
        if (data.progress !== undefined) {
            progressBar.style.width = `${data.progress}%`;
            progressPercent.textContent = `${data.progress}%`;
        }
        
        if (data.status) {
            statusTitle.textContent = data.status;
        }
        
        if (data.task) {
            statusTask.textContent = data.task;
        }

        if (data.success && data.progress === 100) {
            // Generation complete
        }
    }

    function startBackgroundAudioGeneration() {
        fetch("/api/generate-audio-background", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.task_id) {
                pollAudioStatus(data.task_id);
            }
        })
        .catch(error => {
            console.error("Error starting audio generation:", error);
        });
    }

    function pollAudioStatus(taskId) {
        const checkInterval = setInterval(() => {
            fetch(`/api/check-audio-status/${taskId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === "completed") {
                        clearInterval(checkInterval);
                        showAudioNotification("Audio generation completed successfully!");
                    } else if (data.status === "error") {
                        clearInterval(checkInterval);
                        showAudioNotification(`Audio generation failed: ${data.error}`, true);
                    }
                })
                .catch(error => {
                    console.error("Error checking audio status:", error);
                });
        }, 2000);
    }

    function showAudioNotification(message, isError = false) {
        const notification = document.createElement("div");
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: ${isError ? "#ff4444" : "#4CAF50"};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 10000;
            font-weight: bold;
            animation: slideIn 0.3s ease-out;
        `;
        notification.textContent = message;

        const style = document.createElement("style");
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = "slideIn 0.3s ease-out reverse";
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
    }

    function showEditor() {
        generationStage.style.display = "none";
        previewContainer.style.display = "block";
        
        for (let i = 1; i <= 4; i++) {
            const clone = template.content.cloneNode(true);
            const group = clone.querySelector(".editor-group");
            
            group.querySelector(".q-label").textContent = `Part ${i}`;
            group.dataset.part = i;
            
            const audioBtn = clone.querySelector(".audio-icon-btn");
            const player = clone.querySelector(".mini-player");
            const audioSource = clone.querySelector("source");

            if (generateWithAudio) {
                audioSource.src = `/get_audio/${i}`;
                audioBtn.onclick = () => {
                    player.style.display = player.style.display === "none" ? "block" : "none";
                };
            } else {
                // Hide audio controls when audio was not generated
                if (audioBtn) audioBtn.style.display = 'none';
                if (player) player.style.display = 'none';
            }

            // Listen for edit checkbox changes to toggle main button label
            const editCheckbox = clone.querySelector('.edit-check');
            if (editCheckbox) {
                editCheckbox.addEventListener('change', () => {
                    const anyChecked = document.querySelectorAll('.edit-check:checked').length > 0;
                    const saveBtnText = document.getElementById('save-btn-text');
                    saveBtnText.innerText = anyChecked ? 'Regenerate' : 'Save locally';
                });
            }

            editorContainer.appendChild(clone);
        }

        const pdfFrame = document.getElementById("pdf-frame");
        pdfFrame.src = "/generate_pdf_preview"; 
    }
});

async function saveAllChanges() {
    const saveBtn = document.getElementById('save-btn');
    const spinner = document.getElementById('save-btn-spinner');
    const btnText = document.getElementById('save-btn-text');

    // 1. Get all checked files
    const selectedFiles = Array.from(document.querySelectorAll('.export-file:checked'))
                               .map(cb => cb.value);

    if (selectedFiles.length === 0) {
        alert("Please select at least one file to save.");
        return;
    }

    // Check if any edit checkboxes are selected; if none, do direct save+download flow
    const editsSelected = document.querySelectorAll('.edit-check:checked').length > 0;

    // 2. Show loading state
    saveBtn.disabled = true;
    spinner.style.display = 'inline-block';
    btnText.innerText = 'Saving...';

    try {
        if (!editsSelected) {
            // 1a. Save selected files locally first
            const saveResp = await fetch('/api/save-to-firebase', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ files: selectedFiles })
            });

            const saveResult = await saveResp.json().catch(() => ({}));
            if (!saveResp.ok || !saveResult.success) {
                alert('Error saving files locally: ' + (saveResult.error || 'Unknown error'));
                return;
            }
        } else {
            // Regenerate selected parts sequentially
            btnText.innerText = 'Regenerating...';
            const edits = Array.from(document.querySelectorAll('.editor-group')).map(g => ({
                part: g.dataset.part,
                needsEdit: g.querySelector('.edit-check').checked,
                spec: g.querySelector('.spec-input').value
            })).filter(x => x.needsEdit);

            for (const e of edits) {
                try {
                    const resp = await fetch('/api/regenerate-part', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ part: parseInt(e.part), spec: e.spec })
                    });
                    const json = await resp.json().catch(() => ({}));
                    if (!resp.ok || !json.success) {
                        alert('Regeneration failed for part ' + e.part + ': ' + (json.error || 'Unknown'));
                    }
                } catch (err) {
                    console.error('Regenerate error:', err);
                }
            }

            // Refresh preview PDF and audio sources
            const pdfFrame = document.getElementById('pdf-frame');
            pdfFrame.src = '/generate_pdf_preview?ts=' + Date.now();

            // Refresh audio sources for parts that exist
            for (let i = 1; i <= 4; i++) {
                const audioEl = document.querySelector(`.editor-group[data-part='${i}'] .mini-player source`);
                if (audioEl) {
                    audioEl.src = `/get_audio/${i}?ts=${Date.now()}`;
                    const player = audioEl.closest('.mini-player');
                    if (player) player.style.display = 'none';
                }
            }
        }

        // Request the server to build a zip and return it
        const response = await fetch('/api/download-files', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ files: selectedFiles })
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            alert('Error: ' + (err.error || 'Failed to prepare download.'));
            return;
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        // use suggested filename from server
        const filename = response.headers.get('Content-Disposition')?.split('filename=')?.pop() || `ielts_materials.zip`;
        a.download = filename.replace(/"/g, '');
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

        // If no edits selected, redirect back to question generator after download
        if (!editsSelected) {
            setTimeout(() => { window.location.href = '/question-generator'; }, 500);
        }

    } catch (error) {
        console.error("Download error:", error);
        alert("A server error occurred while preparing the download.");
        } finally {
            // 3. Reset button state
            saveBtn.disabled = false;
            spinner.style.display = 'none';
            btnText.innerText = 'Save locally';
        }
}