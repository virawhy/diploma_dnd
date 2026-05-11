const create_char1 = document.getElementById("id-create-char-caption");
const create_char2 = document.getElementById("id-create-char-question");
const create_char3 = document.getElementById("id-create-char-stats-caption");
const create_char4 = document.getElementById("id-create-char-stats-caption some-margin");

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

observerDown.observe(create_char1);
observerLeft.observe(create_char2);
observerLeft.observe(create_char3);
observerLeft.observe(create_char4);
