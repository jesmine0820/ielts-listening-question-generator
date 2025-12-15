const modalIds = ["signup", "login", "forgot"];
const modals = Object.fromEntries(
    modalIds.map((id) => [id, document.getElementById(`${id}-modal`)])
);

function showModal(name) {
    modalIds.forEach((id) => {
        const modal = modals[id];
        if (!modal) return;
        if (id === name) {
            modal.classList.add("active");
        } else {
            modal.classList.remove("active");
        }
    });

    if (name !== "forgot") {
        resetForgotState();
    }
}

document.querySelectorAll("[data-modal]").forEach((el) => {
    el.addEventListener("click", (e) => {
        e.preventDefault();
        const target = el.getAttribute("data-modal");
        if (target) showModal(target);
    });
});