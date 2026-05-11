// Клас для керування системою ініціативи
export class InitiativeTracker {
    constructor() {
        this.initiativeList = [];
        this.initiativeContainer = document.getElementById('initiative-list');
        this.campaignCharacters = [];
        this.sessionId = this.getSessionIdFromUrl();
        this.campaignId = null;
        this.setupEventListeners();
        this.loadCampaignInfo();
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
        this.initiativeContainer.addEventListener('click', (e) => {
            const listItem = e.target.closest('.initiative-item');
            if (listItem) {
                const tokenId = listItem.dataset.tokenId;
                // Емітуємо подію вибору токена
                const selectEvent = new CustomEvent('token-selected', {
                    detail: { tokenId }
                });
                document.dispatchEvent(selectEvent);
            }
        });
        
        // Додаємо слухач події видалення токена
        document.addEventListener('token-removed', (e) => {
            const { tokenId } = e.detail;
            this.removeToken(tokenId);
        });
        
        // Додаємо слухач події завантаження токена з ініціативи
        document.addEventListener('load-initiative-token', (e) => {
            const tokenData = e.detail;
            // Додаємо токен до списку ініціативи без показу діалогу
            this.addSavedToken(tokenData);
        });
    }
    
    // Завантаження інформації про кампанію
    async loadCampaignInfo() {
        if (!this.sessionId) return;
        
        try {
            // Отримуємо інформацію про GameSession з бази даних
            const sessionInfoResponse = await fetch(`/api/session/${this.sessionId}/info`);
            const sessionInfo = await sessionInfoResponse.json();
            
            if (sessionInfo && sessionInfo.campaign_id) {
                this.campaignId = sessionInfo.campaign_id;
                console.log(`Завантажено інформацію про кампанію: ID=${this.campaignId}`);
                
                // Завантажуємо персонажів кампанії
                await this.loadCampaignCharacters();
                return true;
            } else {
                console.error('Не вдалося отримати ID кампанії для сесії');
                return false;
            }
        } catch (error) {
            console.error('Помилка при завантаженні інформації про кампанію:', error);
            return false;
        }
    }
    
    // Завантаження персонажів кампанії
    async loadCampaignCharacters() {
        if (!this.campaignId) return;
        
        try {
            // Очищаємо масив персонажів перед завантаженням нових
            console.log('Очищення масиву персонажів перед завантаженням');
            this.campaignCharacters = [];
            console.log('Масив персонажів після очищення:', this.campaignCharacters);
            
            // Отримуємо список користувачів кампанії
            const response = await fetch(`/api/campaign/${this.campaignId}/members`);
            const members = await response.json();
            console.log('Отримано членів кампанії:', members);
            
            // Для кожного користувача отримуємо його персонажів
            for (const member of members) {
                console.log(`Отримання персонажів для користувача: ${member.username}`);
                const charactersResponse = await fetch(`/api/campaign/${this.campaignId}/user/${member.username}/characters`);
                const characters = await charactersResponse.json();
                console.log(`Отримано ${characters.length} персонажів для користувача ${member.username}:`, characters);
                
                // Перевіряємо на дублікати перед додаванням
                const existingIds = this.campaignCharacters.map(c => c.id);
                const newCharacters = characters.filter(c => !existingIds.includes(c.id));
                const duplicates = characters.filter(c => existingIds.includes(c.id));
                
                if (duplicates.length > 0) {
                    console.warn(`Знайдено ${duplicates.length} дублікатів персонажів для користувача ${member.username}:`, duplicates);
                }
                
                // Додаємо тільки унікальних персонажів
                this.campaignCharacters = [...this.campaignCharacters, ...newCharacters];
                console.log(`Масив персонажів після додавання для ${member.username}:`, this.campaignCharacters);
            }
            
            console.log(`Завантажено ${this.campaignCharacters.length} унікальних персонажів кампанії`);
        } catch (error) {
            console.error('Помилка при завантаженні персонажів кампанії:', error);
        }
    }

