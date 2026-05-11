const searchInput = document.querySelector('#search');
const monsters = document.querySelectorAll('.monster');

searchInput.addEventListener('input', () => {
  const searchText = searchInput.value.toLowerCase();

  monsters.forEach(monster => {
    const name = monster.querySelector('.name').textContent.toLowerCase();

    if (name.includes(searchText)) {
      monster.style.display = '';
    } else {
      monster.style.display = 'none';
    }
  });
});