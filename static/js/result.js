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
            
            audioSource.src = `/get_audio/${i}`;
            
            audioBtn.onclick = () => {
                player.style.display = player.style.display === "none" ? "block" : "none";
            };

            editorContainer.appendChild(clone);
        }

        const pdfFrame = document.getElementById("pdf-frame");
        pdfFrame.src = "/generate_pdf_preview"; 
    }
});

window.saveAllChanges = function() {
    const saveBtn = document.getElementById("save-btn");
    const btnText = document.getElementById("save-btn-text");
    const spinner = document.getElementById("save-btn-spinner");

    saveBtn.disabled = true;
    btnText.style.display = "none";
    spinner.style.display = "block";

    const updates = [];
    document.querySelectorAll(".editor-group").forEach(group => {
        updates.push({
            part: group.dataset.part,
            needsEdit: group.querySelector(".edit-check").checked,
            spec: group.querySelector(".spec-input").value
        });
    });

    console.log("Saving updates:", updates);

    setTimeout(() => {
        alert("Changes saved! The PDF and Audio will be regenerated.");
        saveBtn.disabled = false;
        btnText.style.display = "inline";
        spinner.style.display = "none";
    }, 2000);
};

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

    // 2. Show loading state
    saveBtn.disabled = true;
    spinner.style.display = 'inline-block';
    btnText.innerText = 'Saving...';

    try {
        const response = await fetch('/api/save-to-firebase', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ files: selectedFiles })
        });

        const result = await response.json();

        if (result.success) {
            alert("Successfully saved to Firebase!");
            window.location.href = '/history';
        } else {
            alert("Error: " + (result.error || "Failed to save files."));
        }
    } catch (error) {
        console.error("Save error:", error);
        alert("A server error occurred.");
    } finally {
        // 3. Reset button state
        saveBtn.disabled = false;
        spinner.style.display = 'none';
        btnText.innerText = 'Save';
    }
}