// Головний модуль для encounters
import { createGrid, initializeDragging } from './grid.js';
import { loadSprites, createTokenInfo } from './tokens.js';
import { startAttack } from './attacks.js';
import { initializeUI, initializeDragAndDrop } from './ui.js';
import { InitiativeTracker } from './initiative.js';
import { initializeSaveLoad } from './saveLoad.js';

// Ініціалізуємо систему збереження
let saveLoadSystem;
let initiativeTracker;

document.addEventListener('DOMContentLoaded', function() {
    // Ініціалізуємо систему збереження/завантаження
    saveLoadSystem = initializeSaveLoad();
    // Ініціалізуємо трекер ініціативи
    initiativeTracker = initializeInitiativeTracker();
    // Змінні для виділення області
    let isSelecting = false;
    let startCell = null;
    let selectedSprite = null;
    let selectionBox = document.createElement('div');
    selectionBox.className = 'selection-box';
    selectionBox.style.display = 'none';
    document.querySelector('.game-field').appendChild(selectionBox);

    // Завантаження спрайтів
    loadSprites();

    // Показуємо модальне вікно при завантаженні сторінки
    const modal = document.getElementById('gridSizeModal');
    modal.classList.add('active');

    // Обробка створення сітки
    document.getElementById('createGrid').addEventListener('click', function() {
        const width = parseInt(document.getElementById('gridWidth').value);
        const height = parseInt(document.getElementById('gridHeight').value);

        if (width > 0 && height > 0) {
            createGrid(width, height);
            modal.classList.remove('active');
        }
    });

    // Ініціалізація інтерфейсу
    initializeUI();
    initializeDragAndDrop();

    // Обробка події додавання нового токена
    document.addEventListener('token-added', async (e) => {
        const tokenData = e.detail;
        await initiativeTracker.addToken(tokenData);
    });

    // Обробка події оновлення HP токена
    document.addEventListener('token-hp-updated', (e) => {
        const { tokenId, newHP } = e.detail;
        initiativeTracker.updateTokenHP(tokenId, newHP);
    });

    // Обробка події видалення токена
    document.addEventListener('token-removed', (e) => {
        const { tokenId } = e.detail;
        initiativeTracker.removeToken(tokenId);
    });

    // Обробка події завантаження токена з ініціативи
    document.addEventListener('load-initiative-token', (e) => {
        const tokenData = e.detail;
        // Спочатку завантажуємо інформацію про кампанію, якщо вона ще не завантажена
        if (!initiativeTracker.campaignId) {
            initiativeTracker.loadCampaignInfo().then(() => {
                // Використовуємо метод addSavedToken замість прямого додавання
                initiativeTracker.addSavedToken(tokenData);
            });
        } else {
            // Якщо інформація про кампанію вже завантажена, просто додаємо токен
            initiativeTracker.addSavedToken(tokenData);
        }
    });
});

// Експортуємо функції для використання в saveLoad.js
window.initializeDragging = initializeDragging;

// Ініціалізація трекера ініціативи
function initializeInitiativeTracker() {
    const initiativeTracker = new InitiativeTracker();
    
    // Робимо ініціативу доступною глобально для saveLoad.js
    window.initiativeTracker = initiativeTracker;
    
    // Обробка події вибору токена
    document.addEventListener('token-selected', (e) => {
        const { token } = e.detail;
        initiativeTracker.addToken(token);
    });
    
    // Обробка події видалення токена
    document.addEventListener('token-removed', (e) => {
        const { tokenId } = e.detail;
        initiativeTracker.removeToken(tokenId);
    });

    // Обробка події завантаження токена з ініціативи
    document.addEventListener('load-initiative-token', (e) => {
        const tokenData = e.detail;
        // Спочатку завантажуємо інформацію про кампанію, якщо вона ще не завантажена
        if (!initiativeTracker.campaignId) {
            initiativeTracker.loadCampaignInfo().then(() => {
                // Використовуємо метод addSavedToken замість прямого додавання
                initiativeTracker.addSavedToken(tokenData);
            });
        } else {
            // Якщо інформація про кампанію вже завантажена, просто додаємо токен
            initiativeTracker.addSavedToken(tokenData);
        }
    });
    
    return initiativeTracker;
}