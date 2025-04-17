document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    const response = await fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    });
    
    const data = await response.json();
    if (data.status === 'success') {
        sessionStorage.setItem('username', username);
        sessionStorage.setItem('password', password); // Store password for session
        window.location.href = '/dashboard';
    } else {
        alert('Login failed: ' + data.message);
    }
});