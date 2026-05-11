// Модуль для роботи з інтерфейсом
import { createTokenInfo } from './tokens.js';
import { initializeSidebarToggle } from './sidebar-toggle.js';
export function initializeUI() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            button.classList.add('active');
            const tabId = button.dataset.tab;
            document.getElementById(`${tabId}-content`).classList.add('active');
        });
    });
    
    // Додаємо кнопку для режиму множинного заповнення
    addMultiSelectButton();
    
    // Ініціалізуємо функціонал приховування/відображення сайдбарів
    initializeSidebarToggle();
    
    // Зберігаємо початковий стан ігрового поля після його створення
    // Використовуємо setTimeout, щоб дочекатися завершення створення сітки
    setTimeout(() => {
        saveGameState('Початковий стан');
    }, 1000);
}

// Функція для налаштування кнопок режимів заповнення
function addMultiSelectButton() {
    const normalModeBtn = document.getElementById('normalModeBtn');
    const multiSelectBtn = document.getElementById('multiSelectBtn');
    
    if (!normalModeBtn || !multiSelectBtn) return;
    
    // Встановлюємо початковий стан
    normalModeBtn.classList.add('active');
    
    // Додаємо обробники подій для кнопок
    normalModeBtn.addEventListener('click', () => {
        normalModeBtn.classList.add('active');
        multiSelectBtn.classList.remove('active');
        document.body.classList.remove('multi-select-mode');
        
        // Повертаємо можливість рухати ігрове поле
        const gridContainer = document.querySelector('.grid-container');
        if (gridContainer) {
            gridContainer.style.cursor = 'move';
        }
    });
    
    multiSelectBtn.addEventListener('click', () => {
        multiSelectBtn.classList.add('active');
        normalModeBtn.classList.remove('active');
        document.body.classList.add('multi-select-mode');
        
        // Забороняємо рухати ігрове поле в режимі множинного заповнення
        const gridContainer = document.querySelector('.grid-container');
        if (gridContainer) {
            gridContainer.style.cursor = 'default';
        }
    });
}

// Масив для зберігання історії змін
let actionHistory = [];
const MAX_HISTORY_LENGTH = 20; // Максимальна кількість кроків для скасування

// Функція для налаштування кнопки скасування змін
function addUndoButton() {
    const undoButton = document.getElementById('undoButton');
    
    if (!undoButton) return null;
    
    // Початково кнопка неактивна
    undoButton.disabled = true;
    undoButton.style.opacity = '0.5';
    
    // Додаємо обробник події для кнопки скасування
    undoButton.addEventListener('click', undoLastAction);
    
    return undoButton;
}

// Функція для збереження поточного стану ігрового поля
function saveGameState(action) {
    const gridContainer = document.getElementById('gridContainer');
    if (!gridContainer) return;
    
    // Створюємо глибоку копію поточного стану сітки
    const gridState = {
        action: action,
        timestamp: new Date().toISOString(),
        cells: []
    };
    
    // Зберігаємо стан кожної клітинки
    const cells = gridContainer.querySelectorAll('.grid-cell');
    cells.forEach(cell => {
        const cellState = {
            x: cell.dataset.x,
            y: cell.dataset.y,
            sprites: []
        };
        
        // Зберігаємо інформацію про кожен спрайт в клітинці
        const sprites = cell.querySelectorAll('.sprite');
        sprites.forEach(sprite => {
            cellState.sprites.push({
                src: sprite.src,
                type: sprite.dataset.type || (sprite.src.includes('/environment/') ? 'background' : 'token'),
                alt: sprite.alt || sprite.src.split('/').pop(),
                health: sprite.dataset.health,
                maxHealth: sprite.dataset.maxHealth,
                ac: sprite.dataset.ac,
                speed: sprite.dataset.speed
            });
        });
        
        gridState.cells.push(cellState);
    });
    
    // Додаємо стан до історії
    actionHistory.push(gridState);
    
    // Обмежуємо розмір історії
    if (actionHistory.length > MAX_HISTORY_LENGTH) {
        actionHistory.shift(); // Видаляємо найстаріший запис
    }
    
    // Активуємо кнопку скасування
    const undoButton = document.getElementById('undoButton');
    if (undoButton) {
        undoButton.disabled = false;
        undoButton.style.opacity = '1';
    }
    
    console.log(`Збережено стан: ${action}. Розмір історії: ${actionHistory.length}`);
    return gridState;
}

