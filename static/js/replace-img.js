document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("img").forEach(img => {
        img.onerror = function () {
            this.onerror = null;
            this.src = "{url_for('static', filename='img/question-mark.png')}";
        };
    });
});
