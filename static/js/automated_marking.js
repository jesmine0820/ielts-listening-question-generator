document.addEventListener('DOMContentLoaded', async () => {
    const select = document.querySelector('.question-set-select');
    const markBtn = document.getElementById('mark-btn');
    const pdfContainer = document.querySelector('.pdf-result');
    const pdfViewer = document.getElementById('pdf-viewer');
    const downloadLink = document.getElementById('download-link');

    // Load available sets
    try {
        const res = await fetch('/api/get-history');
        const data = await res.json();
        if (data.success) {
            data.history.forEach(item => {
                const option = document.createElement('option');
                option.value = item.folder_name;
                option.textContent = item.folder_name.toUpperCase();
                select.appendChild(option);
            });
        }
    } catch (err) {
        console.error('Failed to load sets', err);
    }

    select.addEventListener('change', () => {
        markBtn.disabled = select.value === "";
    });

    markBtn.addEventListener('click', async () => {
        const files = document.getElementById('answer-files').files;
        if (!files.length) {
            alert('Please upload at least one file.');
            return;
        }

        const formData = new FormData();
        formData.append('set_name', select.value);
        for (let f of files) formData.append('files', f);

        markBtn.disabled = true;
        markBtn.innerText = 'Marking...';

        try {
            const res = await fetch('/api/automated-marking', {
                method: 'POST',
                body: formData
            });
            const result = await res.json();

            if (result.success) {
                // Show PDF in iframe
                pdfViewer.src = result.pdf_url;
                downloadLink.href = result.pdf_url;
                pdfContainer.style.display = 'block';
            } else {
                alert(result.error || 'Marking failed');
            }
        } catch (err) {
            console.error(err);
            alert('Error during marking');
        }

        markBtn.innerText = 'Mark';
        markBtn.disabled = false;
    });
});
