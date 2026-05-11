// Модуль для роботи з сіткою
export function createGrid(width, height) {
    const gridContainer = document.getElementById('gridContainer');
    gridContainer.style.gridTemplateColumns = `repeat(${width}, 50px)`;
    gridContainer.style.gridTemplateRows = `repeat(${height}, 50px)`;

    for (let i = 0; i < height; i++) {
        for (let j = 0; j < width; j++) {
            const cell = document.createElement('div');
            cell.className = 'grid-cell';
            cell.dataset.x = j;
            cell.dataset.y = i;
            gridContainer.appendChild(cell);
        }
    }

    initializeDragging();
}

export function initializeDragging() {
    const gameField = document.querySelector('.game-field');
    const gridContainer = document.getElementById('gridContainer');
    let isDragging = false;
    let currentX;
    let currentY;
    let initialX;
    let initialY;
    let xOffset = 0;
    let yOffset = 0;
    let scale = 1;

    gameField.addEventListener('wheel', function(e) {
        e.preventDefault();
        const delta = e.deltaY;
        const scaleChange = delta > 0 ? 0.9 : 1.1;
        scale = Math.min(Math.max(0.5, scale * scaleChange), 2.0);
        gridContainer.style.transform = `translate(${xOffset}px, ${yOffset}px) scale(${scale})`;
    });

    gameField.addEventListener('mousedown', dragStart);
    gameField.addEventListener('mousemove', drag);
    gameField.addEventListener('mouseup', dragEnd);
    gameField.addEventListener('mouseleave', dragEnd);

    function dragStart(e) {
        // Перевіряємо, чи активний режим множинного заповнення
        if (document.body.classList.contains('multi-select-mode')) {
            // В режимі множинного заповнення забороняємо переміщення поля
            isDragging = false;
            return;
        }
        
        initialX = e.clientX - xOffset;
        initialY = e.clientY - yOffset;

        if (e.target === gridContainer || e.target.classList.contains('grid-cell')) {
            isDragging = true;
        }
    }

    function drag(e) {
        // Перевіряємо, чи активний режим множинного заповнення
        if (document.body.classList.contains('multi-select-mode')) {
            // В режимі множинного заповнення забороняємо переміщення поля
            isDragging = false;
            return;
        }
        
        if (isDragging) {
            e.preventDefault();
            currentX = e.clientX - initialX;
            currentY = e.clientY - initialY;

            xOffset = currentX;
            yOffset = currentY;

            gridContainer.style.transform = `translate(${currentX}px, ${currentY}px) scale(${scale})`;
        }
    }

    function dragEnd() {
        isDragging = false;
    }
}