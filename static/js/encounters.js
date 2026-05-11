document.addEventListener('DOMContentLoaded', function() {
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

    // Створення сітки
    function createGrid(width, height) {
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

        // Ініціалізація перетягування сітки
        initializeDragging();
    }

    // Ініціалізація перетягування та масштабування
    function initializeDragging() {
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

        // Додаємо обробник для масштабування колесом миші
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
            initialX = e.clientX - xOffset;
            initialY = e.clientY - yOffset;

            if (e.target === gridContainer || e.target.classList.contains('grid-cell')) {
                isDragging = true;
            }
        }

        function drag(e) {
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

    // Функція для завантаження спрайтів
    // Функція для створення інформаційної панелі токена
// Функція для зміни здоров'я токена
function adjustHP(token, amount) {
    if (!token || !token.dataset) return;
    
    const currentHealth = parseInt(token.dataset.health) || 7;
    const maxHealth = parseInt(token.dataset.maxHealth) || 20;
    const newHealth = Math.max(0, Math.min(maxHealth, currentHealth + amount));
    
    token.dataset.health = newHealth;
    
    // Оновлюємо відображення здоров'я в інформаційній панелі
    const statsPanel = document.querySelector('.token-stats-panel');
    if (statsPanel) {
        const hpValue = statsPanel.querySelector('.hp-value');
        if (hpValue) {
            hpValue.textContent = `${newHealth}/${maxHealth}`;
            
            // Оновлюємо колір індикатора здоров'я
            const healthPercentage = (newHealth / maxHealth) * 100;
            hpValue.style.color = healthPercentage <= 25 ? 'red' : 
                                 healthPercentage <= 50 ? 'yellow' : 
                                 'white';
        }
    }
}

function createTokenInfo(token) {
    const tokenInfo = document.querySelector('.token-info');
    const statsPanel = document.querySelector('.token-stats-panel');
    if (!tokenInfo || !statsPanel) return;

    // Оновлюємо превью спрайту
    const spritePreview = tokenInfo.querySelector('.sprite-preview');
    spritePreview.innerHTML = '';

    // Оновлюємо заголовок та статистику
    const title = tokenInfo.querySelector('.token-name');
    const stats = statsPanel.querySelector('.stats');
    const actionButtons = statsPanel.querySelector('.action-buttons');
    const hpValue = statsPanel.querySelector('.hp-value');
    const acValue = statsPanel.querySelector('.ac-value');

    if (!token || !token.alt) {
        // Якщо немає токена, оновлюємо тільки значення
        title.textContent = 'Пуста клітинка';
        stats.style.display = 'none';
        actionButtons.style.display = 'none';
        hpValue.textContent = '-';
        acValue.textContent = '-';
        return;
    }

    // Додаємо превью токена
    const tokenPreview = token.cloneNode(true);
    tokenPreview.style.width = '50px';
    tokenPreview.style.height = '50px';
    spritePreview.appendChild(tokenPreview);

    // Оновлюємо заголовок
    title.textContent = token.alt.replace('.png', '');

    // Перевіряємо, чи це фоновий спрайт
    const isBackground = token.src.includes('/environment/');

    if (!isBackground) {
        // Показуємо статистику та кнопки
        stats.style.display = 'block';
        actionButtons.style.display = 'block';

        // Оновлюємо значення здоров'я та броні
        const currentHealth = parseInt(token.dataset.health) || 7;
        const maxHealth = parseInt(token.dataset.maxHealth) || 20;
        const armorClass = parseInt(token.dataset.ac) || 12;
        
        token.dataset.health = currentHealth;
        token.dataset.maxHealth = maxHealth;
        token.dataset.ac = armorClass;
        
        hpValue.textContent = `${currentHealth}/${maxHealth}`;
        acValue.textContent = armorClass;
        
        // Додаємо візуальну індикацію здоров'я
        const healthPercentage = (currentHealth / maxHealth) * 100;
        hpValue.style.color = healthPercentage <= 25 ? 'red' : 
                             healthPercentage <= 50 ? 'yellow' : 
                             'white';

        // Оновлюємо обробники подій для кнопок
        const minusBtn = statsPanel.querySelector('.minus');
        const plusBtn = statsPanel.querySelector('.plus');
        const attackBtn = statsPanel.querySelector('.attack-btn');

        // Видаляємо старі обробники подій
        minusBtn.removeEventListener('click', minusBtn.onclick);
        plusBtn.removeEventListener('click', plusBtn.onclick);
        attackBtn.removeEventListener('click', attackBtn.onclick);

        // Додаємо нові обробники подій
        minusBtn.onclick = () => adjustHP(tokenPreview, -1);
        plusBtn.onclick = () => adjustHP(tokenPreview, 1);
        attackBtn.onclick = () => startAttack(tokenPreview);
    } else {
        // Приховуємо статистику та кнопки для фонових спрайтів
        stats.style.display = 'none';
        actionButtons.style.display = 'none';
    }
}

// Функція для початку атаки
function startAttack(attacker) {
    if (!attacker || !attacker.dataset) return;

    const gameField = document.querySelector('.game-field');
    if (!gameField) return;

    const ray = document.createElement('div');
    ray.className = 'attack-ray';
    gameField.appendChild(ray);

    function updateRay(e) {
        const rect = attacker.getBoundingClientRect();
        const attackerCenter = {
            x: rect.left + rect.width / 2,
            y: rect.top + rect.height / 2
        };

        const angle = Math.atan2(e.clientY - attackerCenter.y, e.clientX - attackerCenter.x);
        const distance = Math.sqrt(
            Math.pow(e.clientX - attackerCenter.x, 2) + 
            Math.pow(e.clientY - attackerCenter.y, 2)
        );

        ray.style.width = `${distance}px`;
        ray.style.left = `${attackerCenter.x}px`;
        ray.style.top = `${attackerCenter.y}px`;
        ray.style.transform = `rotate(${angle}rad)`;
    }

    function handleClick(e) {
        const targetCell = e.target.closest('.grid-cell');
        const target = targetCell?.querySelector('.sprite');
        if (target && target !== attacker && !target.src.includes('/environment/')) {
            showAttackDialog(attacker, target);
        }
        cleanup();
    }

    function cleanup() {
        gameField.removeEventListener('mousemove', updateRay);
        gameField.removeEventListener('click', handleClick);
        ray.remove();
    }

    gameField.addEventListener('mousemove', updateRay);
    gameField.addEventListener('click', handleClick);
}

// Функція для показу діалогу атаки
function showAttackDialog(attacker, target) {
    const dialog = document.createElement('div');
    dialog.className = 'attack-dialog';
    dialog.innerHTML = `
        <div class="attack-dialog-content">
            <h3>Атака</h3>
            
            <!-- Ліва колонка - інформація про ціль та атаку -->
            <div>
                <p>Ціль: ${target.alt.replace('.png', '')}</p>
                <p>Здоров'я цілі: ${target.dataset.health || 7}</p>
                <p>Клас броні цілі: ${target.dataset.ac || 12}</p>
                
                <div class="attack-roll">
                    <button onclick="rollD20()">КИНУТИ К20</button>
                    <input type="number" id="attackBonus" value="0" min="0" max="20" placeholder="Бонус атаки">
                    <p id="rollResult"></p>
                </div>
                
                <button onclick="this.closest('.attack-dialog').remove()">Закрити</button>
            </div>
            
            <!-- Права колонка - кидок шкоди -->
            <div class="damage-roll" style="display: none">
                <h4>Кидок шкоди:</h4>
                <div class="dice-selection">
                    <label>к4: <input type="number" id="d4" value="0" min="0" max="10"></label>
                    <label>к6: <input type="number" id="d6" value="0" min="0" max="10"></label>
                    <label>к8: <input type="number" id="d8" value="0" min="0" max="10"></label>
                    <label>к10: <input type="number" id="d10" value="0" min="0" max="10"></label>
                    <label>к12: <input type="number" id="d12" value="0" min="0" max="10"></label>
                </div>
                
                <input type="number" id="damageBonus" value="0" placeholder="Модифікатор шкоди">
                
                <div class="damage-modifiers">
                    <label><input type="checkbox" id="resistance"> Супротив</label>
                    <label><input type="checkbox" id="vulnerability"> Вразливість</label>
                </div>
                
                <button onclick="rollDamage()">КИНУТИ НА ШКОДУ</button>
                <p id="damageResult"></p>
            </div>
        </div>
    `;
    document.body.appendChild(dialog);

    // Додаємо функції для кидків
    window.rollD20 = function() {
        const roll = Math.floor(Math.random() * 20) + 1;
        const bonus = parseInt(document.getElementById('attackBonus').value) || 0;
        const total = roll + bonus;
        const targetAC = parseInt(target.dataset.ac) || 12;
        const resultElement = document.getElementById('rollResult');
        resultElement.textContent = `Результат: ${total} (${roll} + ${bonus})`;
        
        if (total >= targetAC) {
            resultElement.style.color = 'green';
            document.querySelector('.damage-roll').style.display = 'block';
        } else {
            resultElement.style.color = 'red';
        }
    };

    window.rollDamage = function() {
        const diceTypes = [4, 6, 8, 10, 12];
        let totalDamage = 0;

        diceTypes.forEach(dice => {
            const count = parseInt(document.getElementById(`d${dice}`).value) || 0;
            for (let i = 0; i < count; i++) {
                totalDamage += Math.floor(Math.random() * dice) + 1;
            }
        });

        const bonus = parseInt(document.getElementById('damageBonus').value) || 0;
        totalDamage += bonus;

        if (document.getElementById('resistance').checked) {
            totalDamage = Math.floor(totalDamage / 2);
        }
        if (document.getElementById('vulnerability').checked) {
            totalDamage *= 2;
        }

        document.getElementById('damageResult').textContent = `Загальна шкода: ${totalDamage}`;

        // Оновлюємо здоров'я цілі
        const currentHealth = parseInt(target.dataset.health) || 7;
        target.dataset.health = Math.max(0, currentHealth - totalDamage);
        
        // Оновлюємо відображення здоров'я, якщо ціль вибрана
        const selectedContent = document.getElementById('selected-content');
        const healthSpan = selectedContent.querySelector('.health');
        if (healthSpan && selectedContent.contains(target)) {
            healthSpan.textContent = target.dataset.health;
        }
    };
}

function loadSprites() {
        fetch('/api/grid', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            // Завантаження токенів
            const tokensContent = document.getElementById('tokens-content');
            data.tokens.forEach(token => {
                const spriteItem = document.createElement('div');
                spriteItem.className = 'sprite-item';
                
                const img = document.createElement('img');
                img.src = `/static/sprites/tokens/${token}`;
                img.alt = token;
                
                const name = document.createElement('div');
                name.className = 'sprite-name';
                name.textContent = token.replace('.png', '');
                
                spriteItem.appendChild(img);
                spriteItem.appendChild(name);
                tokensContent.appendChild(spriteItem);
                img.classList.add('sprite');
                img.draggable = true;
                img.dataset.health = '7';
                img.dataset.ac = '12';

                spriteItem.addEventListener('click', function() {
                    document.querySelectorAll('.sprite-item').forEach(item => item.classList.remove('selected'));
                    this.classList.add('selected');
                });

                // Додаємо обробник для відображення інформації про токен
                img.addEventListener('click', function(e) {
                    createTokenInfo(this);
                });
            });

            // Завантаження об'єктів
            const objectsContent = document.getElementById('objects-content');
            data.objects.forEach(obj => {
                const spriteItem = document.createElement('div');
                spriteItem.className = 'sprite-item';
                
                const img = document.createElement('img');
                img.src = `/static/sprites/objects/${obj}`;
                img.alt = obj;
                img.classList.add('sprite');
                img.draggable = true;
                
                // Прибрано назви об'єктів, залишено лише зображення
                
                spriteItem.appendChild(img);
                objectsContent.appendChild(spriteItem);
            });

            // Завантаження оточення
            const environmentContent = document.getElementById('environment-content');
            data.environment.forEach(env => {
                const spriteItem = document.createElement('div');
                spriteItem.className = 'sprite-item';
                
                const img = document.createElement('img');
                img.src = `/static/sprites/environment/${env}`;
                img.alt = env;
                img.classList.add('sprite');
                img.draggable = true;
                
                const name = document.createElement('div');
                name.className = 'sprite-name';
                name.textContent = env.replace('.png', '');
                
                spriteItem.appendChild(img);
                spriteItem.appendChild(name);
                environmentContent.appendChild(spriteItem);
            });

        })
        .catch(error => console.error('Помилка завантаження спрайтів:', error));
    }

    // Обробка вкладок
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Видаляємо активний клас з усіх кнопок і контенту
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Додаємо активний клас вибраній вкладці
            button.classList.add('active');
            const tabId = button.dataset.tab;
            document.getElementById(`${tabId}-content`).classList.add('active');
        });
    });

    // Змінні для відстеження стану перетягування
    let isDraggingSprite = false;
    let draggedElement = null;
    let lastSourceCell = null;

    // Функція для логування стану спрайтів
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

    // Обробка початку перетягування
    document.addEventListener('dragstart', function(e) {
        if (e.target.classList.contains('sprite')) {
            isDraggingSprite = true;
            draggedElement = e.target.cloneNode(true);
            const currentCell = e.target.closest('.grid-cell');
            
            e.dataTransfer.setData('text/plain', e.target.src);
            e.dataTransfer.setData('sourceCell', currentCell ? 'grid' : 'panel');
            e.dataTransfer.effectAllowed = 'copy';
            
            if (currentCell) {
                lastSourceCell = currentCell;
                currentCell.dataset.dragging = 'true';
            }
            
            // Встановлюємо прозорість для елемента, що перетягується
            e.target.style.opacity = '0.6';
            
            logSpriteState('Початок перетягування', e.target);
            console.log('Деталі перетягування:', {
                sourceType: currentCell ? 'grid' : 'panel',
                sourceCoordinates: currentCell ? `x=${currentCell.dataset.x}, y=${currentCell.dataset.y}` : 'panel',
                spriteSource: e.target.src
            });
        }
    });

    // Дозволяємо drop на клітинках
    document.addEventListener('dragover', function(e) {
        const targetCell = e.target.closest('.grid-cell');
        if (targetCell) {
            const existingSprite = targetCell.querySelector('.sprite:not([data-type="background"])');
            const draggedIsBackground = draggedElement && draggedElement.src.includes('/environment/');
            
            // Якщо в клітинці вже є токен і ми намагаємось додати не фоновий спрайт
            if (existingSprite && !draggedIsBackground) {
                e.dataTransfer.dropEffect = 'none';
                targetCell.style.outline = '2px dashed #FF0000';
                return;
            }
            
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
            targetCell.style.outline = '2px dashed #4CAF50';
        }
    });

    // Видаляємо підсвічування при виході з клітинки
    document.addEventListener('dragleave', function(e) {
        const targetCell = e.target.closest('.grid-cell');
        if (targetCell) {
            targetCell.style.outline = 'none';
        }
    });

    // Обробка drop спрайту на клітинку
    document.addEventListener('drop', function(e) {
        const targetCell = e.target.closest('.grid-cell');
        if (!targetCell) {
            console.log('Drop відхилено: неправильна ціль');
            return;
        }
        
        e.preventDefault();
        const sourceCell = e.dataTransfer.getData('sourceCell');
        const spriteType = draggedElement.src.includes('/environment/') ? 'background' : 'sprite';

        // Очищаємо підсвічування
        targetCell.style.outline = 'none';

        logSpriteState('До drop', targetCell);

        // Перевіряємо, чи не відбувається вже інше перетягування
        if (targetCell.dataset.processing === 'true') {
            console.log('Drop відхилено: клітинка вже обробляється');
            return;
        }

        targetCell.dataset.processing = 'true';

        // Використовуємо клонований елемент
        const newSprite = draggedElement.cloneNode(true);
        newSprite.style.width = '100%';
        newSprite.style.height = '100%';
        newSprite.style.objectFit = 'contain';
        newSprite.dataset.type = spriteType;

        // Зберігаємо поточний стан клітинки
        const existingSprite = targetCell.querySelector('.sprite:not([data-type="background"])');
        const backgroundSprite = targetCell.querySelector('.sprite[data-type="background"]');

        if (spriteType === 'background') {
            // Видаляємо старий фон, якщо він є
            if (backgroundSprite) {
                targetCell.removeChild(backgroundSprite);
            }
            // Додаємо новий фон
            targetCell.insertBefore(newSprite, existingSprite);
            targetCell.dataset.background = 'true';
        } else {
            // Видаляємо старий спрайт, якщо він є
            if (existingSprite) {
                targetCell.removeChild(existingSprite);
            }
            // Додаємо новий спрайт після фону
            targetCell.appendChild(newSprite);
        }

        // Очищаємо початкову клітинку, якщо перетягування було з сітки
        if (sourceCell === 'grid' && lastSourceCell && lastSourceCell !== targetCell) {
            const sourceBackground = lastSourceCell.querySelector('.sprite[data-type="background"]');
            const sourceSprite = lastSourceCell.querySelector('.sprite:not([data-type="background"])');

            if (spriteType === 'background' && sourceBackground) {
                lastSourceCell.removeChild(sourceBackground);
                lastSourceCell.dataset.background = 'false';
            } else if (spriteType !== 'background' && sourceSprite) {
                lastSourceCell.removeChild(sourceSprite);
            }

            if (!lastSourceCell.querySelector('.sprite')) {
                lastSourceCell.dataset.type = '';
            }
            lastSourceCell.removeAttribute('data-dragging');
        }

        // Скидаємо стани перетягування
        isDraggingSprite = false;
        draggedElement = null;
        lastSourceCell = null;

        delete targetCell.dataset.processing;
        logSpriteState('Після drop', targetCell);
    });

    // Очищення станів після завершення перетягування
    document.addEventListener('dragend', function(e) {
        // Відновлюємо прозорість елемента
        if (e.target.classList.contains('sprite')) {
            e.target.style.opacity = '1';
        }

        if (lastSourceCell) {
            logSpriteState('Очищення початкової клітинки', lastSourceCell);
            lastSourceCell.removeAttribute('data-dragging');
        }
        
        // Очищаємо підсвічування всіх клітинок
        document.querySelectorAll('.grid-cell').forEach(cell => {
            cell.style.outline = 'none';
        });

        const processingCells = document.querySelectorAll('.grid-cell[data-processing]');
        processingCells.forEach(cell => {
            delete cell.dataset.processing;
        });
        
        if (isDraggingSprite) {
            isDraggingSprite = false;
            draggedElement = null;
            lastSourceCell = null;
        }
    });

    // Обробка входу в клітинку
    document.addEventListener('dragenter', function(e) {
        if (e.target.classList.contains('grid-cell') && isDraggingSprite) {
            console.log('Вхід в нову клітинку');
        }
    });

    // Обробка виходу з клітинки
    document.addEventListener('dragleave', function(e) {
        if (e.target.classList.contains('grid-cell')) {
            delete e.target.dataset.processing;
            console.log('Вихід з клітинки');
        }
    });
    // Обробка виділення області
    document.getElementById('gridContainer').addEventListener('mousedown', function(e) {
        console.log('MouseDown подія:', {
            shiftKey: e.shiftKey,
            isGridCell: e.target.classList.contains('grid-cell'),
            isSelecting: isSelecting
        });

        if (e.shiftKey && e.target.classList.contains('grid-cell')) {
            const sprite = document.querySelector('.sprite-item.selected img');
            console.log('Вибраний спрайт:', sprite);
            
            if (sprite) {
                e.preventDefault(); // Запобігаємо стандартній поведінці
                isSelecting = true;
                startCell = e.target;
                selectedSprite = sprite.cloneNode(true);
                selectedSprite.style.width = '100%';
                selectedSprite.style.height = '100%';
                selectedSprite.style.objectFit = 'contain';
                selectedSprite.dataset.type = sprite.src.includes('/environment/') ? 'background' : 'sprite';
                
                selectionBox.style.display = 'block';
                selectionBox.style.border = '2px dashed #4CAF50';
                selectionBox.style.backgroundColor = 'rgba(76, 175, 80, 0.1)';
                selectionBox.style.pointerEvents = 'none';
                selectionBox.style.position = 'fixed';
                selectionBox.style.zIndex = '1000';
                
                const rect = startCell.getBoundingClientRect();
                const gridContainer = document.getElementById('gridContainer');
                const scale = parseFloat(gridContainer.style.transform.match(/scale\(([^)]+)\)/)?.[1] || 1);
                
                selectionBox.style.left = rect.left + 'px';
                selectionBox.style.top = rect.top + 'px';
                selectionBox.style.width = (rect.width * scale) + 'px';
                selectionBox.style.height = (rect.height * scale) + 'px';
                
                console.log('Виділення ініціалізовано:', {
                    isSelecting,
                    startCell: startCell.dataset,
                    selectedSpriteType: selectedSprite.dataset.type
                });
            } else {
                console.log('Спрайт не вибрано в панелі');
            }
        }
    });

    // Додаємо обробник для відстеження стану клавіші Shift
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Shift') {
            console.log('Клавіша Shift натиснута');
        }
    });

    document.addEventListener('keyup', function(e) {
        if (e.key === 'Shift') {
            console.log('Клавіша Shift відпущена');
            if (isSelecting) {
                isSelecting = false;
                selectionBox.style.display = 'none';
                console.log('Виділення скасовано через відпускання Shift');
            }
        }
    });

    document.getElementById('gridContainer').addEventListener('mousemove', function(e) {
        if (isSelecting && startCell && selectedSprite) {
            console.log('MouseMove під час виділення:', {
                isSelecting,
                hasStartCell: !!startCell,
                hasSelectedSprite: !!selectedSprite
            });

            const currentCell = e.target.closest('.grid-cell');
            if (currentCell) {
                e.preventDefault(); // Запобігаємо стандартній поведінці

                const startRect = startCell.getBoundingClientRect();
                const currentRect = currentCell.getBoundingClientRect();
                const gridContainer = document.getElementById('gridContainer');
                const scale = parseFloat(gridContainer.style.transform.match(/scale\(([^)]+)\)/)?.[1] || 1);
                
                const left = Math.min(startRect.left, currentRect.left);
                const top = Math.min(startRect.top, currentRect.top);
                const width = Math.abs(currentRect.left - startRect.left) + (currentRect.width * scale);
                const height = Math.abs(currentRect.top - startRect.top) + (currentRect.height * scale);
                
                selectionBox.style.left = left + 'px';
                selectionBox.style.top = top + 'px';
                selectionBox.style.width = width + 'px';
                selectionBox.style.height = height + 'px';

                console.log('Оновлення розмірів виділення:', {
                    left,
                    top,
                    width,
                    height,
                    scale
                });
            }
        }
    });

    document.getElementById('gridContainer').addEventListener('mouseup', function(e) {
        if (isSelecting && startCell && selectedSprite) {
            const endCell = e.target.closest('.grid-cell');
            if (endCell) {
                const startX = parseInt(startCell.dataset.x);
                const startY = parseInt(startCell.dataset.y);
                const endX = parseInt(endCell.dataset.x);
                const endY = parseInt(endCell.dataset.y);

                const minX = Math.min(startX, endX);
                const maxX = Math.max(startX, endX);
                const minY = Math.min(startY, endY);
                const maxY = Math.max(startY, endY);

                for (let y = minY; y <= maxY; y++) {
                    for (let x = minX; x <= maxX; x++) {
                        const cell = document.querySelector(`.grid-cell[data-x="${x}"][data-y="${y}"]`);
                        if (cell) {
                            const newSprite = selectedSprite.cloneNode(true);
                            newSprite.style.width = '100%';
                            newSprite.style.height = '100%';
                            newSprite.style.objectFit = 'contain';

                            if (isBackground) {
                                // Видаляємо старий фон, якщо він є
                                const oldBackground = cell.querySelector('.sprite[data-type="background"]');
                                if (oldBackground) {
                                    cell.removeChild(oldBackground);
                                }
                                // Додаємо новий фон перед іншими спрайтами
                                const existingSprite = cell.querySelector('.sprite:not([data-type="background"])');
                                cell.insertBefore(newSprite, existingSprite);
                                cell.dataset.background = 'true';
                            } else {
                                // Видаляємо старий спрайт, якщо він є
                                const oldSprite = cell.querySelector('.sprite:not([data-type="background"])');
                                if (oldSprite) {
                                    cell.removeChild(oldSprite);
                                }
                                // Додаємо новий спрайт
                                cell.appendChild(newSprite);
                            }
                        }
                    }
                }
            }

            // Очищаємо стан виділення
            isSelecting = false;
            startCell = null;
            selectedSprite = null;
            selectionBox.style.display = 'none';
            console.log('Заповнення області завершено');

            if (endCell) {
                const startX = parseInt(startCell.dataset.x);
                const startY = parseInt(startCell.dataset.y);
                const endX = parseInt(endCell.dataset.x);
                const endY = parseInt(endCell.dataset.y);

                const minX = Math.min(startX, endX);
                const maxX = Math.max(startX, endX);
                const minY = Math.min(startY, endY);
                const maxY = Math.max(startY, endY);

                console.log('Координати області:', { minX, maxX, minY, maxY });

                for (let y = minY; y <= maxY; y++) {
                    for (let x = minX; x <= maxX; x++) {
                        const cell = document.querySelector(`.grid-cell[data-x="${x}"][data-y="${y}"]`);
                        if (cell) {
                            const newSprite = selectedSprite.cloneNode(true);
                            const isBackground = newSprite.dataset.type === 'background';

                            if (isBackground) {
                                const existingBackground = cell.querySelector('.sprite[data-type="background"]');
                                if (existingBackground) {
                                    cell.removeChild(existingBackground);
                                }
                                cell.insertBefore(newSprite, cell.firstChild);
                                cell.dataset.background = 'true';
                            } else {
                                const existingSprite = cell.querySelector('.sprite:not([data-type="background"])');
                                if (existingSprite) {
                                    cell.removeChild(existingSprite);
                                }
                                cell.appendChild(newSprite);
                            }
                        }
                    }
                }
            }

            isSelecting = false;
            startCell = null;
            selectedSprite = null;
            selectionBox.style.display = 'none';
            console.log('Заповнення області завершено');

            // Отримуємо координати початкової та кінцевої клітинок
            const startX = parseInt(startCell.dataset.x);
            const startY = parseInt(startCell.dataset.y);
            const endX = parseInt(endCell.dataset.x);
            const endY = parseInt(endCell.dataset.y);
            
            console.log('Координати виділення:', { startX, startY, endX, endY });
            
            // Визначаємо межі виділеної області
            const minX = Math.min(startX, endX);
            const maxX = Math.max(startX, endX);
            const minY = Math.min(startY, endY);
            const maxY = Math.max(startY, endY);
            
            // Проходимо по всім клітинкам у виділеній області
            for (let y = minY; y <= maxY; y++) {
                for (let x = minX; x <= maxX; x++) {
                    const cell = document.querySelector(`.grid-cell[data-x="${x}"][data-y="${y}"]`);
                    if (!cell) continue;
                    
                    const newSprite = selectedSprite.cloneNode(true);
                    newSprite.style.width = '100%';
                    newSprite.style.height = '100%';
                    newSprite.style.objectFit = 'contain';
                    
                    if (newSprite.dataset.type === 'background') {
                        // Видаляємо старий фон, якщо він є
                        const oldBackground = cell.querySelector('.sprite[data-type="background"]');
                        if (oldBackground) {
                            cell.removeChild(oldBackground);
                        }
                        // Додаємо новий фон
                        cell.insertBefore(newSprite, cell.firstChild);
                        cell.dataset.background = 'true';
                    } else {
                        // Видаляємо старий спрайт, якщо він є
                        const oldSprite = cell.querySelector('.sprite:not([data-type="background"])');
                        if (oldSprite) {
                            cell.removeChild(oldSprite);
                        }
                        // Додаємо новий спрайт
                        cell.appendChild(newSprite);
                    }
                }
            }
            
            // Скидаємо стан виділення
            isSelecting = false;
            startCell = null;
            selectedSprite = null;
            selectionBox.style.display = 'none';
            console.log('Заповнення області завершено');
            if (endCell) {
                let startX = parseInt(startCell.dataset.x);
                let startY = parseInt(startCell.dataset.y);
                let endX = parseInt(endCell.dataset.x);
                let endY = parseInt(endCell.dataset.y);
                
                let minX = Math.min(startX, endX);
                let maxX = Math.max(startX, endX);
                let minY = Math.min(startY, endY);
                let maxY = Math.max(startY, endY);
                
                const cells = document.querySelectorAll('.grid-cell');
                cells.forEach(cell => {
                    const x = parseInt(cell.dataset.x);
                    const y = parseInt(cell.dataset.y);
                    
                    if (x >= minX && x <= maxX && y >= minY && y <= maxY) {
                        const newSprite = selectedSprite.cloneNode(true);
                        
                        if (newSprite.dataset.type === 'background') {
                            const existingBackground = cell.querySelector('.sprite[data-type="background"]');
                            if (existingBackground) {
                                cell.removeChild(existingBackground);
                            }
                            cell.insertBefore(newSprite, cell.firstChild);
                            cell.dataset.background = 'true';
                        } else {
                            const existingSprite = cell.querySelector('.sprite:not([data-type="background"])');
                            if (existingSprite) {
                                cell.removeChild(existingSprite);
                            }
                            cell.appendChild(newSprite);
                        }
                    }
                });
                
                isSelecting = false;
                selectionBox.style.display = 'none';
                console.log('Заповнення області завершено');
            }
            
            if (!e.target.closest('.grid-cell')) {
                console.log('Кінцева клітинка не знайдена');
                return;
            }

            // Отримуємо поточний масштаб сітки
            const gridContainer = document.getElementById('gridContainer');
            const scale = parseFloat(gridContainer.style.transform.match(/scale\(([^)]+)\)/)?.[1] || 1);
            
            // Використовуємо вже оголошені змінні
            startX = parseInt(startCell.dataset.x);
            startY = parseInt(startCell.dataset.y);
            endX = parseInt(endCell.dataset.x);
            endY = parseInt(endCell.dataset.y);
            
            console.log('Координати виділення:', { startX, startY, endX, endY, scale });
            
            // Визначаємо межі виділеної області
            minX = Math.min(startX, endX);
            maxX = Math.max(startX, endX);
            minY = Math.min(startY, endY);
            maxY = Math.max(startY, endY);
            
            // Створюємо базовий спрайт для клонування
            const baseSprite = selectedSprite.cloneNode(true);
            baseSprite.style.width = '100%';
            baseSprite.style.height = '100%';
            baseSprite.style.objectFit = 'contain';
            
            // Проходимо по всім клітинкам у виділеній області
            for (let y = minY; y <= maxY; y++) {
                for (let x = minX; x <= maxX; x++) {
                    const cell = document.querySelector(`.grid-cell[data-x="${x}"][data-y="${y}"]`);
                    if (!cell) continue;
                    
                    const newSprite = baseSprite.cloneNode(true);
                    
                    if (newSprite.dataset.type === 'background') {
                        // Видаляємо старий фон, якщо він є
                        const oldBackground = cell.querySelector('.sprite[data-type="background"]');
                        if (oldBackground) {
                            cell.removeChild(oldBackground);
                        }
                        // Додаємо новий фон
                        cell.insertBefore(newSprite, cell.firstChild);
                        cell.dataset.background = 'true';
                    } else {
                        // Видаляємо старий спрайт, якщо він є
                        const oldSprite = cell.querySelector('.sprite:not([data-type="background"])');
                        if (oldSprite) {
                            cell.removeChild(oldSprite);
                        }
                        // Додаємо новий спрайт
                        cell.appendChild(newSprite);
                    }
                }
            }
            
            // Скидаємо стан виділення
            isSelecting = false;
            startCell = null;
            selectedSprite = null;
            selectionBox.style.display = 'none';
        }
    });

    // Обробка вибору елементів на полі

    // Обробка вибору елементів на полі
    document.getElementById('gridContainer').addEventListener('click', function(e) {
        const cell = e.target.closest('.grid-cell');
        if (cell) {
            const selectedContent = document.getElementById('selected-content');
            const hasBackground = cell.dataset.background === 'true';
            const sprite = cell.querySelector('.sprite:not([data-type="background"])');
            const background = cell.querySelector('.sprite[data-type="background"]');
            
            let contentHTML = `<p>Координати: X=${cell.dataset.x}, Y=${cell.dataset.y}</p>`;
            
            if (hasBackground && background) {
                contentHTML += `<p>Фон: ${background.alt}</p>`;
            }
            
            if (sprite) {
                contentHTML += `<p>Об'єкт: ${sprite.alt}</p>`;
            } else if (!hasBackground) {
                contentHTML += '<p>Тип: Пуста клітинка</p>';
            }
            
            selectedContent.innerHTML = contentHTML;
        }
    });
}); // End of DOMContentLoaded event listener

