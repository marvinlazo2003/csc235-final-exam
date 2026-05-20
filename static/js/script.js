// Tornado table search filter
const searchInput = document.getElementById('searchInput');

if (searchInput) {
    searchInput.addEventListener('keyup', function () {
        let filter = searchInput.value.toLowerCase();

        let rows = document.querySelectorAll('#tornadoTable tbody tr');

        rows.forEach(row => {
            let text = row.textContent.toLowerCase();

            if (text.includes(filter)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
}

// Dynamic clock
function updateClock() {
    const clock = document.getElementById('clock');

    if (clock) {
        const now = new Date();
        clock.innerHTML = now.toLocaleString();
    }
}

setInterval(updateClock, 1000);