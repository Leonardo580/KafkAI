window.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('signup_form');
    const usernameInput = form.querySelector('#id_username');
    const emailInput = form.querySelector('#id_email');
    const passwordInput1 = form.querySelector('#id_password1');
    const passwordInput2 = form.querySelector('#id_password2');

    usernameInput.classList.add('border-0', 'px-3', 'py-3', 'placeholder-gray-400', 'text-gray-700', 'bg-white', 'rounded', 'text-sm', 'shadow', 'focus:outline-none', 'focus:ring', 'w-full');
    emailInput.classList.add('border-0', 'px-3', 'py-3', 'placeholder-gray-400', 'text-gray-700', 'bg-white', 'rounded', 'text-sm', 'shadow', 'focus:outline-none', 'focus:ring', 'w-full');
    passwordInput1.classList.add('border-0', 'px-3', 'py-3', 'placeholder-gray-400', 'text-gray-700', 'bg-white', 'rounded', 'text-sm', 'shadow', 'focus:outline-none', 'focus:ring', 'w-full');
    passwordInput2.classList.add('border-0', 'px-3', 'py-3', 'placeholder-gray-400', 'text-gray-700', 'bg-white', 'rounded', 'text-sm', 'shadow', 'focus:outline-none', 'focus:ring', 'w-full');
});