    // Показ діалогового вікна для кидка ініціативи
    async showInitiativeDialog(tokenData) {
        // Переконуємося, що інформація про кампанію завантажена
        if (!this.campaignId) {
            await this.loadCampaignInfo();
        }
        
        // Якщо персонажі не завантажені, спробуємо завантажити їх
        if (!this.campaignCharacters || this.campaignCharacters.length === 0) {
            if (this.campaignId) {
                await this.loadCampaignCharacters();
            }
        }
        
        return new Promise((resolve) => {
            const dialog = document.createElement('div');
            dialog.className = 'modal initiative-dialog';
            
            // Створюємо HTML для селектора персонажів
            console.log('Початок створення HTML для селектора персонажів');
            console.log('Поточний масив персонажів:', this.campaignCharacters);
            
            // Перевіряємо на дублікати за ID
            const uniqueIds = new Set();
            const duplicateIds = new Set();
            this.campaignCharacters.forEach(character => {
                if (uniqueIds.has(character.id)) {
                    duplicateIds.add(character.id);
                } else {
                    uniqueIds.add(character.id);
                }
            });
            
            if (duplicateIds.size > 0) {
                console.warn('Знайдено дублікати персонажів за ID:', Array.from(duplicateIds));
                console.warn('Дублікати персонажів:', this.campaignCharacters.filter(c => duplicateIds.has(c.id)));
            }
            
            // Перевіряємо на дублікати за іменем
            const nameMap = new Map();
            this.campaignCharacters.forEach(character => {
                const key = `${character.name}-${character.class}-${character.level}`;
                if (nameMap.has(key)) {
                    console.warn(`Знайдено дублікат за іменем: ${character.name} (${character.class}, Рівень ${character.level})`);
                    console.warn('Оригінал:', nameMap.get(key));
                    console.warn('Дублікат:', character);
                } else {
                    nameMap.set(key, character);
                }
            });
            
            let charactersOptionsHTML = '<option value="">Виберіть персонажа (опціонально)</option>';
            if (this.campaignCharacters && this.campaignCharacters.length > 0) {
                // Створюємо масив для відстеження доданих опцій
                const addedOptions = new Set();
                
                this.campaignCharacters.forEach(character => {
                    const optionKey = `${character.id}-${character.name}`;
                    if (!addedOptions.has(optionKey)) {
                        charactersOptionsHTML += `<option value="${character.id}">${character.name} (${character.class}, Рівень ${character.level})</option>`;
                        addedOptions.add(optionKey);
                        console.log(`Додано опцію: ${character.name} (${character.class}, Рівень ${character.level}) з ID ${character.id}`);
                    } else {
                        console.warn(`Пропущено дублікат опції: ${character.name} (${character.class}, Рівень ${character.level}) з ID ${character.id}`);
                    }
                });
                
                console.log(`Додано ${addedOptions.size} унікальних персонажів до селектора з ${this.campaignCharacters.length} загальних`);
            } else {
                console.log('Немає доступних персонажів для вибору');
            }
            
            console.log('Фінальний HTML селектора:', charactersOptionsHTML);
            
            dialog.innerHTML = `
                <div class="modal-content">
                    <span class="close-button">&times;</span>
                    <h2>Кидок ініціативи</h2>
                    <div class="token-preview" style="text-align: center; margin-bottom: 15px;">
                        <img src="${tokenData.sprite}" alt="${tokenData.name}" style="width: 60px; height: 60px; border-radius: 50%; border: 2px solid #cc0000; box-shadow: 0 0 10px rgba(204, 0, 0, 0.5);">
                        <h3 style="margin: 10px 0 0; color: #ecf0f1;">${tokenData.name}</h3>
                    </div>
                    <div class="initiative-roll-container">
                        <div style="display: flex; flex-direction: column; align-items: center; text-align: center; margin-bottom: 15px;">
                            <label for="characterSelect" style="margin-bottom: 10px; color: #aaa;">Персонаж:</label>
                            <select id="characterSelect" style="width: 100%; padding: 8px; background-color: #333; color: #ecf0f1; border: 1px solid #555; border-radius: 4px;">
                                ${charactersOptionsHTML}
                            </select>
                        </div>
                        <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
                            <label for="initiativeBonus" style="margin-bottom: 10px; color: #aaa;">Бонус ініціативи:</label>
                            <input type="number" id="initiativeBonus" placeholder="0" value="0">
                        </div>
                        <div id="roll-result" style="display: none; text-align: center; margin: 15px 0; padding: 15px; background-color: #2c2c2c; border-radius: 6px;">
                            <div class="dice-result" style="font-size: 24px; font-weight: bold; color: #ecf0f1; margin-bottom: 10px;"></div>
                            <div class="total-result" style="font-size: 28px; font-weight: bold; color: #cc0000;"></div>
                        </div>
                        <button id="rollInitiative">Кинути d20</button>
                    </div>
                </div>
            `;
            document.body.appendChild(dialog);

            const rollButton = dialog.querySelector('#rollInitiative');
            const closeButton = dialog.querySelector('.close-button');
            const rollResult = dialog.querySelector('#roll-result');
            const diceResult = dialog.querySelector('.dice-result');
            const totalResult = dialog.querySelector('.total-result');
            const characterSelect = dialog.querySelector('#characterSelect');
            const initiativeBonusInput = dialog.querySelector('#initiativeBonus');
            
            // Додаємо обробник події зміни вибраного персонажа
            characterSelect.addEventListener('change', () => {
                const selectedCharacterId = parseInt(characterSelect.value);
                if (selectedCharacterId) {
                    const selectedCharacter = this.campaignCharacters.find(c => c.id === selectedCharacterId);
                    if (selectedCharacter) {
                        // Розраховуємо бонус ініціативи на основі модифікатора спритності
                        const dexterityModifier = Math.floor((selectedCharacter.dexterity - 10) / 2);
                        initiativeBonusInput.value = selectedCharacter.initiative || dexterityModifier;
                        
                        // Оновлюємо ім'я токена, якщо воно не було встановлено
                        if (tokenData.name === 'Токен') {
                            const tokenPreviewName = dialog.querySelector('.token-preview h3');
                            if (tokenPreviewName) {
                                tokenPreviewName.textContent = selectedCharacter.name;
                                tokenData.name = selectedCharacter.name;
                            }
                        }
                    }
                }
            });

            const closeDialog = () => {
                dialog.remove();
                resolve(null);
            };

            const animateDiceRoll = (finalRoll, bonus) => {
                rollButton.disabled = true;
                rollButton.textContent = 'Кидаємо кубик...';
                rollResult.style.display = 'block';
                
                let count = 0;
                const maxCount = 20;
                const interval = setInterval(() => {
                    const randomRoll = Math.floor(Math.random() * 20) + 1;
                    diceResult.textContent = `Кубик: ${randomRoll}`;
                    count++;
                    
                    if (count >= maxCount) {
                        clearInterval(interval);
                        diceResult.textContent = `Кубик: ${finalRoll}`;
                        totalResult.textContent = `Результат: ${finalRoll + bonus}`;
                        
                        rollButton.textContent = 'Підтвердити';
                        rollButton.disabled = false;
                        
                        // Змінюємо обробник для кнопки підтвердження
                        rollButton.removeEventListener('click', rollDice);
                        rollButton.addEventListener('click', () => {
                            // Зберігаємо інформацію про вибраного персонажа
                            const selectedCharacterId = parseInt(characterSelect.value);
                            let characterInfo = null;
                            
                            if (selectedCharacterId) {
                                const selectedCharacter = this.campaignCharacters.find(c => c.id === selectedCharacterId);
                                if (selectedCharacter) {
                                    characterInfo = {
                                        id: selectedCharacter.id,
                                        name: selectedCharacter.name,
                                        class: selectedCharacter.class,
                                        level: selectedCharacter.level,
                                        hp: selectedCharacter.health_current || selectedCharacter.health_max || tokenData.hp || 0,
                                        maxHp: selectedCharacter.health_max || 0
                                    };
                                }
                            }
                            
                            dialog.remove();
                            resolve({
                                initiative: finalRoll + bonus,
                                character: characterInfo
                            });
                        });
                    }
                }, 50);
            };

            const rollDice = () => {
                const bonus = parseInt(dialog.querySelector('#initiativeBonus').value) || 0;
                const roll = Math.floor(Math.random() * 20) + 1;
                animateDiceRoll(roll, bonus);
            };

            rollButton.addEventListener('click', rollDice);
            closeButton.addEventListener('click', closeDialog);

            dialog.addEventListener('click', (e) => {
                if (e.target === dialog) {
                    closeDialog();
                }
            });

            dialog.style.display = 'block';
        });
    }

