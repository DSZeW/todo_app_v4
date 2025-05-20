document.addEventListener("DOMContentLoaded", function () {
    const logo = document.querySelector(".navbar-logo");
    const links = document.querySelector(".navbar-links");

    logo.addEventListener("click", function () {
        links.classList.toggle("active");
    });
});
