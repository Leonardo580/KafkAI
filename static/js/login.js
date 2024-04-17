window.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('login-form');
    const usernameInput = form.querySelector('#id_username');
    const passwordInput = form.querySelector('#id_password');

    usernameInput.classList.add('border-0', 'px-3', 'py-3', 'placeholder-gray-400', 'text-gray-700', 'bg-white', 'rounded', 'text-sm', 'shadow', 'focus:outline-none', 'focus:ring', 'w-full');
    passwordInput.classList.add('border-0', 'px-3', 'py-3', 'placeholder-gray-400', 'text-gray-700', 'bg-white', 'rounded', 'text-sm', 'shadow', 'focus:outline-none', 'focus:ring', 'w-full');
});