    // Додавання нового токена до списку ініціативи
    async addToken(tokenData) {
        // Перевіряємо, чи токен вже є в списку
        const existingToken = this.initiativeList.find(t => t.id === tokenData.id);
        console.log(this.initiativeList);
        console.log(tokenData.id);
        console.log(existingToken);

        if (existingToken) return; // Якщо токен вже є, виходимо
        
        // Перевіряємо, чи токен є об'єктом (за шляхом до спрайту)
        if (tokenData.sprite.includes('/objects/')) {
            console.log('Об\'єкти не можуть бути додані до списку ініціативи');
            return; // Якщо це об'єкт, виходимо
        }

        const result = await this.showInitiativeDialog(tokenData);
        if (result === null) return; // Якщо діалог було закрито

        // Отримуємо значення ініціативи та інформацію про персонажа
        const initiativeRoll = typeof result === 'object' ? result.initiative : result;
        const characterInfo = typeof result === 'object' ? result.character : null;

        // Створюємо об'єкт з інформацією про токен
        const tokenInfo = {
            id: tokenData.id,
            name: tokenData.name,
            sprite: tokenData.sprite,
            initiative: initiativeRoll,
            hp: characterInfo ? characterInfo.hp : (tokenData.hp || 0),
            maxHp: characterInfo ? characterInfo.maxHp : (tokenData.maxHp || 0),
            ac: characterInfo && characterInfo.ac ? characterInfo.ac : (tokenData.ac || 0)
        };

        // Якщо є інформація про персонажа, додаємо її до елемента ініціативи
        if (characterInfo) {
            tokenInfo.characterId = characterInfo.id;
            tokenInfo.characterClass = characterInfo.class;
            tokenInfo.characterLevel = characterInfo.level;
            
            // Оновлюємо характеристики токену на ігровому полі
            this.updateTokenOnGrid(tokenData.id, characterInfo);
        }
        
        this.addTokenToList(tokenInfo);
    }
    