// Функція для відновлення попереднього стану
function undoLastAction() {
    if (actionHistory.length === 0) return;
    
    // Видаляємо поточний стан з історії
    const previousState = actionHistory.pop();
    
    // Якщо історія порожня, деактивуємо кнопку скасування
    if (actionHistory.length === 0) {
        const undoButton = document.getElementById('undoButton');
        if (undoButton) {
            undoButton.disabled = true;
            undoButton.style.opacity = '0.5';
        }
    }
    
    // Відновлюємо стан з попереднього запису
    restoreGameState(previousState);
    
    console.log(`Скасовано дію: ${previousState.action}. Залишилось в історії: ${actionHistory.length}`);
}

// Функція для відновлення стану ігрового поля
function restoreGameState(state) {
    const gridContainer = document.getElementById('gridContainer');
    if (!gridContainer) return;
    
    // Очищаємо всі клітинки від спрайтів
    const cells = gridContainer.querySelectorAll('.grid-cell');
    cells.forEach(cell => {
        const sprites = cell.querySelectorAll('.sprite');
        sprites.forEach(sprite => sprite.remove());
    });
    
    // Відновлюємо спрайти в кожній клітинці
    state.cells.forEach(cellState => {
        const cell = gridContainer.querySelector(`.grid-cell[data-x="${cellState.x}"][data-y="${cellState.y}"]`);
        if (!cell) return;
        
        // Сортуємо спрайти: спочатку фони, потім токени
        const backgrounds = cellState.sprites.filter(sprite => sprite.type === 'background');
        const tokens = cellState.sprites.filter(sprite => sprite.type !== 'background');
        
        // Додаємо спрайти в правильному порядку
        [...backgrounds, ...tokens].forEach(spriteState => {
            const sprite = document.createElement('img');
            sprite.className = 'sprite';
            sprite.src = spriteState.src;
            sprite.dataset.type = spriteState.type;
            sprite.draggable = true;
            
            // Встановлюємо атрибути для токенів
            if (spriteState.type !== 'background') {
                // Використовуємо збережені атрибути або встановлюємо значення за замовчуванням
                sprite.alt = spriteState.alt || spriteState.src.split('/').pop();
                sprite.dataset.health = spriteState.health || '7';
                sprite.dataset.maxHealth = spriteState.maxHealth || '20';
                sprite.dataset.ac = spriteState.ac || '12';
                sprite.dataset.speed = spriteState.speed || '30';
            }
            
            // Додаємо обробник кліку для всіх спрайтів
            sprite.addEventListener('click', function() {
                createTokenInfo(this);
            });
            
            cell.appendChild(sprite);
        });
    });
    
    // Оновлюємо інформацію про токени після відновлення
    const tokenInfoPanel = document.querySelector('.token-info');
    if (tokenInfoPanel) {
        const title = tokenInfoPanel.querySelector('.token-name');
        if (title) {
            title.textContent = 'Пуста клітинка';
        }
    }
}

