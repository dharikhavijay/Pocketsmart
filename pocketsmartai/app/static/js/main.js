// PocketSmart AI Main Client Script

document.addEventListener("DOMContentLoaded", () => {
    // 1. Loading Overlay for Planner Submissions
    const plannerForms = document.querySelectorAll("form.planner-form");
    const loadingOverlay = document.getElementById("loadingOverlay");
    const loadingMessage = document.getElementById("loadingMessage");

    plannerForms.forEach(form => {
        form.addEventListener("submit", (e) => {
            if (form.checkValidity()) {
                if (loadingOverlay) {
                    const category = form.getAttribute("data-category") || "plan";
                    if (loadingMessage) {
                        if (category === "home") {
                            loadingMessage.textContent = "Analyzing space, styling rooms, and calculating optimal budget allocation...";
                        } else if (category === "party") {
                            loadingMessage.textContent = "Calculating per-guest costs, sourcing catering and entertainment...";
                        } else if (category === "jewelry") {
                            loadingMessage.textContent = "Inspecting outfit colors, neckline harmony, and matching accessories...";
                        } else {
                            loadingMessage.textContent = "Consulting Gemini AI foundation model...";
                        }
                    }
                    loadingOverlay.style.display = "flex";
                }
            }
        });
    });

    // 2. Drag & Drop and Preview for Outfit Image Upload
    const dropzone = document.getElementById("uploadDropzone");
    const fileInput = document.getElementById("outfit_image");
    const previewContainer = document.getElementById("imagePreviewContainer");
    const previewImg = document.getElementById("imagePreview");
    const removeBtn = document.getElementById("removeImageBtn");

    if (dropzone && fileInput) {
        // Click to open file dialog
        dropzone.addEventListener("click", () => fileInput.click());

        // Drag events
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add("dragover");
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove("dragover");
            }, false);
        });

        dropzone.addEventListener("drop", (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files && files[0]) {
                fileInput.files = files;
                showImagePreview(files[0]);
            }
        });

        fileInput.addEventListener("change", (e) => {
            if (e.target.files && e.target.files[0]) {
                showImagePreview(e.target.files[0]);
            }
        });

        function showImagePreview(file) {
            if (!file.type.startsWith("image/")) {
                alert("Please select a valid image file (JPG, PNG, WEBP).");
                return;
            }
            const reader = new FileReader();
            reader.onload = (e) => {
                if (previewImg && previewContainer) {
                    previewImg.src = e.target.result;
                    previewContainer.style.display = "block";
                    dropzone.style.display = "none";
                }
            };
            reader.readAsDataURL(file);
        }

        if (removeBtn) {
            removeBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                fileInput.value = "";
                if (previewImg) previewImg.src = "";
                if (previewContainer) previewContainer.style.display = "none";
                dropzone.style.display = "block";
            });
        }
    }
});
