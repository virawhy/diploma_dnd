// Модуль для роботи з токенами
import { startAttack } from './attacks.js';

export function adjustHP(token, amount) {
    if (!token || !token.dataset) return;
    
    const currentHealth = parseInt(token.dataset.health) || 7;
    const maxHealth = parseInt(token.dataset.maxHealth) || 20;
    const newHealth = Math.max(0, Math.min(maxHealth, currentHealth + amount));
    
    token.dataset.health = newHealth;
    
    const statsPanel = document.querySelector('.token-stats-panel');
    if (statsPanel) {
        const hpValue = statsPanel.querySelector('.hp-value');
        if (hpValue) {
            hpValue.textContent = `${newHealth}/${maxHealth}`;
            
            const healthPercentage = (newHealth / maxHealth) * 100;
            hpValue.style.color = healthPercentage <= 25 ? 'red' : 
                                 healthPercentage <= 50 ? 'yellow' : 
                                 'white';
        }
    }
    
    // Емітуємо подію оновлення здоров'я токена для списку ініціативи
    if (token.alt && token.src) {
        const tokenId = `${token.alt}-${token.src}`;
        document.dispatchEvent(new CustomEvent('token-hp-updated', {
            detail: {
                tokenId: tokenId,
                newHP: newHealth
            }
        }));
    }
}

export function adjustMaxHP(token, amount) {
    if (!token || !token.dataset) return;
    
    const currentHealth = parseInt(token.dataset.health) || 7;
    const currentMaxHealth = parseInt(token.dataset.maxHealth) || 20;
    // Обмежуємо максимальне здоров'я від 1 до 999
    const newMaxHealth = Math.max(1, Math.min(999, currentMaxHealth + amount));
    
    token.dataset.maxHealth = newMaxHealth;
    
    // Якщо поточне здоров'я більше нового максимального, зменшуємо його
    let newHealth = currentHealth;
    if (currentHealth > newMaxHealth) {
        newHealth = newMaxHealth;
        token.dataset.health = newHealth;
    }
    
    const statsPanel = document.querySelector('.token-stats-panel');
    if (statsPanel) {
        const maxHpValue = statsPanel.querySelector('.max-hp-value');
        const hpValue = statsPanel.querySelector('.hp-value');
        
        if (maxHpValue) {
            maxHpValue.textContent = newMaxHealth;
        }
        
        if (hpValue) {
            hpValue.textContent = `${newHealth}/${newMaxHealth}`;
            
            const healthPercentage = (newHealth / newMaxHealth) * 100;
            hpValue.style.color = healthPercentage <= 25 ? 'red' : 
                                 healthPercentage <= 50 ? 'yellow' : 
                                 'white';
        }
    }
    
    // Емітуємо подію оновлення здоров'я токена для списку ініціативи
    if (token.alt && token.src) {
        const tokenId = `${token.alt}-${token.src}`;
        document.dispatchEvent(new CustomEvent('token-hp-updated', {
            detail: {
                tokenId: tokenId,
                newHP: newHealth
            }
        }));
    }
    
    // Емітуємо подію оновлення здоров'я токена для списку ініціативи
    if (token.alt && token.src) {
        const tokenId = `${token.alt}-${token.src}`;
        document.dispatchEvent(new CustomEvent('token-hp-updated', {
            detail: {
                tokenId: tokenId,
                newHP: newHealth
            }
        }));
    }
}

export function adjustAC(token, amount) {
    if (!token || !token.dataset) return;
    
    const currentAC = parseInt(token.dataset.ac) || 12;
    // Обмежуємо клас броні від 1 до 30
    const newAC = Math.max(1, Math.min(30, currentAC + amount));
    
    token.dataset.ac = newAC;
    
    const statsPanel = document.querySelector('.token-stats-panel');
    if (statsPanel) {
        const acValue = statsPanel.querySelector('.ac-value');
        if (acValue) {
            acValue.textContent = newAC;
        }
    }
    
    // Емітуємо подію оновлення токена для списку ініціативи, щоб оновити відображення
    if (token.alt && token.src) {
        const tokenId = `${token.alt}-${token.src}`;
        const currentHealth = parseInt(token.dataset.health) || 7;
        document.dispatchEvent(new CustomEvent('token-hp-updated', {
            detail: {
                tokenId: tokenId,
                newHP: currentHealth
            }
        }));
    }
}

