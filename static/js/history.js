document.addEventListener('DOMContentLoaded', async () => {
    const historyList = document.getElementById('history-list');
    const template = document.getElementById('history-card-template');
    const previewModal = document.getElementById('preview-modal');
    const previewIframe = document.getElementById('preview-iframe');
    const previewClose = document.getElementById('preview-close');

    previewClose.addEventListener('click', () => {
        previewModal.style.display = 'none';
        previewIframe.src = '';
    });

    try {
        const response = await fetch('/api/get-history');
        const result = await response.json();

        if (result.success && result.history.length > 0) {
            historyList.innerHTML = ''; // Clear loader

            result.history.forEach(item => {
                const clone = template.content.cloneNode(true);

                clone.querySelector('.set-name').innerText = item.folder_name.toUpperCase();
                clone.querySelector('.set-date').innerText = `Date: ${item.timestamp.split(' ')[0]}`;
                clone.querySelector('.set-time').innerText = `Time: ${item.timestamp.split(' ')[1] || ''}`;

                const dropdown = clone.querySelector('.file-dropdown');
                const previewBtn = clone.querySelector('.btn-preview');
                const downloadBtn = clone.querySelector('.btn-download');

                // Build options from files object
                const files = item.files || {};
                Object.entries(files).forEach(([key, url]) => {
                    const option = document.createElement('option');
                    option.value = url;
                    // display-friendly name
                    const display = key.replace(/_/g, '.');
                    option.innerText = display;
                    dropdown.appendChild(option);
                });

                // Preview handler
                previewBtn.addEventListener('click', () => {
                    const url = dropdown.value;
                    if (!url) { alert('Please select a file to preview.'); return; }
                    previewIframe.src = url;
                    previewModal.style.display = 'flex';
                });

                // Download handler
                downloadBtn.addEventListener('click', () => {
                    const url = dropdown.value;
                    if (!url) { alert('Please select a file to download.'); return; }
                    // Use anchor to trigger download/open in new tab
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
        } else {
            historyList.innerHTML = `
                <div class="empty-history">
                    <img src="../static/images/empty_box.png" alt="Empty" class="empty-icon">
                    <h3>No Practice History Found</h3>
                    <p>It looks like you haven't saved any question sets yet.</p>
                    <a href="/question-generator" class="btn-primary">Generate Your First Set</a>
                </div>
            `;
        }
    } catch (err) {
        historyList.innerHTML = '<p class="error">Failed to load history. Please try again later.</p>';
        console.error('Failed to load history', err);
    }
});