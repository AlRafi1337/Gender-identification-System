document.addEventListener('DOMContentLoaded', function () {
    // Basic Fade-in Animation for Page Load
    const content = document.querySelector('.content');
    if (content) {
        content.classList.add('fade-in');
    }
});
// Placeholder for any required JS animations or form validations
document.addEventListener("DOMContentLoaded", function () {
    console.log("JavaScript is ready!");
});
const sidebarToggle = document.querySelector('.sidebar-toggle');
const sidebar = document.querySelector('.sidebar');

sidebarToggle?.addEventListener('click', () => {
    sidebar.classList.toggle('active');
});
document.getElementById("uploadForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const fileInput = document.getElementById("dataFile");
    const resultDiv = document.getElementById("result");

    if (fileInput.files.length === 0) {
        resultDiv.innerHTML = "<p class='error'>Please select a file to upload.</p>";
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                // Render result visually
                renderResult(data.result);
            } else {
                resultDiv.innerHTML = `<p class='error'>${data.error}</p>`;
            }
        } else {
            const error = await response.json();
            resultDiv.innerHTML = `<p class='error'>${error.error || "An error occurred."}</p>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<p class='error'>Error: ${error.message}</p>`;
    }
});

function renderResult(result) {
    const resultDiv = document.getElementById("result");
    resultDiv.innerHTML = "";

    if (result.status === "positive") {
        resultDiv.innerHTML = `
            <h2 class="positive-result">Positive Detection</h2>
            <img src="/static/images/positive_graph.png" alt="Positive Graph">
        `;
    } else if (result.status === "negative") {
        resultDiv.innerHTML = `
            <h2 class="negative-result">Negative Detection</h2>
            <img src="/static/images/negative_graph.png" alt="Negative Graph">
        `;
    } else {
        resultDiv.innerHTML = `<p>Unexpected result: ${JSON.stringify(result)}</p>`;
    }
}
function showProgress() {
    const indicator = document.getElementById('progress-indicator');
    if (indicator) {
        indicator.style.display = 'block';
    }
}
document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.querySelector(".upload-form");
    const progressBar = document.querySelector(".progress-bar");
    const progressContainer = document.querySelector(".progress-container");

    if (uploadForm) {
        uploadForm.addEventListener("submit", function () {
            progressContainer.style.display = "block";
            let width = 0;
            let interval = setInterval(() => {
                if (width >= 100) {
                    clearInterval(interval);
                } else {
                    width += 10;
                    progressBar.style.width = width + "%";
                }
            }, 400);
        });
    }
});