    // Додавання збереженого токена до списку ініціативи без діалогу
    addSavedToken(tokenData) {
        // Перевіряємо, чи токен вже є в списку
        const existingToken = this.initiativeList.find(t => t.id === tokenData.id);
        if (existingToken) return; // Якщо токен вже є, виходимо
        
        console.log('Додавання збереженого токена:', tokenData);
        console.log('Доступні персонажі:', this.campaignCharacters);
        
        // Перевіряємо, чи є у нас інформація про персонажа для цього токена
        if (tokenData.characterId && this.campaignCharacters && this.campaignCharacters.length > 0) {
            const character = this.campaignCharacters.find(c => c.id === tokenData.characterId);
            if (character) {
                console.log('Знайдено персонажа для токена:', character);
                // Оновлюємо інформацію про персонажа
                tokenData.characterClass = character.class;
                tokenData.characterLevel = character.level;
                tokenData.hp = character.health_current || character.health_max || tokenData.hp;
                tokenData.maxHp = character.health_max || tokenData.maxHp;
                
                // Створюємо об'єкт з інформацією про персонажа для оновлення токену на ігровому полі
                const characterInfo = {
                    id: character.id,
                    name: character.name,
                    class: character.class,
                    level: character.level,
                    hp: character.health_current || character.health_max || tokenData.hp,
                    maxHp: character.health_max || tokenData.maxHp,
                    ac: character.armor_class || tokenData.ac
                };
                
                // Оновлюємо характеристики токену на ігровому полі
                this.updateTokenOnGrid(tokenData.id, characterInfo);
            } else {
                console.log('Персонаж не знайдений для ID:', tokenData.characterId);
            }
        } else if (!this.campaignCharacters || this.campaignCharacters.length === 0) {
            console.log('Список персонажів порожній або не завантажений');
        }
        
        this.addTokenToList(tokenData);
    }
    
    // Додавання токена до списку ініціативи (спільний код для addToken і addSavedToken)
    addTokenToList(tokenInfo) {

        this.initiativeList.push(tokenInfo);
        this.sortInitiativeList();
        this.updateInitiativeDisplay();
    }

    // Сортування списку за значенням ініціативи
    sortInitiativeList() {
        this.initiativeList.sort((a, b) => b.initiative - a.initiative);
    }

