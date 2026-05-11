// Модуль для роботи з атаками
export function startAttack(attacker) {
    if (!attacker || !attacker.dataset) return;

    const gameField = document.querySelector('.game-field');
    if (!gameField) return;

    const ray = document.createElement('div');
    ray.className = 'attack-ray';
    gameField.appendChild(ray);

    // Створюємо елемент для відображення відстані
    const distanceLabel = document.createElement('div');
    distanceLabel.className = 'attack-distance-label';
    gameField.appendChild(distanceLabel);

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

        // Розрахунок відстані в футах (3 фути = 1 клітинка ігрового поля)
        // Розмір клітинки - 50px
        const cellSize = 50;
        const distanceInCells = distance / cellSize;
        const distanceInFeet = Math.round(distanceInCells * 3);

        // Позиціонуємо мітку відстані над серединою лінії атаки
        const labelX = attackerCenter.x + Math.cos(angle) * (distance / 2);
        const labelY = attackerCenter.y + Math.sin(angle) * (distance / 2) - 20; // 20px вище лінії

        distanceLabel.textContent = `${distanceInFeet} футів`;
        distanceLabel.style.left = `${labelX}px`;
        distanceLabel.style.top = `${labelY}px`;
        distanceLabel.style.display = 'block';
    }

    function handleClick(e) {
        const targetCell = e.target.closest('.grid-cell');
        const sprites = targetCell?.querySelectorAll('.sprite');
        const target = Array.from(sprites || []).find(sprite => 
            sprite !== attacker && 
            !sprite.src.includes('/environment/') && 
            sprite === e.target
        );
        if (target) {
            showAttackDialog(attacker, target);
        }
        cleanup();
    }

    function cleanup() {
        gameField.removeEventListener('mousemove', updateRay);
        gameField.removeEventListener('click', handleClick);
        ray.remove();
        distanceLabel.remove(); // Видаляємо мітку відстані
    }

    gameField.addEventListener('mousemove', updateRay);
    gameField.addEventListener('click', handleClick);
}

export function showAttackDialog(attacker, target) {
    const dialog = document.createElement('div');
    dialog.className = 'attack-dialog';
    dialog.innerHTML = `
        <div class="attack-dialog-content">
            <h3>Атака</h3>
            <p>Ціль: ${target.alt.replace('.png', '')}</p>
            <p>Здоров'я цілі: ${target.dataset.health || 7}</p>
            <p>Клас броні цілі: ${target.dataset.ac || 12}</p>
            <div class="attack-roll">
                <button onclick="rollD20()">Кинути к20</button>
                <input type="number" id="attackBonus" value="0" min="0" max="20" placeholder="Бонус атаки">
                <p id="rollResult"></p>
            </div>
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
                <button onclick="rollDamage()">Кинути на шкоду</button>
                <p id="damageResult"></p>
            </div>
            <button onclick="this.closest('.attack-dialog').remove()">Закрити</button>
        </div>
    `;
    document.body.appendChild(dialog);

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

        const currentHealth = parseInt(target.dataset.health) || 7;
        target.dataset.health = Math.max(0, currentHealth - totalDamage);
        
        const selectedContent = document.getElementById('selected-content');
        const healthSpan = selectedContent.querySelector('.health');
        if (healthSpan && selectedContent.contains(target)) {
            healthSpan.textContent = target.dataset.health;
        }
    };
}