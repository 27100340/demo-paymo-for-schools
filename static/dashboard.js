window.onload = async () => {
    // const username = sessionStorage.getItem('username');
    // if (!username) {
    //     window.location.href = '/';
    //     return;
    // }

    try {
        const response = await fetch('/get-user-data', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            // body: JSON.stringify({ username: username })
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            document.getElementById('studentName').textContent = data.name;
            document.getElementById('balance').textContent = data.balance;
            updateTransactionTable(data.transactions);
        } else {
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Error loading user data:', error);
        window.location.href = '/';
    }
};

function updateTransactionTable(transactions) {
    const tbody = document.getElementById('transactionBody');
    tbody.innerHTML = '';
    
    transactions.forEach(tx => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${tx.type}</td>
            <td>$${tx.amount}</td>
            <td>${tx.type === 'topup' ? `Via ${tx.method}` : 
                tx.type === 'received' ? `From: ${tx.with} (${tx.school})` : 
                `${tx.details || ''}`}</td>
            <td>${tx.timestamp}</td>
        `;
        tbody.appendChild(row);
    });
}

function showSendMoneyForm() {
    document.getElementById('sendMoneyForm').style.display = 'block';
}

function hideSendMoneyForm() {
    document.getElementById('sendMoneyForm').style.display = 'none';
    document.getElementById('sendForm').reset();
}

document.getElementById('sendForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const response = await fetch('/send', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            recipient_id: document.getElementById('recipient_id').value,
            recipient_school: document.getElementById('recipient_school').value,
            amount: document.getElementById('amount').value
        })
    });
    
    const data = await response.json();
    if (data.status === 'success') {
        document.getElementById('balance').textContent = data.sender_balance;
        updateTransactionTable(data.transactions);
        hideSendMoneyForm();
        alert('Money sent successfully!');
    } else {
        alert('Transaction failed: ' + data.message);
    }
});