    // Оновлення відображення списку ініціативи
    updateInitiativeDisplay() {
        this.initiativeContainer.innerHTML = '';
        
        this.initiativeList.forEach(token => {
            const listItem = document.createElement('div');
            listItem.className = 'initiative-item';
            listItem.dataset.tokenId = token.id;

            const truncatedName = token.name.length > 15 
                ? token.name.substring(0, 12) + '...' 
                : token.name;

            // Додаємо інформацію про клас і рівень персонажа, якщо вона доступна
            let characterInfo = '';
            if (token.characterClass && token.characterLevel) {
                characterInfo = `<span class="initiative-character-info" title="${token.characterClass}, Рівень ${token.characterLevel}">${token.characterClass} ${token.characterLevel}</span>`;
            }

            // Відображаємо тільки поточне здоров'я без максимального
            const hpDisplay = `HP: ${token.hp}`;
            
            // Додаємо інформацію про клас броні, якщо вона доступна
            const acDisplay = token.ac ? `AC: ${token.ac}` : '';

            listItem.innerHTML = `
                <div class="initiative-sprite">
                    <img src="${token.sprite}" alt="${token.name}">
                </div>
                <div class="initiative-info">
                    <span class="initiative-name" title="${token.name}">${truncatedName}</span>
                    ${characterInfo}
                    <span class="initiative-stats">
                        <span class="initiative-hp">${hpDisplay}</span>
                        ${acDisplay ? `<span class="initiative-ac">${acDisplay}</span>` : ''}
                        <span class="initiative-value">Ініціатива: ${token.initiative}</span>
                    </span>
                </div>
            `;

            this.initiativeContainer.appendChild(listItem);
        });
    }

    // Оновлення HP токена
    updateTokenHP(tokenId, newHP) {
        const token = this.initiativeList.find(t => t.id === tokenId);
        if (token) {
            token.hp = newHP;
            this.updateInitiativeDisplay();
        }
    }
    
    // Оновлення характеристик токену на ігровому полі
    updateTokenOnGrid(tokenId, characterInfo) {
        console.log('Оновлення характеристик токену на ігровому полі:', tokenId, characterInfo);
        
        // Знаходимо всі спрайти на ігровому полі
        const sprites = document.querySelectorAll('.sprite');
        
        // Шукаємо спрайт з відповідним ID
        for (const sprite of sprites) {
            const spriteId = `${sprite.alt}-${sprite.src}`;
            
            if (spriteId === tokenId) {
                console.log('Знайдено токен на ігровому полі:', sprite);
                
                // Оновлюємо характеристики токену
                sprite.dataset.health = characterInfo.hp || sprite.dataset.health;
                sprite.dataset.maxHealth = characterInfo.maxHp || sprite.dataset.maxHealth;
                sprite.dataset.ac = characterInfo.ac || sprite.dataset.ac;
                
                // Якщо є інформація про швидкість, оновлюємо її
                if (characterInfo.speed) {
                    sprite.dataset.speed = characterInfo.speed;
                }
                
                // Оновлюємо назву токену, якщо вона не була встановлена
                if (sprite.alt === 'Токен' && characterInfo.name) {
                    sprite.alt = characterInfo.name;
                }
                
                // Оновлюємо панель статистики, якщо вона відкрита для цього токену
                const statsPanel = document.querySelector('.token-stats-panel');
                if (statsPanel && statsPanel.style.display === 'block') {
                    const selectedSprite = document.querySelector('.selected-sprite');
                    if (selectedSprite && selectedSprite.src === sprite.src) {
                        const hpValue = statsPanel.querySelector('.hp-value');
                        const maxHpValue = statsPanel.querySelector('.max-hp-value');
                        const acValue = statsPanel.querySelector('.ac-value');
                        
                        if (hpValue) hpValue.textContent = `${characterInfo.hp}/${characterInfo.maxHp}`;
                        if (maxHpValue) maxHpValue.textContent = characterInfo.maxHp;
                        if (acValue) acValue.textContent = characterInfo.ac;
                    }
                }
                
                break;
            }
        }
    }

    // Видалення токена зі списку ініціативи
    removeToken(tokenId) {
        this.initiativeList = this.initiativeList.filter(t => t.id !== tokenId);
        this.updateInitiativeDisplay();
    }
}