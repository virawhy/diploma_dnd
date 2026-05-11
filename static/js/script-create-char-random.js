const inputs = Array.from(document.querySelectorAll('.random-stats-container input[type="text"]'));
      document.querySelector('.random-stats-button').addEventListener('click', () => {
      inputs.forEach(input => {
      const nums = Array.from({length: 4}, () => Math.floor(Math.random() * 6) + 1);
      nums.sort((a, b) => b - a);
      const sum = nums.slice(0, 3).reduce((acc, cur) => acc + cur, 0);
      input.value = sum;
    });
  });
