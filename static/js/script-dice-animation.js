// Функція для створення та відображення спливаючого вікна з анімацією
function showSkillCheckWindow(skillName, mainStatValue, skillValue, hasProficiency) {
    // Створюємо елементи спливаючого вікна
    const popup = document.createElement('div');
    popup.className = 'skill-check-popup';
    
    const d20Container = document.createElement('div');
    d20Container.className = 'd20-container';
    
    // Створюємо два кубики, якщо є proficiency
    const d20First = document.createElement('div');
    d20First.className = 'd20';
    d20First.innerHTML = `<div class="d20-container"><span class="d20-number">20</span></div>`;
    
    let d20Second = null;
    if (hasProficiency) {
        d20Second = document.createElement('div');
        d20Second.className = 'd20';
        d20Second.innerHTML = `<div class="d20-container"><span class="d20-number">20</span></div>`;

        d20Second.style.marginTop = '-230px';
    }
    
    const resultContainer = document.createElement('div');
    resultContainer.className = 'result-container';
    
    // Додаємо елементи до DOM
    d20Container.appendChild(d20First);
    if (hasProficiency) {
        d20Container.appendChild(d20Second);
    }
    popup.appendChild(d20Container);
    popup.appendChild(resultContainer);
    document.body.appendChild(popup);
    
    // Анімація кидка кубика
    let rotations = 0;
    let maxRotations = 10;
    let speed = 100;
    let diceResult1 = Math.floor(Math.random() * 20) + 1;
    let diceResult2 = hasProficiency ? Math.floor(Math.random() * 20) + 1 : 0;
    
    function animateDice() {
        if (rotations < maxRotations) {
            d20First.style.transform = `rotate(${rotations * 360}deg)`;
            if (hasProficiency) {
                d20Second.style.transform = `rotate(${rotations * 360}deg)`;
            }
            rotations++;
            speed = Math.max(50, speed - 5);
            setTimeout(animateDice, speed);
        } else {
            // Показуємо результат
            const d20Number1 = d20First.querySelector('.d20-number');
            d20Number1.textContent = diceResult1;
            
            let finalDiceResult = diceResult1;
            if (hasProficiency) {
                const d20Number2 = d20Second.querySelector('.d20-number');
                d20Number2.textContent = diceResult2;
                finalDiceResult = Math.max(diceResult1, diceResult2);
            }
            
            // Розраховуємо модифікатор основної характеристики
            let mainStatMod = Math.floor((mainStatValue - 10) / 2);
            
            // Розраховуємо загальну суму
            const total = mainStatMod + parseInt(skillValue) + finalDiceResult;
            
            // Відображаємо результат
            let resultText = `Результат: ${total}<br>`;
            
            if (hasProficiency) {
                const total1 = mainStatMod + parseInt(skillValue) + diceResult1;
                const total2 = mainStatMod + parseInt(skillValue) + diceResult2;
                resultText += `Перший кидок: ${total1} (${mainStatMod} + ${skillValue} + ${diceResult1})<br>`;
                resultText += `Другий кидок: ${total2} (${mainStatMod} + ${skillValue} + ${diceResult2})<br>`;
                resultText += `Обрано найвищий результат: ${total}`;
            } else {
                resultText += `(${mainStatMod} + ${skillValue} + ${finalDiceResult})`;
            }
            
            if (finalDiceResult === 20) {
                resultText += '<br><span class="critical-success">Критичний успіх!</span>';
            } else if (finalDiceResult === 1) {
                resultText += '<br><span class="critical-fail">Критичний провал!</span>';
            }
            
            resultContainer.innerHTML = resultText;
        }
    }
    
    // Запускаємо анімацію
    animateDice();
    
    // Закриваємо вікно при кліку поза ним
    popup.addEventListener('click', (e) => {
        if (e.target === popup) {
            document.body.removeChild(popup);
        }
    });
}

// Додаємо обробники подій для всіх навичок
document.addEventListener('DOMContentLoaded', () => {
    const skillElements = document.querySelectorAll('.character-stats-prof-list-element p');
    
    skillElements.forEach(skillElement => {
        // Видаляємо старі обробники подій, якщо вони є
        const oldClickHandler = skillElement._clickHandler;
        if (oldClickHandler) {
            skillElement.removeEventListener('click', oldClickHandler);
        }

        // Створюємо новий обробник
        const clickHandler = () => {
            const skillContainer = skillElement.closest('.character-stats-prof-list-element');
            const skillInput = skillContainer.querySelector('input[type="number"]');
            const proficiencyCheckbox = skillContainer.querySelector('input[type="checkbox"]');
            const parentId = skillInput.getAttribute('data-parent');
            const parentInput = document.getElementById(parentId);
            
            showSkillCheckWindow(
                skillElement.textContent,
                parentInput.value,
                skillInput.value,
                proficiencyCheckbox.checked
            );
        };

        // Зберігаємо посилання на обробник
        skillElement._clickHandler = clickHandler;
        
        // Додаємо новий обробник
        skillElement.addEventListener('click', clickHandler);
    });
});