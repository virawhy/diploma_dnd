document.addEventListener('DOMContentLoaded', function() {
    // Отримання елементів модальних вікон
    const createModal = document.getElementById('createCampaignModal');
    const deleteModal = document.getElementById('deleteCampaignModal');
    const createForm = document.getElementById('createCampaignForm');
    const createBtn = document.getElementById('createCampaignBtn');
    const closeBtns = document.getElementsByClassName('close');
    const cancelBtns = document.getElementsByClassName('cancel-btn');

    let campaignToDelete = null;

    // Відкриття модального вікна створення кампанії
    createBtn.onclick = function() {
        createModal.style.display = 'block';
    }

    // Закриття модальних вікон при кліку на хрестик
    Array.from(closeBtns).forEach(btn => {
        btn.onclick = function() {
            createModal.style.display = 'none';
            deleteModal.style.display = 'none';
        }
    });

    // Закриття модальних вікон при кліку на кнопку скасування
    Array.from(cancelBtns).forEach(btn => {
        btn.onclick = function() {
            createModal.style.display = 'none';
            deleteModal.style.display = 'none';
        }
    });

    // Закриття модальних вікон при кліку поза ними
    window.onclick = function(event) {
        if (event.target == createModal || event.target == deleteModal) {
            createModal.style.display = 'none';
            deleteModal.style.display = 'none';
        }
    }

    // Обробка створення нової кампанії
    createForm.onsubmit = async function(e) {
        e.preventDefault();
        const formData = new FormData(createForm);
        try {
            const response = await fetch('/create_campaign', {
                method: 'POST',
                body: formData
            });
            if (response.ok) {
                location.reload();
            } else {
                alert('Помилка при створенні кампанії');
            }
        } catch (error) {
            console.error('Помилка:', error);
            alert('Помилка при створенні кампанії');
        }
    }

    // Обробка видалення кампанії
    const deleteBtns = document.getElementsByClassName('delete-campaign-btn');
    Array.from(deleteBtns).forEach(btn => {
        btn.onclick = function() {
            campaignToDelete = btn.dataset.id;
            deleteModal.style.display = 'block';
        }
    });

    // Підтвердження видалення кампанії
    document.getElementById('confirmDelete').onclick = async function() {
        if (campaignToDelete) {
            try {
                const response = await fetch(`/delete_campaign/${campaignToDelete}`, {
                    method: 'POST'
                });
                if (response.ok) {
                    location.reload();
                } else {
                    alert('Помилка при видаленні кампанії');
                }
            } catch (error) {
                console.error('Помилка:', error);
                alert('Помилка при видаленні кампанії');
            }
        }
        deleteModal.style.display = 'none';
    }

    // Обробка прийняття запрошення
    const acceptBtns = document.getElementsByClassName('accept-invite-btn');
    Array.from(acceptBtns).forEach(btn => {
        btn.onclick = async function() {
            const membershipId = btn.dataset.id;
            try {
                const response = await fetch(`/accept_invitation/${membershipId}`, {
                    method: 'POST'
                });
                if (response.ok) {
                    location.reload();
                } else {
                    alert('Помилка при прийнятті запрошення');
                }
            } catch (error) {
                console.error('Помилка:', error);
                alert('Помилка при прийнятті запрошення');
            }
        }
    });

    // Обробка відхилення запрошення
    const declineBtns = document.getElementsByClassName('decline-invite-btn');
    Array.from(declineBtns).forEach(btn => {
        btn.onclick = async function() {
            const membershipId = btn.dataset.id;
            try {
                const response = await fetch(`/decline_invitation/${membershipId}`, {
                    method: 'POST'
                });
                if (response.ok) {
                    location.reload();
                } else {
                    alert('Помилка при відхиленні запрошення');
                }
            } catch (error) {
                console.error('Помилка:', error);
                alert('Помилка при відхиленні запрошення');
            }
        }
    });

    // Функція для форматування даних персонажа
    function formatCharacterInfo(character) {
        console.log('Форматування персонажа:', character);
        const name = character.name 
        const level = character.level 
        const race = character.race 
        const className = character.class
        
        return `${name} (Рівень ${level}) - ${race} ${className}`;
    }
    
    // Обробка додавання персонажа
    const addCharacterBtn = document.getElementById('addCharacterBtn');
    const characterModal = document.getElementById('addCharacterModal');
    const characterList = document.getElementById('characterList');
    
    if (addCharacterBtn) {
        addCharacterBtn.onclick = async function() {
            const username = document.getElementById('username').value;
            const campaignId = this.dataset.campaignId;
            
            try {
                const response = await fetch(`/api/campaign/${campaignId}/user/${username}/characters`);
                if (response.ok) {
                    const characters = await response.json();
                    console.log('Отримані персонажі:', characters);
                    characterList.innerHTML = '';
                    characters.forEach(character => {
                        console.log('Обробка персонажа:', character);
                        const characterDiv = document.createElement('div');
                        characterDiv.className = 'character-item';
                        characterDiv.innerHTML = `
                            <span>${formatCharacterInfo(character)}</span>
                            <button class="select-character-btn" data-character-id="${character.id_character}">
                                Обрати
                            </button>
                        `;
                        characterList.appendChild(characterDiv);
                    });
                    
                    // Додаємо обробники для кнопок вибору персонажа
                    const selectBtns = document.getElementsByClassName('select-character-btn');
                    Array.from(selectBtns).forEach(btn => {
                        btn.onclick = async function() {
                            const characterId = this.dataset.characterId;
                            try {
                                const response = await fetch(`/api/campaign/${campaignId}/character/${characterId}`, {
                                    method: 'POST'
                                });
                                if (response.ok) {
                                    location.reload();
                                } else {
                                    alert('Помилка при додаванні персонажа до кампанії');
                                }
                            } catch (error) {
                                console.error('Помилка:', error);
                                alert('Помилка при додаванні персонажа до кампанії');
                            }
                        }
                    });
                } else {
                    alert('Помилка при отриманні списку персонажів');
                }
            } catch (error) {
                console.error('Помилка:', error);
                alert('Помилка при отриманні списку персонажів');
            }
        }
    }
});

    findUserBtn.onclick = async function() {
        const username = usernameInput.value;
        try {
            const response = await fetch(`/api/campaign/${campaignId}/user/${username}/characters`);
            const characters = await response.json();
            
            console.log('Отримані дані персонажів:', characters);
            
            if (response.ok) {
                characterList.innerHTML = characters.map(char => {
                    console.log('Обробка персонажа:', char);
                    
                    // Перевірка та логування даних персонажа
                    console.log('Раса:', char.race);
                    console.log('Клас:', char.class);
                    
                    
                    const charLevel = char.level ;
                    
                    return `
                        <div class="character-option" data-id="${char.id_character}">
                            <h4>${char.name || 'Безіменний'}</h4>
                            <p>${char.race} - ${className} (Рівень ${charLevel})</p>
                        </div>
                    `;
                }).join('');
            }
        } catch (error) {
            console.error('Детальна помилка при пошуку користувача:', error);
            alert('Помилка при пошуку користувача. Перевірте консоль для деталей.');
        }
    }
