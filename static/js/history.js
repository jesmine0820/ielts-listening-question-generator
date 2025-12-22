document.addEventListener('DOMContentLoaded', async () => {
    const historyList = document.getElementById('history-list');
    const template = document.getElementById('history-card-template');

    try {
        const response = await fetch('/api/get-history');
        const result = await response.json();

        if (result.success && result.history.length > 0) {
            historyList.innerHTML = ''; // Clear loader
            
            result.history.forEach(item => {
                const clone = template.content.cloneNode(true);
                
                // Parse set name and date
                clone.querySelector('.set-name').innerText = item.folder_name.toUpperCase();
                const [date, time] = item.timestamp.split(' ');
                clone.querySelector('.set-date').innerText = `Date: ${date}`;
                clone.querySelector('.set-time').innerText = `Time: ${time}`;

                // Populate Dropdown
                const dropdown = clone.querySelector('.file-dropdown');
                for (const [fileName, url] of Object.entries(item.files)) {
                    const option = document.createElement('option');
                    option.value = url;
                    // Replace underscore back to dot for display (Full_Set_pdf -> Full_Set.pdf)
                    option.innerText = fileName.replace(/_([^_]*)$/, '.$1'); 
                    dropdown.appendChild(option);
                }

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
    }
});

function downloadSelectedFile(button) {
    const select = button.previousElementSibling;
    const url = select.value;
    if (url) {
        window.open(url, '_blank');
    } else {
        alert("Please select a file first.");
    }
}