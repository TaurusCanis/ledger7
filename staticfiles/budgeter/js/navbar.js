const hamburger = document.querySelector(".hamburger");
const navMenu = document.querySelector(".nav-menu");

console.log("hamburger", hamburger)

hamburger.addEventListener("click", mobileMenu);

function mobileMenu() {
  hamburger.classList.toggle("active");
  navMenu.classList.toggle("active");

  if (hamburger.classList.contains("active")) {
    this.setAttribute('aria-expanded', 'true');
  } else {
    this.setAttribute('aria-expanded', 'false');
  }
}
