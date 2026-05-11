document.addEventListener('DOMContentLoaded', function() {
    // Змінні для зберігання поточного стану
    let currentTab = localStorage.getItem('campaignActiveTab') || 'npcs';
    
    // Перевіряємо, чи існують елементи перед додаванням класів
    const tabButton = document.querySelector(`[data-tab="${currentTab}"]`);
    const tabContent = document.getElementById(currentTab);
    
    if (tabButton && tabContent) {
        // Встановлюємо активну вкладку при завантаженні
        tabButton.classList.add('active');
        tabContent.classList.add('active');
        
        // Видаляємо клас active з інших вкладок
        document.querySelectorAll('.tab-content').forEach(tab => {
            if (tab.id !== currentTab) {
                tab.classList.remove('active');
            }
        });
        document.querySelectorAll('.tab-button').forEach(button => {
            if (button.getAttribute('data-tab') !== currentTab) {
                button.classList.remove('active');
            }
        });
    } else {
        console.error(`Не знайдено елементи для вкладки ${currentTab}`);
        // Встановлюємо першу вкладку як активну, якщо поточна не знайдена
        const firstTabButton = document.querySelector('.tab-button');
        if (firstTabButton) {
            const firstTabId = firstTabButton.getAttribute('data-tab');
            firstTabButton.classList.add('active');
            const firstTabContent = document.getElementById(firstTabId);
            if (firstTabContent) {
                firstTabContent.classList.add('active');
                currentTab = firstTabId;
                localStorage.setItem('campaignActiveTab', currentTab);
            }
        }
    }
    
    // Ініціалізація пошуку
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    
    // Функція для виконання пошуку
    function performSearch() {
        const searchText = searchInput.value.toLowerCase();
        if (searchText.trim() === '') {
            // Якщо пошуковий запит порожній, показуємо всі елементи
            document.querySelectorAll('.entry-item').forEach(item => {
                item.classList.remove('hidden');
            });
            
            // Видаляємо підсвічування
            document.querySelectorAll('.highlight').forEach(el => {
                const parent = el.parentNode;
                parent.innerHTML = parent.innerHTML.replace(/<mark class="highlight">(.*?)<\/mark>/g, '$1');
            });
            return;
        }
        
        // Шукаємо по всіх елементах у всіх вкладках
        document.querySelectorAll('.entry-item').forEach(item => {
            const title = item.querySelector('h3').textContent.toLowerCase();
            const description = item.querySelector('p').textContent.toLowerCase();
            const date = item.querySelector('small')?.textContent.toLowerCase() || '';
            
            const content = title + ' ' + description + ' ' + date;
            
            if (content.includes(searchText)) {
                item.classList.remove('hidden');
                
                // Підсвічуємо знайдений текст
                highlightText(item.querySelector('h3'), searchText);
                highlightText(item.querySelector('p'), searchText);
                if (item.querySelector('small')) {
                    highlightText(item.querySelector('small'), searchText);
                }
            } else {
                item.classList.add('hidden');
            }
        });
        
        // Перевіряємо, чи є видимі елементи у поточній вкладці
        const activeTab = document.querySelector('.tab-content.active');
        const visibleItems = activeTab.querySelectorAll('.entry-item:not(.hidden)');
        
        if (visibleItems.length === 0) {
            // Якщо немає видимих елементів, показуємо повідомлення
            let noResultsMsg = activeTab.querySelector('.no-results-message');
            if (!noResultsMsg) {
                noResultsMsg = document.createElement('div');
                noResultsMsg.className = 'no-results-message';
                noResultsMsg.textContent = 'Нічого не знайдено за вашим запитом';
                noResultsMsg.style.textAlign = 'center';
                noResultsMsg.style.padding = '2rem';
                noResultsMsg.style.color = 'var(--text-gray)';
                activeTab.appendChild(noResultsMsg);
            }
        } else {
            // Видаляємо повідомлення, якщо воно є
            const noResultsMsg = activeTab.querySelector('.no-results-message');
            if (noResultsMsg) {
                noResultsMsg.remove();
            }
        }
    }
    
    // Функція для підсвічування тексту
    function highlightText(element, searchText) {
        if (!element) return;
        
        const text = element.innerHTML;
        const regex = new RegExp(searchText, 'gi');
        const highlightedText = text.replace(regex, match => `<mark class="highlight">${match}</mark>`);
        element.innerHTML = highlightedText;
    }
    
    // Обробник події для кнопки пошуку
    searchButton.addEventListener('click', performSearch);
    
    // Обробник події для поля введення (пошук при натисканні Enter)
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    
    // Функція для очищення підсвічування
    function clearHighlights() {
        document.querySelectorAll('.highlight').forEach(el => {
            const parent = el.parentNode;
            parent.innerHTML = parent.innerHTML.replace(/<mark class="highlight">(.*?)<\/mark>/g, '$1');
        });
    }
    
    // Обробка кліків по вкладках
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // Зберігаємо активну вкладку в localStorage
            localStorage.setItem('campaignActiveTab', tabId);
            currentTab = tabId;
            
            // Видаляємо клас active з усіх вкладок
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Додаємо клас active до вибраної вкладки
            this.classList.add('active');
            const activeTabContent = document.getElementById(tabId);
            if (activeTabContent) {
                activeTabContent.classList.add('active');
            } else {
                console.error(`Не знайдено вміст вкладки з id ${tabId}`);
            }
            
            // Видаляємо підсвічування
            clearHighlights();
            
            // Якщо є текст у полі пошуку, виконуємо пошук для нової вкладки
            if (searchInput.value.trim() !== '') {
                setTimeout(performSearch, 100); // Невелика затримка для завершення перемикання вкладок
            }
        });
    });
    let currentDeleteId = null;
    let currentEditId = null;
    let currentEditType = null;
    let selectedCharacterId = null;

    // Модальні вікна
    const addCharacterModal = document.getElementById('add-character-modal');
    const confirmModal = document.getElementById('confirm-modal');
    const closeButtons = document.getElementsByClassName('close');

    // Кнопки та елементи форми
    const addCharacterBtn = document.getElementById('add-character-btn');
    const findUserBtn = document.getElementById('find-user-btn');
    const addSelectedCharacterBtn = document.getElementById('add-selected-character-btn');
    const usernameInput = document.getElementById('username-input');
    const characterList = document.getElementById('character-list');
    const userSelectStep = document.getElementById('user-select-step');
    const characterSelectStep = document.getElementById('character-select-step');

    // Відкриття модального вікна для додавання персонажа
    if (addCharacterBtn) {
        addCharacterBtn.onclick = function() {
            addCharacterModal.style.display = 'block';
            userSelectStep.style.display = 'block';
            characterSelectStep.style.display = 'none';
            usernameInput.value = '';
            characterList.innerHTML = '';
        }
    }

    // Закриття модальних вікон
    Array.from(closeButtons).forEach(button => {
        button.onclick = function() {
            addCharacterModal.style.display = 'none';
            confirmModal.style.display = 'none';
            // Закриваємо також модальне вікно редагування
            const editModal = document.getElementById('edit-modal');
            if (editModal) {
                editModal.style.display = 'none';
            }
            // Закриваємо всі модальні вікна з класом .modal, які є батьківськими для цього хрестика
            const modalParent = button.closest('.modal');
            if (modalParent) {
                modalParent.style.display = 'none';
            }
        }
    });

    // Пошук користувача та його персонажів
    // Додамо список доступних рас та класів
    const availableRaces = {
        "Human": "Людина",
        "Elf": "Ельф",
        "Dwarf": "Дворф",
        "Half-Elf": "Напівельф",
        "Half-Orc": "Напіворк",
        "Gnome": "Гном",
        "Tiefling": "Тифлінг",
        "Dragonborn": "Драконороджений",
        "Halfling": "Напіврослик"
    };
    
    const availableClasses = {
        "Barbarian": "Варвар",
        "Bard": "Бард",
        "Cleric": "Жрець",
        "Druid": "Друїд",
        "Fighter": "Воїн",
        "Monk": "Монах",
        "Paladin": "Паладин",
        "Ranger": "Рейнджер",
        "Rogue": "Розбійник",
        "Sorcerer": "Чародій",
        "Warlock": "Чорнокнижник",
        "Wizard": "Чарівник"
    };
    
    // Модифікуємо функцію пошуку користувача з обробкою помилок
    if (findUserBtn) {
        findUserBtn.onclick = async function() {
            const username = usernameInput.value;
            try {
                const response = await fetch(`/api/campaign/${campaignId}/user/${username}/characters`);
            const characters = await response.json();
            
            console.log('Отримані дані персонажів:', characters);
            
            if (response.ok) {
                characterList.innerHTML = characters.map(char => {
                    console.log('Обробка персонажа:', char);
                    
                    // Отримуємо значення з правильних полів
                    const raceName = char.race || 'Невідомо';
                    const className = char.class || 'Невідомо';
                    
                    const charLevel = char.level;
                    console.log(`
                        <div class="character-option" data-id="${char.id}">
                            <h4>${char.name || 'Безіменний'}</h4>
                            <p>${raceName} - ${className} (Рівень ${charLevel})</p>
                        </div>
                    `)
                    return `
                        <div class="character-option" data-id="${char.id}">
                            <h4>${char.name || 'Безіменний'}</h4>
                            <p>${raceName} - ${className} (Рівень ${charLevel})</p>
                        </div>
                    `;
                }).join('');
    
                userSelectStep.style.display = 'none';
                characterSelectStep.style.display = 'block';
    
                // Додаємо обробники для вибору персонажа
                document.querySelectorAll('.character-option').forEach(option => {
                    option.onclick = function() {
                        document.querySelectorAll('.character-option').forEach(opt => 
                            opt.classList.remove('selected'));
                        this.classList.add('selected');
                        selectedCharacterId = this.getAttribute('data-id');
                        console.log('Вибрано персонажа з ID:', selectedCharacterId);
                        
                        // Додаємо перевірку чи ID встановлено коректно
                        if (!selectedCharacterId) {
                            console.error('ID персонажа не встановлено');
                            return;
                        }
                        
                        // Зберігаємо ID в data-атрибуті кнопки підтвердження
                        addSelectedCharacterBtn.setAttribute('data-selected-id', selectedCharacterId);
                    }
                });
            } else {
                alert('Користувача не знайдено');
            }
        } catch (error) {
            console.error('Детальна помилка при пошуку користувача:', error);
            alert('Помилка при пошуку користувача. Перевірте консоль для деталей.');
        }
    }
    }

    // Додавання вибраного персонажа до кампанії
    addSelectedCharacterBtn.onclick = async function() {
        const characterId = this.getAttribute('data-selected-id');
        
        if (!characterId) {
            console.log('Спроба додати персонажа без вибраного ID');
            alert('Будь ласка, виберіть персонажа');
            return;
        }

        try {
            console.log('Спроба додати персонажа до кампанії:', {
                characterId,
                campaignId,
                endpoint: `/api/campaign/${campaignId}/character/${characterId}`
            });

            const response = await fetch(`/api/campaign/${campaignId}/character/${characterId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
                },
                credentials: 'include', // Додаємо передачу кукі
                body: JSON.stringify({ character_id: characterId })
            });

            console.log('Відповідь від сервера:', {
                status: response.status,
                statusText: response.statusText,
                ok: response.ok
            });

            if (response.ok) {
                console.log('Персонаж успішно доданий до кампанії');
                location.reload();
            } else {
                const errorData = await response.json().catch(e => {
                    console.error('Помилка при парсингу відповіді:', e);
                    return {};
                });
                console.error('Детальна відповідь сервера:', errorData);
                
                // Додаємо специфічні повідомлення про помилки
                if (response.status === 403) {
                    throw new Error('У вас немає прав для додавання персонажа до цієї кампанії');
                }
                throw new Error(errorData.message || 'Помилка при додаванні персонажа до кампанії');
            }
        } catch (error) {
            console.error('Повна інформація про помилку:', {
                message: error.message,
                stack: error.stack,
                characterId,
                campaignId
            });
            alert(`Помилка при додаванні персонажа: ${error.message}`);
        }
    }

    // Обробник для кнопок видалення
    function addDeleteHandler(button, type) {
        button.onclick = function() {
            const item = this.closest('.entry-item');
            currentDeleteId = item.dataset.id;
            currentEditType = type;
            confirmModal.style.display = 'block';
        }
    }

    // Обробник для кнопок редагування
    function addEditHandler(button, type) {
        button.onclick = function() {
            const item = this.closest('.entry-item');
            currentEditId = item.dataset.id;
            currentEditType = type;
            const editModal = document.getElementById('edit-modal');
            const form = document.getElementById('edit-form');

            form.elements['name'].value = item.querySelector('h3').textContent;
            form.elements['description'].value = item.querySelector('p').textContent;

            if (type === 'event' || type === 'events') {
                const dateElement = item.querySelector('small');
                if (dateElement) {
                    form.elements['date'].style.display = 'block';
                    form.elements['date'].value = dateElement.textContent.replace('Дата: ', '');
                }
            } else {
                form.elements['date'].style.display = 'none';
            }

            editModal.style.display = 'block';
        }
    }

    // Додаємо обробники для існуючих кнопок видалення та редагування
    document.querySelectorAll('.delete-character-btn').forEach(btn => addDeleteHandler(btn, 'character'));
    document.querySelectorAll('.delete-npc-btn').forEach(btn => addDeleteHandler(btn, 'npc'));
    document.querySelectorAll('.delete-btn').forEach(btn => {
        const type = btn.closest('.tab-content').id;
        addDeleteHandler(btn, type);
    });

    document.querySelectorAll('.edit-btn').forEach(btn => {
        const type = btn.closest('.tab-content').id;
        addEditHandler(btn, type);
    });

    // Обробка підтвердження видалення
    document.getElementById('confirm-yes').onclick = async function() {
        try {
            let endpoint = '';
            let itemType = '';
            
            switch(currentEditType) {
                case 'character':
                    endpoint = `/api/campaign/${campaignId}/character/${currentDeleteId}`;
                    itemType = 'персонажа';
                    break;
                case 'npc':
                    endpoint = `/api/npc/${currentDeleteId}`;
                    itemType = 'NPC';
                    break;
                case 'event':
                case 'events':
                    endpoint = `/api/event/${currentDeleteId}`;
                    itemType = 'подію';
                    break;
                case 'location':
                case 'locations':
                    endpoint = `/api/location/${currentDeleteId}`;
                    itemType = 'локацію';
                    break;
                default:
                    console.error('Невідомий тип запису для видалення');
                    return;
            }

            console.log('Спроба видалення запису:', {
                campaignId,
                itemId: currentDeleteId,
                type: currentEditType,
                endpoint: endpoint
            });

            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
            console.log('CSRF токен:', csrfToken);

            const response = await fetch(endpoint, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': csrfToken,
                    'Accept': 'application/json'
                },
                credentials: 'same-origin'
            });

            console.log('Відповідь від сервера:', {
                status: response.status,
                statusText: response.statusText,
                headers: Object.fromEntries(response.headers.entries())
            });

            if (response.ok) {
                location.reload();
                confirmModal.style.display = 'none';
            } else {
                const errorData = await response.json().catch(e => {
                    console.error('Помилка при парсингу відповіді:', e);
                    return { message: 'Невідома помилка' };
                });
                
                console.error('Детальна відповідь сервера:', errorData);
                
                if (response.status === 405) {
                    alert('Помилка: Метод видалення не дозволений на сервері. Зверніться до адміністратора.');
                } else {
                    alert(`Помилка при видаленні ${itemType}: ${errorData.message || 'Невідома помилка'}`);
                }
            }
        } catch (error) {
            console.error('Помилка при видаленні:', error);
            alert(`Помилка при видаленні ${currentEditType}`);
        }
    }

    document.getElementById('confirm-no').onclick = function() {
        confirmModal.style.display = 'none';
    }

    // Обробка форми редагування
    const editForm = document.getElementById('edit-form');
    if (editForm) {
        editForm.onsubmit = async function(e) {
            e.preventDefault();
            const formData = new FormData(editForm);
            const data = {};
            formData.forEach((value, key) => data[key] = value);

            let endpoint = '';
            switch(currentEditType) {
                case 'event':
                case 'events':
                    endpoint = `/api/event/${currentEditId}`;
                    try {
                        data.date = formatDate(data.date);
                    } catch (error) {
                        alert(error.message);
                        return;
                    }
                    break;
                case 'location':
                case 'locations':
                    endpoint = `/api/location/${currentEditId}`;
                    break;
                default:
                    console.error('Невідомий тип запису для редагування');
                    return;
            }

            try {
                const response = await fetch(endpoint, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
                    },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    location.reload();
                } else {
                    const errorData = await response.json();
                    throw new Error(errorData.message || 'Помилка при оновленні запису');
                }
            } catch (error) {
                console.error('Помилка при оновленні:', error);
                alert(`Помилка при оновленні: ${error.message}`);
            }
        }
    }
    
    // Функція для перетворення назви вкладки в тип API-ендпоінту
    function getApiType(tabName) {
        if (tabName === 'events') return 'event';
        if (tabName === 'locations') return 'location';
        return 'npc'; // За замовчуванням
    }

    // Обробка перемикання вкладок
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => {
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });

            const tabId = button.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
            button.classList.add('active');
            currentTab = tabId;
            
            // Зберігаємо активну вкладку в localStorage
            localStorage.setItem('campaignActiveTab', tabId);
            
            // Очищаємо виділення пошуку при зміні вкладки
            if (typeof clearHighlights === 'function') {
                clearHighlights();
            }
        });
    });


    // Обробка форм створення
    const forms = {
        'npc-form': '/api/campaign/' + campaignId + '/npc',
        'event-form': '/api/campaign/' + campaignId + '/event',
        'location-form': '/api/campaign/' + campaignId + '/location'
    };

    // Форматування дати у потрібний формат
    function formatDate(dateStr) {
        console.log('Отримана дата для форматування:', dateStr);
        
        // Перевірка формату дати (підтримка обох форматів: MM-DD-YYYY та YYYY-MM-DD)
        const mmddyyyyRegex = /^\d{1,2}-\d{1,2}-\d{1,4}$/;
        const yyyymmddRegex = /^\d{1,4}-\d{1,2}-\d{1,2}$/;
        
        let year, month, day;
        
        if (yyyymmddRegex.test(dateStr)) {
            [year, month, day] = dateStr.split('-').map(Number);
        } else if (mmddyyyyRegex.test(dateStr)) {
            [month, day, year] = dateStr.split('-').map(Number);
        } else {
            console.error('Неправильний формат дати:', dateStr);
            throw new Error('Неправильний формат дати. Використовуйте формат MM-DD-YYYY або YYYY-MM-DD');
        }

        // Доповнення року нулями зліва до 4 цифр і конвертація в число
        year = parseInt(String(year).padStart(4, '0'));
        
        // Перевірка валідності року
        if (year < 1) {
            console.error('Неправильний рік:', year);
            throw new Error('Рік повинен бути більше 0');
        }
        
        // Перевірка валідності місяця
        month = parseInt(month);
        if (month < 1 || month > 12) {
            console.error('Неправильний місяць:', month);
            throw new Error('Місяць повинен бути від 1 до 12');
        }
        
        // Перевірка валідності дня
        day = parseInt(day);
        const daysInMonth = new Date(year, month, 0).getDate();
        if (day < 1 || day > daysInMonth) {
            console.error('Неправильний день:', day, 'для місяця:', month);
            throw new Error(`День повинен бути від 1 до ${daysInMonth} для місяця ${month}`);
        }
        
        // Конвертація в формат YYYY-MM-DD
        const formattedDate = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        console.log('Відформатована дата:', formattedDate);
        return formattedDate;
    }

    Object.entries(forms).forEach(([formId, endpoint]) => {
        const form = document.getElementById(formId);
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(form);
                const data = {};
                formData.forEach((value, key) => data[key] = value);

                try {
                    // Перетворюємо дату в правильний формат для події
                    if (formId === 'event-form') {
                        if (!data.date) {
                            alert('Будь ласка, вкажіть дату події');
                            return;
                        }
                        if (!data.name || !data.description) {
                            alert('Будь ласка, заповніть всі поля події');
                            return;
                        }
                        try {
                            data.date = formatDate(data.date);
                            console.log('Дані події для відправки:', data);
                        } catch (error) {
                            alert(error.message);
                            return;
                        }
                    }

                    console.log('Відправляємо дані:', data);
                    console.log('На ендпоінт:', endpoint);
                    
                    const response = await fetch(endpoint, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data)
                    });

                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.error || 'Помилка при збереженні');
                    }

                    const result = await response.json();
                    // Визначаємо тип запису на основі formId
                    const entryType = formId.split('-')[0]; // 'npc', 'event', 'location'
                    addNewEntry(result, entryType);
                    form.reset();
                    // Оновлюємо сторінку після успішного додавання
                    window.location.reload();
                } catch (error) {
                    console.error('Error:', error);
                    alert('Помилка при збереженні: ' + error.message);
                    // Не перезавантажуємо сторінку при помилці, щоб користувач міг виправити дані
                }
            });
        }
    });

    // Функція для додавання нового запису в список
    function addNewEntry(data, type) {
        // Перевіряємо тип і коригуємо його, якщо потрібно
        let listType = type;
        if (type === 'event') listType = 'events';
        else if (type === 'location') listType = 'locations';
        else if (type === 'npc') listType = 'npc';
        
        const list = document.getElementById(`${listType}-list`);
        if (!list) {
            console.error(`Не знайдено список для типу: ${listType}`);
            return;
        }
        
        const div = document.createElement('div');
        div.className = 'entry-item';
        div.setAttribute('data-id', data.id);

        let content = `
            <div class="entry-actions">
                <button class="edit-btn">Редагувати</button>
                <button class="delete-btn">Видалити</button>
            </div>
            <h3>${data.name}</h3>
            <p>${data.description}</p>
        `;

        if ((type === 'event' || type === 'events') && data.date) {
            content += `<small>Дата: ${data.date}</small>`;
        }

        div.innerHTML = content;
        setupEntryActions(div);
        list.appendChild(div);
        
        // Оновлюємо сторінку, щоб відобразити зміни
        // window.location.reload(); // Закоментовано, оскільки ми додаємо елемент динамічно
    }

    // Налаштування дій для записів
    function setupEntryActions(entryElement) {
        const deleteBtn = entryElement.querySelector('.delete-btn');
        const editBtn = entryElement.querySelector('.edit-btn');
        const id = entryElement.getAttribute('data-id');

        deleteBtn.addEventListener('click', () => {
            currentDeleteId = id;
            document.getElementById('delete-modal').style.display = 'block';
        });

        editBtn.addEventListener('click', () => {
            currentEditId = id;
            currentEditType = currentTab;
            const editModal = document.getElementById('edit-modal');
            const form = document.getElementById('edit-form');

            form.elements['name'].value = entryElement.querySelector('h3').textContent;
            form.elements['description'].value = entryElement.querySelector('p').textContent;

            if (currentTab === 'events' || currentTab === 'event') {
                const dateElement = entryElement.querySelector('small');
                if (dateElement) {
                    const dateInput = form.elements['date'];
                    dateInput.style.display = 'block';
                    dateInput.value = dateElement.textContent.replace('Дата: ', '');
                }
            } else {
                form.elements['date'].style.display = 'none';
            }

            editModal.style.display = 'block';
        });
    }

    // Налаштування модальних вікон
    document.querySelectorAll('.close-modal').forEach(button => {
        button.addEventListener('click', () => {
            button.closest('.modal').style.display = 'none';
        });
    });

    // Підтвердження видалення
    document.getElementById('confirm-delete').addEventListener('click', async () => {
        if (!currentDeleteId) {
            console.error('ID для видалення не встановлено');
            return;
        }

        try {
            // Формуємо правильний ендпоінт для видалення
            const apiType = getApiType(currentTab);
            const endpoint = `/api/${apiType}/${currentDeleteId}`;
            console.log('Видалення запису:', { id: currentDeleteId, type: apiType, endpoint });
            
            const response = await fetch(endpoint, {
                method: 'DELETE'
            });

            console.log('Відповідь сервера:', { status: response.status, ok: response.ok });
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Помилка від сервера:', errorText);
                throw new Error(`Помилка сервера: ${response.status} ${errorText}`);
            }

            const element = document.querySelector(`[data-id="${currentDeleteId}"]`);
            if (element) {
                console.log('Елемент знайдено, видаляємо з DOM');
                element.remove();
            } else {
                console.warn('Елемент не знайдено в DOM:', currentDeleteId);
            }

            document.getElementById('delete-modal').style.display = 'none';
            currentDeleteId = null;
            
            // Оновлюємо сторінку після успішного видалення
            console.log('Видалення успішне, оновлюємо сторінку');
            window.location.reload();
        } catch (error) {
            console.error('Помилка при видаленні:', error);
            alert('Помилка при видаленні: ' + error.message);
        }
    });

    // Обробка форми редагування
    document.getElementById('edit-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!currentEditId || !currentEditType) {
            console.error('ID або тип для редагування не встановлено', { id: currentEditId, type: currentEditType });
            return;
        }

        const form = e.target;
        const formData = new FormData(form);
        const data = {};
        formData.forEach((value, key) => data[key] = value);

        try {
            // Перевіряємо та форматуємо дату для події
            if (currentEditType === 'events') {
                if (!data.date) {
                    alert('Будь ласка, вкажіть дату події');
                    return;
                }
                if (!data.name || !data.description) {
                    alert('Будь ласка, заповніть всі поля події');
                    return;
                }
                try {
                    data.date = formatDate(data.date);
                    console.log('Дані події для відправки:', {
                        name: data.name,
                        description: data.description,
                        date: data.date
                    });
                } catch (error) {
                    alert(error.message);
                    return;
                }
            }
            // Формуємо правильний ендпоінт для редагування
            const apiType = getApiType(currentEditType);
            const endpoint = `/api/${apiType}/${currentEditId}`;
            
            // Формуємо об'єкт з необхідними полями
            const requestData = {
                name: data.name,
                description: data.description
            };
            
            // Додаємо дату тільки для подій
            if (currentEditType === 'events') {
                requestData.date = data.date;
            }
            
            console.log('Редагування запису:', { id: currentEditId, type: apiType, endpoint, data: requestData });
            
            const response = await fetch(endpoint, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            console.log('Відповідь сервера:', { status: response.status, ok: response.ok });
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Помилка від сервера:', errorText);
                throw new Error(`Помилка сервера: ${response.status} ${errorText}`);
            }

            const result = await response.json();
            console.log('Отримані дані після редагування:', result);
            
            const element = document.querySelector(`[data-id="${currentEditId}"]`);
            if (element) {
                console.log('Елемент знайдено, оновлюємо в DOM');
                element.querySelector('h3').textContent = result.name;
                element.querySelector('p').textContent = result.description;
                if (currentEditType === 'events' && result.date) {
                    const dateElement = element.querySelector('small');
                    if (dateElement) {
                        dateElement.textContent = `Дата: ${result.date}`;
                    }
                }
            } else {
                console.warn('Елемент не знайдено в DOM:', currentEditId);
            }

            document.getElementById('edit-modal').style.display = 'none';
            currentEditId = null;
            currentEditType = null;
            
            // Оновлюємо сторінку після успішного редагування
            console.log('Редагування успішне, оновлюємо сторінку');
            window.location.reload();
        } catch (error) {
            console.error('Помилка при оновленні:', error);
            alert('Помилка при оновленні: ' + error.message);
        }
    });

    // Ініціалізація дій для існуючих записів
    document.querySelectorAll('.entry-item').forEach(setupEntryActions);
});