export function initializeDragAndDrop() {
    let isDraggingSprite = false;
    let draggedElement = null;
    let lastSourceCell = null;
    let selectedCells = [];
    let isSelecting = false;
    let selectionBox = null;
    let startX, startY;
    let selectedSprite = null;
    
    // Додаємо кнопку скасування змін
    const undoButton = addUndoButton();

    function logSpriteState(action, cell) {
        const sprites = cell.querySelectorAll('.sprite');
        const spriteInfo = Array.from(sprites).map(sprite => ({
            type: sprite.dataset.type || 'невідомий',
            src: sprite.src,
            isBackground: sprite.dataset.type === 'background'
        }));

        console.log(`[${action}] Стан клітинки (${cell.dataset.x}, ${cell.dataset.y}):`, {
            totalSprites: sprites.length,
            sprites: spriteInfo,
            hasBackground: cell.dataset.background === 'true',
            cellType: cell.dataset.type
        });
    }
    
    // Функція для створення рамки вибору
    function createSelectionBox(x, y) {
        const box = document.createElement('div');
        box.className = 'selection-box';
        box.style.left = `${x}px`;
        box.style.top = `${y}px`;
        box.style.width = '0';
        box.style.height = '0';
        document.body.appendChild(box);
        return box;
    }
    
    // Функція для оновлення рамки вибору
    function updateSelectionBox(box, x1, y1, x2, y2) {
        const left = Math.min(x1, x2);
        const top = Math.min(y1, y2);
        const width = Math.abs(x2 - x1);
        const height = Math.abs(y2 - y1);
        
        box.style.left = `${left}px`;
        box.style.top = `${top}px`;
        box.style.width = `${width}px`;
        box.style.height = `${height}px`;
    }
    
    // Функція для вибору клітинок в межах рамки
    function selectCellsInBox(box) {
        const boxRect = box.getBoundingClientRect();
        const gridCells = document.querySelectorAll('.grid-cell');
        
        // Очищаємо попередній вибір
        clearCellSelection();
        
        gridCells.forEach(cell => {
            const cellRect = cell.getBoundingClientRect();
            
            // Перевіряємо, чи перетинається клітинка з рамкою вибору
            if (!(boxRect.right < cellRect.left || 
                  boxRect.left > cellRect.right || 
                  boxRect.bottom < cellRect.top || 
                  boxRect.top > cellRect.bottom)) {
                
                // Додаємо клітинку до вибраних
                cell.classList.add('selected-cell');
                cell.style.backgroundColor = 'rgba(76, 175, 80, 0.2)';
                cell.style.border = '2px solid #4CAF50';
                selectedCells.push(cell);
            }
        });
    }
    
    // Функція для очищення вибору клітинок
    function clearCellSelection() {
        selectedCells.forEach(cell => {
            cell.classList.remove('selected-cell');
            cell.style.backgroundColor = '';
            cell.style.border = '1px solid #bdc3c7';
        });
        selectedCells = [];
    }
    
    // Функція для заповнення вибраних клітинок спрайтом
    function fillSelectedCells(sprite) {
        if (!sprite) return;
        
        // Зберігаємо стан перед заповненням
        saveGameState('Заповнення множинних клітинок');
        
        selectedCells.forEach(cell => {
            // Перевіряємо, чи це фон оточення
            const isBackground = sprite.src.includes('/environment/');
            
            // Збираємо існуючі спрайти в клітинці
            const existingSprites = cell.querySelectorAll('.sprite');
            const existingBackgrounds = Array.from(existingSprites).filter(s => s.src.includes('/environment/'));
            const existingTokens = Array.from(existingSprites).filter(s => !s.src.includes('/environment/'));
            
            // Створюємо новий спрайт
            const newSprite = sprite.cloneNode(true);
            
            // Якщо новий спрайт - фон оточення
            if (isBackground) {
                // Видаляємо існуючі фони оточення
                existingBackgrounds.forEach(bg => bg.remove());
                
                // Додаємо новий фон оточення першим елементом (під токенами)
                if (existingTokens.length > 0) {
                    // Видаляємо всі токени
                    existingTokens.forEach(token => token.remove());
                    // Додаємо фон
                    cell.appendChild(newSprite);
                    // Повертаємо всі токени
                    existingTokens.forEach(token => cell.appendChild(token));
                } else {
                    // Якщо токенів немає, просто додаємо фон
                    cell.appendChild(newSprite);
                }
            } else {
                // Якщо новий спрайт - токен або об'єкт, додаємо його поверх фону
                cell.appendChild(newSprite);
            }
            
            // Оновлюємо інформацію про спрайти в клітинці
            const sprites = cell.querySelectorAll('.sprite');
            sprites.forEach(s => {
                s.addEventListener('click', function() {
                    createTokenInfo(this);
                });
            });
            
            logSpriteState('Після заповнення', cell);
        });
    }

    // Обробник кліку на спрайт в панелі
    document.querySelectorAll('.tab-content').forEach(tabContent => {
        tabContent.addEventListener('click', function(e) {
            const spriteItem = e.target.closest('.sprite-item');
            if (spriteItem && document.body.classList.contains('multi-select-mode')) {
                // Знімаємо виділення з усіх спрайтів
                document.querySelectorAll('.sprite-item').forEach(item => {
                    item.classList.remove('selected');
                    item.style.border = '2px solid transparent';
                    item.style.backgroundColor = '';
                });
                
                // Виділяємо обраний спрайт
                spriteItem.classList.add('selected');
                spriteItem.style.border = '2px solid #4CAF50';
                spriteItem.style.backgroundColor = 'rgba(76, 175, 80, 0.1)';
                
                // Зберігаємо обраний спрайт
                const spriteImg = spriteItem.querySelector('img');
                if (spriteImg) {
                    selectedSprite = spriteImg;
                }
            }
        });
    });
    
    // Обробник для початку вибору клітинок
    document.addEventListener('mousedown', function(e) {
        // Перевіряємо, чи ми в режимі множинного вибору
        if (!document.body.classList.contains('multi-select-mode')) return;
        
        // Перевіряємо, чи клік був на ігровому полі
        const gameField = document.querySelector('.game-field');
        if (!gameField.contains(e.target)) return;
        
        // Починаємо вибір
        isSelecting = true;
        startX = e.clientX;
        startY = e.clientY;
        
        // Створюємо рамку вибору
        if (selectionBox) selectionBox.remove();
        selectionBox = createSelectionBox(startX, startY);
        
        // Запобігаємо стандартній поведінці перетягування
        e.preventDefault();
    });
    
    // Обробник для оновлення рамки вибору
    document.addEventListener('mousemove', function(e) {
        if (!isSelecting || !selectionBox) return;
        
        // Оновлюємо рамку вибору
        updateSelectionBox(selectionBox, startX, startY, e.clientX, e.clientY);
    });
    
    // Обробник для завершення вибору
    document.addEventListener('mouseup', function(e) {
        if (!isSelecting) return;
        
        // Вибираємо клітинки в межах рамки
        if (selectionBox) {
            selectCellsInBox(selectionBox);
            
            // Якщо є обраний спрайт, заповнюємо вибрані клітинки
            if (selectedSprite && selectedCells.length > 0) {
                fillSelectedCells(selectedSprite);
            }
            
            // Видаляємо рамку вибору
            selectionBox.remove();
            selectionBox = null;
        }
        
        isSelecting = false;
    });
    
    document.addEventListener('dragstart', function(e) {
        // Якщо ми в режимі множинного вибору, забороняємо перетягування
        if (document.body.classList.contains('multi-select-mode')) {
            e.preventDefault();
            return;
        }
        
        if (e.target.classList.contains('sprite')) {
            isDraggingSprite = true;
            draggedElement = e.target.cloneNode(true);
            const currentCell = e.target.closest('.grid-cell');
            
            e.dataTransfer.setData('text/plain', e.target.src);
            e.dataTransfer.setData('sourceCell', currentCell ? 'grid' : 'panel');
            e.dataTransfer.effectAllowed = 'move';
            lastSourceCell = currentCell;
        }
    });

    document.addEventListener('dragend', function() {
        isDraggingSprite = false;
        draggedElement = null;
    });

    document.addEventListener('dragover', function(e) {
        if (isDraggingSprite) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        }
    });

    document.addEventListener('drop', function(e) {
        if (!isDraggingSprite) return;

        e.preventDefault();
        const targetCell = e.target.closest('.grid-cell');
        if (!targetCell) return;
        
        // Зберігаємо стан перед перетягуванням
        saveGameState('Перетягування спрайту');

        const sourceType = e.dataTransfer.getData('sourceCell');
        const spriteSrc = e.dataTransfer.getData('text/plain');
        const existingSprite = targetCell.querySelector('.sprite');

        // Перевірка чи є існуючий спрайт оточенням
        // Збираємо всі спрайти в клітинці
        const existingSprites = targetCell.querySelectorAll('.sprite');
        const existingBackgrounds = Array.from(existingSprites).filter(sprite => sprite.src.includes('/environment/'));
        const existingTokens = Array.from(existingSprites).filter(sprite => !sprite.src.includes('/environment/'));
        
        const isNewSpriteBackground = draggedElement.src.includes('/environment/');

        // Перевіряємо чи це та сама клітинка
        if (sourceType === 'grid' && lastSourceCell === targetCell) {
            // Якщо перетягуємо в ту саму клітинку, нічого не робимо
            return;
        }

        // Видаляємо спрайт з початкової клітинки, якщо він був на полі
        if (sourceType === 'grid' && lastSourceCell) {
            // Якщо перетягуємо фон, видаляємо тільки фон з початкової клітинки
            if (isNewSpriteBackground) {
                const backgroundsToRemove = lastSourceCell.querySelectorAll('.sprite');
                backgroundsToRemove.forEach(sprite => {
                    if (sprite.src.includes('/environment/')) {
                        sprite.remove();
                    }
                });
            } else {
                // Якщо перетягуємо токен або об'єкт, видаляємо тільки його
                const tokensToRemove = lastSourceCell.querySelectorAll('.sprite');
                tokensToRemove.forEach(sprite => {
                    if (sprite.src === draggedElement.src) {
                        sprite.remove();
                    }
                });
            }
        }

        // Додаємо новий спрайт в цільову клітинку
        const newSprite = draggedElement.cloneNode(true);
        
        // Якщо новий спрайт - фон оточення
        if (isNewSpriteBackground) {
            // Видаляємо існуючі фони оточення
            existingBackgrounds.forEach(bg => bg.remove());
            
            // Додаємо новий фон оточення першим елементом (під токенами)
            if (existingTokens.length > 0) {
                // Видаляємо всі токени
                existingTokens.forEach(token => token.remove());
                // Додаємо фон
                targetCell.appendChild(newSprite);
                // Повертаємо всі токени
                existingTokens.forEach(token => targetCell.appendChild(token));
            } else {
                // Якщо токенів немає, просто додаємо фон
                targetCell.appendChild(newSprite);
            }
        } else {
            // Якщо новий спрайт - токен або об'єкт, додаємо його поверх фону
            targetCell.appendChild(newSprite);
        }

        // Оновлюємо інформацію про спрайти в клітинці
        const sprites = targetCell.querySelectorAll('.sprite');
        sprites.forEach(sprite => {
            sprite.addEventListener('click', function() {
                createTokenInfo(this);
            });
        });

        logSpriteState('Після перетягування', targetCell);
    });
}