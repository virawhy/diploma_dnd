  const parents = document.querySelectorAll('.parent');

  parents.forEach((parent) => {
    parent.addEventListener('input', () => {

      const parentValue = parseInt(parent.value);

      const children = document.querySelectorAll(`.child[data-parent="${parent.id}"]`);

      children.forEach((child) => {

        const checkbox = document.querySelector(`[for="${child.id}"]`);

        let newValue = parentValue / 4;

        newValue = Math.floor(newValue);

        child.value = newValue;
      });
    });
  });

  document.addEventListener('DOMContentLoaded', function() {

    const parents1 = document.querySelectorAll('.parent');

        parents1.forEach(element => {

          const parentValue = parseInt(element.value);

          const children = document.querySelectorAll(`.child[data-parent="${element.id}"]`);

          children.forEach((child) => {

            const checkbox = document.querySelector(`[for="${child.id}"]`);
    
            let newValue = parentValue / 4;
    
            newValue = Math.floor(newValue);
    
            child.value = newValue;
        });
      });

  });

