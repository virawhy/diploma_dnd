
const options = {
  root: null,
  threshold: 0.1,
  rootMargin: '0px'
}


const observerDown = new IntersectionObserver(function(entries, observer) {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('show-down');
      observer.unobserve(entry.target);
    }
  });
}, options);

const observerDownDelay = new IntersectionObserver(function(entries, observer) {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('show-down-delay');
      observer.unobserve(entry.target);
    }
  });
}, options);

const observerLeft = new IntersectionObserver(function(entries, observer) {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('show-left');
      observer.unobserve(entry.target);
    }
  });
}, options);

const observerRight = new IntersectionObserver(function(entries, observer) {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('show-right');
      observer.unobserve(entry.target);
    }
  });
}, options);

const observerUnRight = new IntersectionObserver(function(entries, observer) {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('un-show-right');
      observer.unobserve(entry.target);
    }
  });
}, options);

