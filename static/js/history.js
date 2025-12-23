document.addEventListener('DOMContentLoaded', async () => {
    const historyList = document.getElementById('history-list');
    const template = document.getElementById('history-card-template');

    try {
        const response = await fetch('/api/get-history');
        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error || 'Failed to load history');
        }

        if (result.history.length === 0) {
            historyList.innerHTML = `
                <div class="empty-history">
                    <img src="../static/images/empty_box.png" alt="Empty" class="empty-icon">
                    <h3>No Practice History Found</h3>
                    <p>You haven’t saved any question sets yet.</p>
                    <a href="/question-generator" class="btn-primary">
                        Generate Your First Set
                    </a>
                </div>
            `;
            return;
        }

        historyList.innerHTML = '';

        result.history.forEach(item => {
            const clone = template.content.cloneNode(true);

            clone.querySelector('.set-name').innerText = item.folder_name.toUpperCase();

            const [date, time] = item.timestamp.split(' ');
            clone.querySelector('.set-date').innerText = `Date: ${date}`;
            clone.querySelector('.set-time').innerText = `Time: ${time || ''}`;

            const dropdown = clone.querySelector('.file-dropdown');
            const downloadBtn = clone.querySelector('.btn-download');

            const files = item.files || {};
            Object.entries(files).forEach(([key, url]) => {
                const option = document.createElement('option');
                option.value = url;
                option.innerText = key.replace(/_/g, '.');
                dropdown.appendChild(option);
            });

            downloadBtn.addEventListener('click', () => {
                const url = dropdown.value;
                if (!url) {
                    alert('Please select a file to download.');
                    return;
                }

                const a = document.createElement('a');
                a.href = url;
                a.target = '_blank';
                a.rel = 'noopener';
                document.body.appendChild(a);
                a.click();
                a.remove();
            });

            historyList.appendChild(clone);
        });

    } catch (error) {
        console.error('History load error:', error);
        historyList.innerHTML = `
            <p class="error">
                Failed to load history. Please try again later.
            </p>
        `;
    }
});

async function checkAudioStatus(taskId, setName) {
    const interval = setInterval(async () => {
        const res = await fetch(`/api/audio-task-status/${taskId}`);
        const data = await res.json();

        if (data.status === "completed") {
            clearInterval(interval);
            alert(`Audio for set ${setName} is ready!`);
            // Optionally update a download button
            const audioLink = document.getElementById('download-audio');
            audioLink.href = `/static/output/${setName}/full_set_audio.wav`;
            audioLink.style.display = 'inline-block';
        } else if (data.status.startsWith("error")) {
            clearInterval(interval);
            alert(`Audio generation failed: ${data.status}`);
        }
        // else keep polling if "processing"
    }, 3000); // poll every 3 seconds
}

async function handleAudioGeneration(setName) {
    const res = await fetch(`/api/check-or-generate-audio/${setName}`);
    const data = await res.json();

    if (data.status === "ready") {
        alert("Audio already exists!");
    } else if (data.status === "processing") {
        checkAudioStatus(data.task_id, setName);
        alert("Audio generation started in background. You will be notified when ready.");
    } else {
        alert(`Error: ${data.error}`);
    }
}
