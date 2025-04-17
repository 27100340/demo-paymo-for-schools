document.getElementById('topupForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const messageDiv = document.getElementById('message');
    
    try {
        const response = await fetch('/topup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                student_id: document.getElementById('student_id').value,
                school_name: document.getElementById('school_name').value,
                amount: document.getElementById('amount').value
            })
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            messageDiv.className = 'success';
            messageDiv.textContent = `Top-up successful! New balance: $${data.new_balance}`;
            document.getElementById('topupForm').reset();
        } else {
            messageDiv.className = 'error';
            messageDiv.textContent = `Top-up failed: ${data.message}`;
        }
    } catch (error) {
        messageDiv.className = 'error';
        messageDiv.textContent = 'An error occurred while processing the request';
    }
});

function showAddUserForm() {
    document.getElementById('addUserForm').style.display = 'block';
}

function hideAddUserForm() {
    document.getElementById('addUserForm').style.display = 'none';
    document.getElementById('userForm').reset();
}

async function deleteUser(username) {
    if (!confirm(`Are you sure you want to delete user "${username}"?`)) {
        return;
    }

    try {
        const response = await fetch('/admin/update-user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                action: 'delete'
            })
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            alert('User deleted successfully');
            location.reload();
        } else {
            alert('Error deleting user: ' + data.message);
        }
    } catch (error) {
        alert('An error occurred while deleting user');
    }
}

async function editUser(username) {
    const newPassword = prompt('Enter new password for user:');
    if (newPassword === null) return; // User canceled

    try {
        const response = await fetch('/admin/update-user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                action: 'update',
                password: newPassword
            })
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            alert('User password updated successfully');
            location.reload();
        } else {
            alert('Error updating user: ' + data.message);
        }
    } catch (error) {
        alert('An error occurred while updating user');
    }
}

document.getElementById('userForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    try {
        const response = await fetch('/admin/update-user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'add',
                username: document.getElementById('new_username').value,
                password: document.getElementById('new_password').value,
                name: document.getElementById('new_name').value,
                school: document.getElementById('new_school').value,
                student_id: document.getElementById('new_student_id').value
            })
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        alert('Error adding user');
    }
});

document.getElementById('adminLoginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const response = await fetch('/admin-login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: document.getElementById('username').value,
            password: document.getElementById('password').value
        })
    });
    
    const data = await response.json();
    if (data.status === 'success') {
        window.location.href = '/admin-dashboard';
    } else {
        alert('Login failed: ' + data.message);
    }
});