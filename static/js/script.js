// Input Highlighting
document.querySelectorAll('input').forEach(input => {
    input.addEventListener('focus', () => {
        input.style.borderColor = '#0077ff';
        input.style.boxShadow = '0 0 5px rgba(0, 119, 255, 0.4)';
    });
    input.addEventListener('blur', () => {
        input.style.borderColor = '#ccc';
        input.style.boxShadow = 'none';
    });
});

// Disable submit button on submit to prevent spam
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', () => {
        const btn = form.querySelector('button[type="submit"]');
        if (btn) {
            btn.disabled = true;
            btn.innerText = 'Processing...';
        }
    });
});

// Balance coloring
const balanceEl = document.querySelector('.balance');
if (balanceEl) {
    const value = parseFloat(balanceEl.innerText.replace(/[^\d.-]/g, ''));
    if (value < 100) {
        balanceEl.style.color = '#ff2e2e'; // danger low
    } else if (value > 100000) {
        balanceEl.style.color = '#00c851'; // rich mode
    } else {
        balanceEl.style.color = '#008c3e';
    }
}

// Auto-dismiss alert divs (if added later)
const alertBox = document.querySelector('.alert');
if (alertBox) {
    setTimeout(() => {
        alertBox.style.opacity = '0';
        setTimeout(() => alertBox.remove(), 500);
    }, 4000);
}

// ====================
// ✅ Toast System
// ====================
function showToast(message, category) {
    const toast = document.createElement("div");
    toast.className = `toast toast-${category} show`;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => document.body.removeChild(toast), 500);
    }, 4000);
}

