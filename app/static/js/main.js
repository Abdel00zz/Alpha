document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const analyzeButtons = document.querySelectorAll('.analyze-btn');
    const resultModal = new bootstrap.Modal(document.getElementById('resultModal'));
    const resultContent = document.getElementById('result-content');
    const loading = document.getElementById('loading');
    const overleafForm = document.getElementById('overleaf-form');
    const overleafContent = document.getElementById('overleaf-content');
    
    let currentFile = null;

    // Get CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    // Add CSRF token to all fetch requests
    function fetchWithCSRF(url, options = {}) {
        if (!options.headers) {
            options.headers = {};
        }
        options.headers['X-CSRFToken'] = csrfToken;
        return fetch(url, options);
    }

    // Drag and drop handlers
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const file = dt.files[0];
        handleFile(file);
    }

    function handleFileSelect(e) {
        const file = e.target.files[0];
        handleFile(file);
    }

    function handleFile(file) {
        if (file && file.type === 'application/pdf') {
            const formData = new FormData();
            formData.append('file', file);

            fetchWithCSRF('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.filename) {
                    currentFile = data.filename;
                    analyzeButtons.forEach(btn => btn.disabled = false);
                    dropZone.innerHTML = `<i class="fas fa-check-circle fa-3x text-success mb-3"></i>
                                        <h4>${file.name}</h4>
                                        <p class="text-muted">Fichier prêt pour l'analyse</p>`;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Erreur lors du téléchargement du fichier');
            });
        } else {
            alert('Veuillez sélectionner un fichier PDF valide');
        }
    }

    // Analyze button handlers
    analyzeButtons.forEach(button => {
        button.addEventListener('click', () => {
            const analysisType = button.dataset.type;
            
            resultContent.textContent = '';
            loading.classList.remove('d-none');
            resultModal.show();

            const formData = new FormData();
            formData.append('filename', currentFile);
            formData.append('type', analysisType);

            fetchWithCSRF('/analyze', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                loading.classList.add('d-none');
                resultContent.textContent = data.latex;
                overleafContent.value = data.overleaf_url;
                overleafForm.style.display = 'block';
            })
            .catch(error => {
                loading.classList.add('d-none');
                resultContent.textContent = 'Erreur lors de l\'analyse : ' + error;
                overleafForm.style.display = 'none';
            });
        });
    });
});
