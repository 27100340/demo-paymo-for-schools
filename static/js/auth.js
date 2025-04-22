async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();
        
        if (data.status === 'success') {
            window.location.href = '/dashboard';
        } else {
            alert(data.message || 'Login failed');
        }
    } catch (error) {
        alert('An error occurred. Please try again.');
    }
}

async function handleSignup(event) {
    event.preventDefault();
    
    const formData = {
        name: document.getElementById('name').value,
        username: document.getElementById('username').value,
        school: document.getElementById('school').value,
        student_id: document.getElementById('student_id').value,
        password: document.getElementById('password').value,
    };

    try {
        const response = await fetch('/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        });

        const data = await response.json();
        
        if (data.status === 'success') {
            window.location.href = '/login';
        } else {
            alert(data.message || 'Signup failed');
        }
    } catch (error) {
        alert('An error occurred. Please try again.');
    }
}