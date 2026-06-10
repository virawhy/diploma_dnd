export function startAttack(attacker) {
    if (!attacker || !attacker.dataset) return;
    if (!attacker.closest('.grid-cell')) return;

    const gameField = document.querySelector('.game-field');
    if (!gameField) return;

    const ray = document.createElement('div');
    ray.className = 'attack-ray';
    gameField.appendChild(ray);

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

        const cellSize = 50;
        const distanceInCells = distance / cellSize;
        const distanceInFeet = Math.round(distanceInCells * 3);
        const labelX = attackerCenter.x + Math.cos(angle) * (distance / 2);
        const labelY = attackerCenter.y + Math.sin(angle) * (distance / 2) - 20;

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
        distanceLabel.remove();
    }

    gameField.addEventListener('mousemove', updateRay);
    gameField.addEventListener('click', handleClick);
}

export function showAttackDialog(attacker, target) {
    const dialog = document.createElement('div');
    dialog.className = 'attack-dialog';

    const attackerName = cleanSpriteName(attacker.alt);
    const targetName = cleanSpriteName(target.alt);
    const targetHp = target.dataset.health || 7;
    const targetAc = target.dataset.ac || 12;

    dialog.innerHTML = `
        <div class="attack-dialog-content">
            <button class="attack-close" type="button" aria-label="Закрити">&times;</button>
            <div class="attack-dialog-header">
                <span class="attack-dialog-kicker">Бойова дія</span>
                <h3>Атака</h3>
            </div>
            <div class="combatants">
                <div class="combatant-card">
                    <span>Атакує</span>
                    <strong>${attackerName}</strong>
                </div>
                <div class="combatant-card target-card">
                    <span>Ціль</span>
                    <strong>${targetName}</strong>
                    <small>HP ${targetHp} · AC ${targetAc}</small>
                </div>
            </div>
            <div class="attack-roll">
                <h4>Кидок на влучання</h4>
                <label class="attack-field">
                    <span>Бонус атаки</span>
                    <input type="number" id="attackBonus" value="0" min="0" max="20">
                </label>
                <button class="roll-attack-button" type="button">Кинути d20</button>
                <p id="rollResult" class="attack-result"></p>
            </div>
            <div class="damage-roll" hidden>
                <h4>Кидок шкоди</h4>
                <div class="dice-selection">
                    <label>d4 <input type="number" id="d4" value="0" min="0" max="10"></label>
                    <label>d6 <input type="number" id="d6" value="0" min="0" max="10"></label>
                    <label>d8 <input type="number" id="d8" value="0" min="0" max="10"></label>
                    <label>d10 <input type="number" id="d10" value="0" min="0" max="10"></label>
                    <label>d12 <input type="number" id="d12" value="0" min="0" max="10"></label>
                </div>
                <label class="attack-field">
                    <span>Модифікатор шкоди</span>
                    <input type="number" id="damageBonus" value="0">
                </label>
                <div class="damage-modifiers">
                    <label><input type="checkbox" id="resistance"> Супротив</label>
                    <label><input type="checkbox" id="vulnerability"> Вразливість</label>
                </div>
                <button class="roll-damage-button" type="button">Кинути шкоду</button>
                <p id="damageResult" class="attack-result"></p>
            </div>
        </div>
    `;

    document.body.appendChild(dialog);

    const rollAttackButton = dialog.querySelector('.roll-attack-button');
    const rollDamageButton = dialog.querySelector('.roll-damage-button');
    const closeButton = dialog.querySelector('.attack-close');

    rollAttackButton.addEventListener('click', () => rollD20(dialog, target));
    rollDamageButton.addEventListener('click', () => rollDamage(dialog, target));
    closeButton.addEventListener('click', () => dialog.remove());
}

function cleanSpriteName(name) {
    return (name || 'Токен').replace('.png', '');
}

function rollD20(dialog, target) {
    const roll = Math.floor(Math.random() * 20) + 1;
    const bonus = parseInt(dialog.querySelector('#attackBonus').value) || 0;
    const total = roll + bonus;
    const targetAC = parseInt(target.dataset.ac) || 12;
    const resultElement = dialog.querySelector('#rollResult');

    resultElement.textContent = `Результат: ${total} (${roll} + ${bonus})`;

    if (total >= targetAC) {
        resultElement.className = 'attack-result success';
        dialog.querySelector('.damage-roll').hidden = false;
    } else {
        resultElement.className = 'attack-result failure';
    }
}

function rollDamage(dialog, target) {
    const diceTypes = [4, 6, 8, 10, 12];
    let totalDamage = 0;

    diceTypes.forEach(dice => {
        const count = parseInt(dialog.querySelector(`#d${dice}`).value) || 0;
        for (let i = 0; i < count; i++) {
            totalDamage += Math.floor(Math.random() * dice) + 1;
        }
    });

    const bonus = parseInt(dialog.querySelector('#damageBonus').value) || 0;
    totalDamage += bonus;

    if (dialog.querySelector('#resistance').checked) {
        totalDamage = Math.floor(totalDamage / 2);
    }
    if (dialog.querySelector('#vulnerability').checked) {
        totalDamage *= 2;
    }

    dialog.querySelector('#damageResult').textContent = `Загальна шкода: ${totalDamage}`;

    const currentHealth = parseInt(target.dataset.health) || 7;
    target.dataset.health = Math.max(0, currentHealth - totalDamage);

    const selectedContent = document.getElementById('selected-content');
    const healthSpan = selectedContent?.querySelector('.health');
    if (healthSpan && selectedContent.contains(target)) {
        healthSpan.textContent = target.dataset.health;
    }

    document.dispatchEvent(new CustomEvent('token-hp-updated', {
        detail: {
            tokenId: `${target.alt}-${target.src}`,
            newHP: parseInt(target.dataset.health) || 0
        }
    }));
}
