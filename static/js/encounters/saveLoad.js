// Функціональність збереження та завантаження сесій

export class SessionSaveLoad {
    constructor() {
        this.sessionId = this.getSessionIdFromUrl();
        this.setupEventListeners();
        this.checkForExistingSave();
    }

    // Отримання ID сесії з URL
    getSessionIdFromUrl() {
        const pathParts = window.location.pathname.split('/');
        const sessionIndex = pathParts.indexOf('session');
        if (sessionIndex !== -1 && pathParts[sessionIndex + 1]) {
            return parseInt(pathParts[sessionIndex + 1]);
        }
        return null;
    }

    // Налаштування слухачів подій
    setupEventListeners() {
        const saveBtn = document.getElementById('saveSessionBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveSession());
        }
    }

    // Перевірка наявності збереженої сесії
    async checkForExistingSave() {
        if (!this.sessionId) return;

        try {
            const response = await fetch(`/api/session/${this.sessionId}/load`);
            const result = await response.json();

            if (result.has_save) {
                this.loadSession(result.data);
            }
        } catch (error) {
            console.error('Помилка при перевірці збереженої сесії:', error);
        }
    }

    // Збирання даних про поточний стан гри
    collectGameData() {
        const gridContainer = document.getElementById('gridContainer');
        if (!gridContainer) return null;

        // Отримуємо розміри сітки
        const gridStyle = window.getComputedStyle(gridContainer);
        const gridTemplateColumns = gridStyle.gridTemplateColumns;
        const gridTemplateRows = gridStyle.gridTemplateRows;
        
        const gridWidth = gridTemplateColumns.split(' ').length;
        const gridHeight = gridTemplateRows.split(' ').length;

        // Збираємо інформацію про токени
        const tokens = [];
        const cells = gridContainer.querySelectorAll('.grid-cell');
        
        cells.forEach(cell => {
            const sprites = cell.querySelectorAll('.sprite');
            sprites.forEach(sprite => {
                const tokenData = {
                    x: parseInt(cell.dataset.x),
                    y: parseInt(cell.dataset.y),
                    src: sprite.src,
                    alt: sprite.alt,
                    health: parseInt(sprite.dataset.health) || 7,
                    maxHealth: parseInt(sprite.dataset.maxHealth) || 20,
                    ac: parseInt(sprite.dataset.ac) || 12,
                    speed: parseInt(sprite.dataset.speed) || 30,
                    isBackground: sprite.src.includes('/environment/')
                };
                tokens.push(tokenData);
            });
        });

        // Отримуємо список ініціативи
        const initiativeList = [];
        const initiativeItems = document.querySelectorAll('.initiative-item');
        
        initiativeItems.forEach(item => {
            const img = item.querySelector('.initiative-sprite img');
            const name = item.querySelector('.initiative-name');
            const hpText = item.querySelector('.initiative-hp');
            const initiativeText = item.querySelector('.initiative-value');
            
            if (img && name) {
                const initiativeData = {
                    id: item.dataset.tokenId,
                    name: name.textContent,
                    sprite: img.src,
                    hp: parseInt(hpText.textContent.replace('HP: ', '')) || 0,
                    initiative: parseInt(initiativeText.textContent.replace('Ініціатива: ', '')) || 0
                };
                initiativeList.push(initiativeData);
            }
        });

        return {
            grid_width: gridWidth,
            grid_height: gridHeight,
            tokens: tokens,
            initiative_list: initiativeList
        };
    }

    // Збереження сесії
    async saveSession() {
        if (!this.sessionId) {
            alert('Помилка: не вдалося визначити ID сесії');
            return;
        }

        const gameData = this.collectGameData();
        if (!gameData) {
            alert('Помилка: не вдалося зібрати дані гри');
            return;
        }

        try {
            const response = await fetch(`/api/session/${this.sessionId}/save`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(gameData)
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                alert('Сесію успішно збережено!');
            } else {
                alert('Помилка при збереженні: ' + (result.error || 'Невідома помилка'));
            }
        } catch (error) {
            console.error('Помилка при збереженні сесії:', error);
            alert('Помилка при збереженні сесії');
        }
    }

    // Завантаження сесії
    async loadSession(saveData) {
        // Приховуємо модальне вікно розмірності поля
        const modal = document.getElementById('gridSizeModal');
        if (modal) {
            modal.classList.remove('active');
        }

        // Створюємо сітку з збережених даних
        this.createGridFromSave(saveData.grid_width, saveData.grid_height);

        // Переконуємося, що ініціатива завантажена
        if (window.initiativeTracker) {
            console.log('Завантаження інформації про кампанію перед завантаженням токенів...');
            try {
                // Завантажуємо інформацію про кампанію перед завантаженням токенів
                await window.initiativeTracker.loadCampaignInfo();
            } catch (error) {
                console.error('Помилка при завантаженні інформації про кампанію:', error);
            }
        }

        // Завантажуємо токени після короткої затримки
        setTimeout(() => {
            this.loadTokens(saveData.tokens);
            this.loadInitiativeList(saveData.initiative_list);
        }, 100);
    }

    // Створення сітки з збережених даних
    createGridFromSave(width, height) {
        const gridContainer = document.getElementById('gridContainer');
        if (!gridContainer) return;

        // Очищуємо існуючу сітку
        gridContainer.innerHTML = '';
        gridContainer.style.gridTemplateColumns = `repeat(${width}, 50px)`;
        gridContainer.style.gridTemplateRows = `repeat(${height}, 50px)`;

        // Створюємо клітинки
        for (let i = 0; i < height; i++) {
            for (let j = 0; j < width; j++) {
                const cell = document.createElement('div');
                cell.className = 'grid-cell';
                cell.dataset.x = j;
                cell.dataset.y = i;
                gridContainer.appendChild(cell);
            }
        }

        // Ініціалізуємо перетягування для нової сітки
        if (window.initializeDragging) {
            window.initializeDragging();
        }
    }

    // Завантаження токенів
    loadTokens(tokens) {
        const gridContainer = document.getElementById('gridContainer');
        if (!gridContainer) return;

        tokens.forEach(tokenData => {
            const cell = gridContainer.querySelector(`[data-x="${tokenData.x}"][data-y="${tokenData.y}"]`);
            if (cell) {
                const sprite = document.createElement('img');
                sprite.src = tokenData.src;
                sprite.alt = tokenData.alt;
                sprite.className = 'sprite';
                sprite.dataset.health = tokenData.health;
                sprite.dataset.maxHealth = tokenData.maxHealth;
                sprite.dataset.ac = tokenData.ac;
                sprite.dataset.speed = tokenData.speed || 30;
                
                cell.appendChild(sprite);
            }
        });
    }

    // Завантаження списку ініціативи
    loadInitiativeList(initiativeList) {
        // Емітуємо події для кожного токена з ініціативи
        initiativeList.forEach(tokenData => {
            const event = new CustomEvent('load-initiative-token', {
                detail: tokenData
            });
            document.dispatchEvent(event);
        });
    }
}

// Експортуємо функцію ініціалізації
export function initializeSaveLoad() {
    return new SessionSaveLoad();
}