export function adjustSpeed(token, amount) {
    if (!token || !token.dataset) return;
    
    const currentSpeed = parseInt(token.dataset.speed) || 30;
    // Обмежуємо швидкість від 0 до 120
    const newSpeed = Math.max(0, Math.min(120, currentSpeed + amount));
    
    token.dataset.speed = newSpeed;
    
    const statsPanel = document.querySelector('.token-stats-panel');
    if (statsPanel) {
        const speedValue = statsPanel.querySelector('.speed-value');
        if (speedValue) {
            speedValue.textContent = newSpeed;
        }
    }
    
    // Емітуємо подію оновлення токена для списку ініціативи, щоб оновити відображення
    if (token.alt && token.src) {
        const tokenId = `${token.alt}-${token.src}`;
        const currentHealth = parseInt(token.dataset.health) || 7;
        document.dispatchEvent(new CustomEvent('token-hp-updated', {
            detail: {
                tokenId: tokenId,
                newHP: currentHealth
            }
        }));
    }
}

// Функція для видалення токена з поля гри та зі списку ініціативи
export function removeToken(token) {
    if (!token || !token.alt) return;
    
    // Отримуємо ідентифікатор токена
    const tokenId = `${token.alt}-${token.src}`;
    
    // Видаляємо токен з поля гри
    const cell = token.closest('.grid-cell');
    if (cell && token) {
        token.remove();
    }
    
    // Емітуємо подію видалення токена для списку ініціативи
    document.dispatchEvent(new CustomEvent('token-removed', {
        detail: { tokenId }
    }));
    
    // Очищаємо панель інформації про токен
    const tokenInfo = document.querySelector('.token-info');
    const statsPanel = document.querySelector('.token-stats-panel');
    if (tokenInfo && statsPanel) {
        const spritePreview = tokenInfo.querySelector('.sprite-preview');
        const title = tokenInfo.querySelector('.token-name');
        const stats = statsPanel.querySelector('.stats');
        const actionButtons = statsPanel.querySelector('.action-buttons');
        
        spritePreview.innerHTML = '';
        title.textContent = 'Пуста клітинка';
        stats.style.display = 'none';
        actionButtons.style.display = 'none';
    }
}

