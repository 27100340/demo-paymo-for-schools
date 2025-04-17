document.getElementById('signupForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const response = await fetch('/signup', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: document.getElementById('username').value,
            password: document.getElementById('password').value,
            name: document.getElementById('name').value,
            school: document.getElementById('school').value,
            student_id: document.getElementById('student_id').value
        })
    });
    
    const data = await response.json();
    if (data.status === 'success') {
        alert('Account created successfully!');
        window.location.href = '/login';
    } else {
        alert('Signup failed: ' + data.message);
    }
});