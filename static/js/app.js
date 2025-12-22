document.addEventListener("DOMContentLoaded", () => {
    const generateBtn = document.getElementById("generate-btn");
    let configData = {};

    fetch("/api/config")
        .then(res => res.json())
        .then(data => {
            configData = data;
            initForm();
        })
        .catch(err => console.error("Error loading config:", err));

    function initForm() {
        populateThemes();
        populateAllQuestionTypes();
        setupAddQuestionTypeButtons();
        setupDeleteButtons();
        updateAddButtonVisibility();
        for (let i = 1; i <= 4; i++) {
            updateQuestionCountDisplay(i.toString());
        }
        checkFormCompletion();
    }

    function populateAllQuestionTypes() {
        document.querySelectorAll(".question-type-select").forEach(select => {
            populateQuestionTypes(select);
        });
    }

    function populateThemes() {
        const themeSelect = document.getElementById("global-theme-select");
        if (!themeSelect) return;

        Object.keys(configData.Theme).forEach(theme => {
            const opt = document.createElement("option");
            opt.value = theme;
            opt.textContent = theme;
            themeSelect.appendChild(opt);
        });

        themeSelect.addEventListener("change", () => {
            updateAllTopics(themeSelect.value);
            checkFormCompletion();
        });
    }

    function updateAllTopics(theme) {
        document.querySelectorAll(".topic-select").forEach(select => {
            select.innerHTML = `<option value="">Select Topic</option>`;
            if (!theme) return;
            configData.Theme[theme].Topic.forEach(topic => {
                const opt = document.createElement("option");
                opt.value = topic;
                opt.textContent = topic;
                select.appendChild(opt);
            });
        });
    }

    function populateQuestionTypes(selectElement) {
        if (!selectElement) return;
        const part = selectElement.dataset.part;
        if (!configData.Part || !configData.Part[part]) return;
        
        const firstOption = selectElement.querySelector("option[value='']");
        selectElement.innerHTML = "";
        if (firstOption) {
            selectElement.appendChild(firstOption);
        } else {
            const opt = document.createElement("option");
            opt.value = "";
            opt.textContent = "Select Question Type";
            selectElement.appendChild(opt);
        }
        
        const types = configData.Part[part].type;
        Object.keys(types).forEach(typeId => {
            const opt = document.createElement("option");
            opt.value = typeId;
            opt.textContent = typeId + " - " + types[typeId].description;
            selectElement.appendChild(opt);
        });
    }

    function getTotalQuestionsForPart(partNum) {
        let total = 0;
        const partContainer = document.querySelector(`.part-container[data-part="${partNum}"]`);
        if (!partContainer) return 0;
        
        partContainer.querySelectorAll(".question-numbers-input").forEach(input => {
            const value = parseInt(input.value) || 0;
            total += value;
        });
        return total;
    }

    function getQuestionTypeCountForPart(partNum) {
        const partContainer = document.querySelector(`.part-container[data-part="${partNum}"]`);
        if (!partContainer) return 0;
        return partContainer.querySelectorAll(".question-type-block").length;
    }

    function updateQuestionNumberMax(partNum) {
        const partContainer = document.querySelector(`.part-container[data-part="${partNum}"]`);
        if (!partContainer) return;
        
        partContainer.querySelectorAll(".question-numbers-input").forEach(input => {
            const currentValue = parseInt(input.value) || 0;
            const otherTotal = getTotalQuestionsForPart(partNum) - currentValue;
            const remaining = 10 - otherTotal;
            const maxValue = Math.max(1, Math.min(10, remaining));
            
            input.max = maxValue;
            if (currentValue > maxValue) {
                input.value = maxValue;
            }
        });
    }

    function updateQuestionCountDisplay(partNum) {
        const countElement = document.querySelector(`.question-count[data-part="${partNum}"]`);
        if (countElement) {
            const totalQuestions = getTotalQuestionsForPart(partNum);
            countElement.textContent = `(${totalQuestions}/10 questions)`;
            if (totalQuestions === 10) {
                countElement.style.color = "#90EE90";
                countElement.style.fontWeight = "bold";
            } else {
                countElement.style.color = "#ffffff";
                countElement.style.fontWeight = "normal";
            }
        }
    }

    function updateAddButtonVisibility() {
        document.querySelectorAll(".add-question-type-btn").forEach(btn => {
            const partNum = btn.dataset.part;
            const totalQuestions = getTotalQuestionsForPart(partNum);
            const questionTypeCount = getQuestionTypeCountForPart(partNum);
            
            if (totalQuestions >= 10 || questionTypeCount >= 2) {
                btn.style.display = "none";
            } else {
                btn.style.display = "block";
            }
            
            updateQuestionCountDisplay(partNum);
        });
        
        for (let i = 1; i <= 4; i++) {
            updateQuestionCountDisplay(i.toString());
        }
    }

    function setupAddQuestionTypeButtons() {
        document.querySelectorAll(".add-question-type-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const partNum = btn.dataset.part;
                const partContainer = document.querySelector(`.part-container[data-part="${partNum}"]`);
                if (!partContainer) return;
                
                const questionTypeCount = getQuestionTypeCountForPart(partNum);
                if (questionTypeCount >= 2) return;
                
                const newTypeNum = questionTypeCount + 1;
                const theme = document.getElementById("global-theme-select")?.value;
                
                const newBlock = document.createElement("div");
                newBlock.className = "question-type-block";
                newBlock.dataset.type = newTypeNum;
                newBlock.style.background = "rgba(255, 255, 255, 0.15)";
                newBlock.style.padding = "1rem";
                newBlock.style.borderRadius = "10px";
                newBlock.style.position = "relative";
                
                newBlock.innerHTML = `
                    <button class="delete-question-type-btn" data-part="${partNum}" data-type="${newTypeNum}" style="position: absolute; top: 0.5rem; right: 0.5rem; padding: 0.4rem 0.8rem; border-radius: 6px; border: none; background-color: #ff4444; color: #ffffff; font-weight: bold; cursor: pointer; font-size: 0.85rem;">Delete</button>
                    <label>Select Question Type:</label>
                    <select class="question-type-select" data-part="${partNum}" data-type="${newTypeNum}">
                        <option value="">Select Question Type</option>
                    </select>
                    <label>Select Topic:</label>
                    <select class="topic-select" data-part="${partNum}" data-type="${newTypeNum}">
                        <option value="">Select Topic</option>
                    </select>
                    <label>Specifications:</label>
                    <textarea class="specifications-input" data-part="${partNum}" data-type="${newTypeNum}" placeholder="Enter any specific requirements"></textarea>
                    <label>Question Numbers:</label>
                    <input type="number" class="question-numbers-input" data-part="${partNum}" data-type="${newTypeNum}" min="1" max="10" placeholder="Select Number of Questions in This Part">
                `;
                
                btn.parentNode.insertBefore(newBlock, btn);
                
                const newSelect = newBlock.querySelector(".question-type-select");
                populateQuestionTypes(newSelect);
                
                if (theme) {
                    const topicSelect = newBlock.querySelector(".topic-select");
                    updateTopicsForSelect(topicSelect, theme);
                }
                
                const currentTotal = getTotalQuestionsForPart(partNum);
                const remainingQuestions = 10 - currentTotal;
                const newQuestionInput = newBlock.querySelector(".question-numbers-input");
                
                if (currentTotal > 0 && remainingQuestions > 0 && remainingQuestions <= 10) {
                    newQuestionInput.value = remainingQuestions;
                }
                
                const deleteBtn = newBlock.querySelector(".delete-question-type-btn");
                deleteBtn.addEventListener("click", () => {
                    newBlock.remove();
                    updateAddButtonVisibility();
                    updateQuestionNumberMax(partNum);
                    updateQuestionCountDisplay(partNum);
                    checkFormCompletion();
                });
                
                setupQuestionTypeBlockListeners(newBlock);
                
                updateQuestionNumberMax(partNum);
                updateAddButtonVisibility();
                updateQuestionCountDisplay(partNum);
                checkFormCompletion();
            });
        });
    }

    function setupDeleteButtons() {
        document.querySelectorAll(".delete-question-type-btn").forEach(btn => {
            btn.addEventListener("click", (e) => {
                e.preventDefault();
                const block = btn.closest(".question-type-block");
                if (!block) return;
                
                const partNum = btn.dataset.part || block.querySelector(".question-type-select")?.dataset.part;
                
                block.remove();
                updateAddButtonVisibility();
                if (partNum) {
                    updateQuestionNumberMax(partNum);
                    updateQuestionCountDisplay(partNum);
                }
                checkFormCompletion();
            });
        });
    }

    function setupQuestionTypeBlockListeners(block) {
        const qTypeSelect = block.querySelector(".question-type-select");
        const topicSelect = block.querySelector(".topic-select");
        const qNumberInput = block.querySelector(".question-numbers-input");
        const partNum = qTypeSelect?.dataset.part || block.querySelector(".question-type-select")?.dataset.part;
        
        if (qTypeSelect) {
            qTypeSelect.addEventListener("change", () => {
                checkFormCompletion();
            });
        }
        
        if (topicSelect) {
            topicSelect.addEventListener("change", () => {
                checkFormCompletion();
            });
        }
        
        if (qNumberInput) {
            qNumberInput.addEventListener("input", () => {
                if (partNum) {
                    updateQuestionNumberMax(partNum);
                    updateAddButtonVisibility();
                    updateQuestionCountDisplay(partNum);
                }
                checkFormCompletion();
            });
        }
    }

    function updateTopicsForSelect(selectElement, theme) {
        if (!selectElement || !theme) return;
        selectElement.innerHTML = `<option value="">Select Topic</option>`;
        configData.Theme[theme].Topic.forEach(topic => {
            const opt = document.createElement("option");
            opt.value = topic;
            opt.textContent = topic;
            selectElement.appendChild(opt);
        });
    }

    document.querySelectorAll(".question-type-block").forEach(block => {
        setupQuestionTypeBlockListeners(block);
    });

    function checkFormCompletion() {
        if (!generateBtn) return;
        let allFilled = true;
        
        const theme = document.getElementById("global-theme-select")?.value;
        if (!theme) allFilled = false;

        let totalQuestionsAllParts = 0;
        for (let partNum = 1; partNum <= 4; partNum++) {
            const totalQuestions = getTotalQuestionsForPart(partNum);
            totalQuestionsAllParts += totalQuestions;
            if (totalQuestions !== 10) {
                allFilled = false;
            }
        }

        if (totalQuestionsAllParts !== 40) {
            allFilled = false;
        }

        document.querySelectorAll(".question-type-block").forEach(block => {
            const qType = block.querySelector(".question-type-select")?.value;
            const topic = block.querySelector(".topic-select")?.value;
            const qNumber = block.querySelector(".question-numbers-input")?.value;
            if (!qType || !topic || !qNumber) allFilled = false;
        });

        generateBtn.disabled = !allFilled;
    }

    document.addEventListener("change", (e) => {
        if (e.target.matches(".question-type-select, .topic-select, .question-numbers-input, #global-theme-select")) {
            if (e.target.matches("#global-theme-select")) {
                updateAllTopics(e.target.value);
            }
            if (e.target.matches(".question-numbers-input")) {
                const partNum = e.target.dataset.part;
                updateQuestionNumberMax(partNum);
                updateAddButtonVisibility();
                updateQuestionCountDisplay(partNum);
            }
            checkFormCompletion();
        }
    });

    if (generateBtn) {
        generateBtn.addEventListener("click", () => {
            const data = { Themes: [], Part: {} };
            const theme = document.getElementById("global-theme-select").value;
            data.Themes.push(theme);

            document.querySelectorAll(".part-container").forEach(partContainer => {
                const partNum = partContainer.dataset.part;
                data.Part[partNum] = { type1: [], topic: [], specifications: [], number_of_questions: [] };

                partContainer.querySelectorAll(".question-type-block").forEach(block => {
                    data.Part[partNum].type1.push(block.querySelector(".question-type-select").value);
                    data.Part[partNum].topic.push(block.querySelector(".topic-select").value);
                    data.Part[partNum].specifications.push(block.querySelector(".specifications-input").value);
                    data.Part[partNum].number_of_questions.push(parseInt(block.querySelector(".question-numbers-input").value) || 0);
                });
            });

            const generateWithAudio = confirm("Do you want to generate questions with audio?\n\nOK => Generate with audio\nCancel => Generate question only (audio can be generated later).");
            
            localStorage.setItem("questionData", JSON.stringify(data));
            localStorage.setItem("generateWithAudio", generateWithAudio ? "true" : "false");
            
            window.location.href = "/result";
        });
    }
});