export function createTokenInfo(token) {
    const tokenInfo = document.querySelector('.token-info');
    const statsPanel = document.querySelector('.token-stats-panel');
    if (!tokenInfo || !statsPanel) return;

    const spritePreview = tokenInfo.querySelector('.sprite-preview');
    spritePreview.innerHTML = '';

    const title = tokenInfo.querySelector('.token-name');
    const stats = statsPanel.querySelector('.stats');
    const actionButtons = statsPanel.querySelector('.action-buttons');
    const hpValue = statsPanel.querySelector('.hp-value');
    const maxHpValue = statsPanel.querySelector('.max-hp-value');
    const acValue = statsPanel.querySelector('.ac-value');
    const speedValue = statsPanel.querySelector('.speed-value');

    if (!token || !token.alt) {
        title.textContent = 'Пуста клітинка';
        stats.style.display = 'none';
        actionButtons.style.display = 'none';
        hpValue.textContent = '-';
        maxHpValue.textContent = '-';
        acValue.textContent = '-';
        speedValue.textContent = '-';
        return;
    }

    // Отримуємо всі спрайти з клітинки
    const cell = token.closest('.grid-cell');
    const sprites = cell ? Array.from(cell.querySelectorAll('.sprite')) : [token];
    const selectedSprite = token;

    // Показуємо превью вибраного спрайту
    const tokenPreview = selectedSprite.cloneNode(true);
    tokenPreview.style.width = '100px';
    tokenPreview.style.height = '100px';
    spritePreview.appendChild(tokenPreview);

    // Показуємо назву вибраного спрайту з обмеженням довжини
    const tokenName = selectedSprite.alt.replace('.png', '');
    title.textContent = tokenName.length > 20 ? tokenName.substring(0, 20) + '...' : tokenName;
    title.title = tokenName; // Додаємо повну назву як підказку

    const isBackground = selectedSprite.src.includes('/environment/');

    // Емітуємо подію додавання нового токену
    if (!isBackground) {
        // Використовуємо комбінацію імені та шляху до спрайту як унікальний ідентифікатор
        const tokenData = {
            id: `${selectedSprite.alt}-${selectedSprite.src}`,
            name: selectedSprite.alt.replace('.png', ''),
            sprite: selectedSprite.src,
            hp: parseInt(selectedSprite.dataset.health) || 7,
            maxHp: parseInt(selectedSprite.dataset.maxHealth) || 20,
            ac: parseInt(selectedSprite.dataset.ac) || 12,
            speed: parseInt(selectedSprite.dataset.speed) || 30
        };
        document.dispatchEvent(new CustomEvent('token-added', { detail: tokenData }));
    }

    if (!isBackground) {
        stats.style.display = 'block';
        actionButtons.style.display = 'block';

        // Перевіряємо, чи вже встановлені значення в dataset, і тільки якщо ні - встановлюємо базові значення
        if (!selectedSprite.dataset.health) selectedSprite.dataset.health = '7';
        if (!selectedSprite.dataset.maxHealth) selectedSprite.dataset.maxHealth = '20';
        if (!selectedSprite.dataset.ac) selectedSprite.dataset.ac = '12';
        if (!selectedSprite.dataset.speed) selectedSprite.dataset.speed = '30';
        
        const currentHealth = parseInt(selectedSprite.dataset.health);
        const maxHealth = parseInt(selectedSprite.dataset.maxHealth);
        const armorClass = parseInt(selectedSprite.dataset.ac);
        const speed = parseInt(selectedSprite.dataset.speed);
        
        hpValue.textContent = `${currentHealth}/${maxHealth}`;
        maxHpValue.textContent = maxHealth;
        acValue.textContent = armorClass;
        speedValue.textContent = speed;
        
        const healthPercentage = (currentHealth / maxHealth) * 100;
        hpValue.style.color = healthPercentage <= 25 ? 'red' : 
                             healthPercentage <= 50 ? 'yellow' : 
                             'white';

        const minusHPBtn = statsPanel.querySelector('.hp-container .minus');
        const plusHPBtn = statsPanel.querySelector('.hp-container .plus');
        const minusMaxHPBtn = statsPanel.querySelector('.max-hp-container .minus');
        const plusMaxHPBtn = statsPanel.querySelector('.max-hp-container .plus');
        const minusACBtn = statsPanel.querySelector('.ac-container .minus');
        const plusACBtn = statsPanel.querySelector('.ac-container .plus');
        const minusSpeedBtn = statsPanel.querySelector('.speed-container .minus');
        const plusSpeedBtn = statsPanel.querySelector('.speed-container .plus');
        const attackBtn = statsPanel.querySelector('.attack-btn');
        const removeTokenBtn = statsPanel.querySelector('.remove-token-btn');

        // Видаляємо старі обробники подій
        minusHPBtn.removeEventListener('click', minusHPBtn.onclick);
        plusHPBtn.removeEventListener('click', plusHPBtn.onclick);
        minusMaxHPBtn.removeEventListener('click', minusMaxHPBtn.onclick);
        plusMaxHPBtn.removeEventListener('click', plusMaxHPBtn.onclick);
        minusACBtn.removeEventListener('click', minusACBtn.onclick);
        plusACBtn.removeEventListener('click', plusACBtn.onclick);
        minusSpeedBtn.removeEventListener('click', minusSpeedBtn.onclick);
        plusSpeedBtn.removeEventListener('click', plusSpeedBtn.onclick);
        attackBtn.removeEventListener('click', attackBtn.onclick);
        if (removeTokenBtn) {
            removeTokenBtn.removeEventListener('click', removeTokenBtn.onclick);
        }

        // Додаємо обробники для кнопок здоров'я
        minusHPBtn.onclick = () => {
            adjustHP(selectedSprite, -1);
            if (tokenPreview.dataset) {
                tokenPreview.dataset.health = selectedSprite.dataset.health;
            }
        };
        plusHPBtn.onclick = () => {
            adjustHP(selectedSprite, 1);
            if (tokenPreview.dataset) {
                tokenPreview.dataset.health = selectedSprite.dataset.health;
            }
        };

        // Додаємо обробники для кнопок максимального здоров'я
        minusMaxHPBtn.onclick = () => {
            adjustMaxHP(selectedSprite, -1);
            if (tokenPreview.dataset) {
                tokenPreview.dataset.maxHealth = selectedSprite.dataset.maxHealth;
            }
        };
        plusMaxHPBtn.onclick = () => {
            adjustMaxHP(selectedSprite, 1);
            if (tokenPreview.dataset) {
                tokenPreview.dataset.maxHealth = selectedSprite.dataset.maxHealth;
            }
        };

        // Додаємо обробники для кнопок класу броні
        minusACBtn.onclick = () => {
            adjustAC(selectedSprite, -1);
            if (tokenPreview.dataset) {
                tokenPreview.dataset.ac = selectedSprite.dataset.ac;
            }
        };
        plusACBtn.onclick = () => {
            adjustAC(selectedSprite, 1);
            if (tokenPreview.dataset) {
                tokenPreview.dataset.ac = selectedSprite.dataset.ac;
            }
        };

        // Додаємо обробники для кнопок швидкості
        minusSpeedBtn.onclick = () => {
            adjustSpeed(selectedSprite, -5);
            if (tokenPreview.dataset) {
                tokenPreview.dataset.speed = selectedSprite.dataset.speed;
            }
        };
        plusSpeedBtn.onclick = () => {
            adjustSpeed(selectedSprite, 5);
            if (tokenPreview.dataset) {
                tokenPreview.dataset.speed = selectedSprite.dataset.speed;
            }
        };

        attackBtn.onclick = () => startAttack(selectedSprite);
        
        // Додаємо обробник для кнопки видалення токена
        if (removeTokenBtn) {
            removeTokenBtn.onclick = () => removeToken(selectedSprite);
        }
    } else {
        stats.style.display = 'none';
        actionButtons.style.display = 'none';
    }
}

export function loadSprites() {
    fetch('/api/grid', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
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
            img.dataset.maxHealth = '20';
            img.dataset.ac = '12';
            img.dataset.speed = '30';

            spriteItem.addEventListener('click', function() {
                document.querySelectorAll('.sprite-item').forEach(item => item.classList.remove('selected'));
                this.classList.add('selected');
            });

            img.addEventListener('click', function(e) {
                createTokenInfo(this);
            });
        });

        const objectsContent = document.getElementById('objects-content');
        data.objects.forEach(obj => {
            const spriteItem = document.createElement('div');
            spriteItem.className = 'sprite-item';
            
            const img = document.createElement('img');
            img.src = `/static/sprites/objects/${obj}`;
            img.alt = obj;
            img.classList.add('sprite');
            img.draggable = true;
            img.dataset.health = '20';
            img.dataset.maxHealth = '20';
            img.dataset.ac = '12';
            img.dataset.speed = '30';
            
            // Прибрано назви об'єктів, залишено лише зображення
            
            spriteItem.appendChild(img);
            objectsContent.appendChild(spriteItem);
        });

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