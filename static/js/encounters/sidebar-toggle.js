// Модуль для керування відображенням сайдбарів та нижнього бару

/**
 * Ініціалізує функціонал приховування/відображення сайдбарів та нижнього бару
 */
export function initializeSidebarToggle() {
    const leftSidebar = document.querySelector('.left-sidebar');
    const rightSidebar = document.querySelector('.right-sidebar');
    const bottomBar = document.getElementById('bottomBar');
    
    const leftToggleBtn = document.getElementById('leftSidebarToggle');
    const rightToggleBtn = document.getElementById('rightSidebarToggle');
    const bottomToggleBtn = document.getElementById('bottomBarToggle');

    // Функція для приховування/відображення лівого сайдбара
    leftToggleBtn.addEventListener('click', () => {
        leftSidebar.classList.toggle('hidden');
        leftToggleBtn.classList.toggle('sidebar-hidden');
        leftToggleBtn.textContent = leftSidebar.classList.contains('hidden') ? '▶' : '◀';
    });

    // Функція для приховування/відображення правого сайдбара
    rightToggleBtn.addEventListener('click', () => {
        rightSidebar.classList.toggle('hidden');
        rightToggleBtn.classList.toggle('sidebar-hidden');
        rightToggleBtn.textContent = rightSidebar.classList.contains('hidden') ? '◀' : '▶';
    });
    
    // Функція для приховування/відображення нижнього бару
    bottomToggleBtn.addEventListener('click', () => {
        bottomBar.classList.toggle('hidden');
        bottomToggleBtn.classList.toggle('sidebar-hidden');
        bottomToggleBtn.textContent = bottomBar.classList.contains('hidden') ? '▼' : '▲';
    });
}