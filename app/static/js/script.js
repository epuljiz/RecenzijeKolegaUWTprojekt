// Glavni JavaScript za Recenzijsku platformu

document.addEventListener('DOMContentLoaded', function () {
    initializeFilters();
    initializeRatingInputs();
    initializeUserSearch();
});

// Funkcije za filtriranje recenzija
function initializeFilters() {
    const filterRating = document.getElementById('filter_rating');
    const filterProject = document.getElementById('filter_project');
    const searchUser = document.getElementById('search_user');

    if (filterRating) {
        filterRating.addEventListener('change', filterReviews);
    }
    if (filterProject) {
        filterProject.addEventListener('change', filterReviews);
    }
    if (searchUser) {
        searchUser.addEventListener('input', filterReviews);
    }
}

function filterReviews() {
    const ratingFilter = document.getElementById('filter_rating').value;
    const projectFilter = document.getElementById('filter_project').value;
    const userSearch = document.getElementById('search_user').value.toLowerCase();

    const reviews = document.querySelectorAll('.review-card');

    reviews.forEach(review => {
        const rating = review.getAttribute('data-rating');
        const project = review.getAttribute('data-project');
        const userName = review.getAttribute('data-user');

        let show = true;

        // Filtriraj po ocjeni
        if (ratingFilter && rating < ratingFilter) {
            show = false;
        }

        // Filtriraj po vrsti projekta
        if (projectFilter && project !== projectFilter) {
            show = false;
        }

        // Filtriraj po korisniku
        if (userSearch && !userName.includes(userSearch)) {
            show = false;
        }

        if (show) {
            review.style.display = 'block';
        } else {
            review.style.display = 'none';
        }
    });
}

// Funkcije za ocjenjivanje
function initializeRatingInputs() {
    const ratingInputs = document.querySelectorAll('input[name="rating"]');

    ratingInputs.forEach(input => {
        input.addEventListener('change', function () {
            updateRatingDisplay(this.value);
        });

        // Inicijalno postavi prikaz ako je već odabrano
        if (input.checked) {
            updateRatingDisplay(input.value);
        }
    });
}

function updateRatingDisplay(rating) {
    const labels = document.querySelectorAll('label[for^="rating"]');

    labels.forEach(label => {
        const stars = label.querySelector('.rating-stars');
        const labelRating = label.htmlFor.replace('rating', '');

        if (labelRating <= rating) {
            stars.classList.add('text-warning');
        } else {
            stars.classList.remove('text-warning');
        }
    });
}

// Funkcije za pretragu korisnika
function initializeUserSearch() {
    const userSearchInput = document.getElementById('user-search');

    if (userSearchInput) {
        let debounceTimer;

        userSearchInput.addEventListener('input', function () {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                searchUsers(this.value);
            }, 300);
        });
    }
}

function searchUsers(query) {
    if (query.length < 2) {
        clearSearchResults();
        return;
    }

    fetch(`/api/users/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(users => {
            displaySearchResults(users);
        })
        .catch(error => {
            console.error('Error searching users:', error);
        });
}

function displaySearchResults(users) {
    const resultsContainer = document.getElementById('search-results');
    if (!resultsContainer) return;

    resultsContainer.innerHTML = '';

    if (users.length === 0) {
        resultsContainer.innerHTML = '<div class="dropdown-item text-muted">Nema rezultata</div>';
        resultsContainer.classList.add('show');
        return;
    }

    users.forEach(user => {
        const userElement = document.createElement('a');
        userElement.className = 'dropdown-item';
        userElement.href = '#';
        userElement.innerHTML = `
            <div>
                <strong>${user.name}</strong>
                <div class="small text-muted">${user.email}</div>
                ${user.faculty ? `<div class="small text-muted">${user.faculty} - ${user.department || ''}</div>` : ''}
            </div>
        `;

        userElement.addEventListener('click', function (e) {
            e.preventDefault();
            selectUser(user);
        });

        resultsContainer.appendChild(userElement);
    });

    resultsContainer.classList.add('show');
}

function selectUser(user) {
    const emailInput = document.getElementById('reviewed_user_email');
    if (emailInput) {
        emailInput.value = user.email;
    }
    clearSearchResults();
}

function clearSearchResults() {
    const resultsContainer = document.getElementById('search-results');
    if (resultsContainer) {
        resultsContainer.innerHTML = '';
        resultsContainer.classList.remove('show');
    }
}

// Funkcije za validaciju obrazaca
function validateReviewForm() {
    const email = document.getElementById('reviewed_user_email').value;
    const rating = document.querySelector('input[name="rating"]:checked');
    const comment = document.getElementById('comment').value;

    if (!email) {
        showAlert('Molimo unesite email adresu kolege.', 'danger');
        return false;
    }

    if (!rating) {
        showAlert('Molimo odaberite ocjenu.', 'danger');
        return false;
    }

    if (!comment || comment.length < 10) {
        showAlert('Komentar mora imati najmanje 10 znakova.', 'danger');
        return false;
    }

    return true;
}

// Pomocne funkcije
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);

    // Automatski sakrij alert nakon 5 sekundi
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Export funkcija za globalni pristup (ako je potrebno)
window.RecenzijeApp = {
    filterReviews,
    searchUsers,
    validateReviewForm,
    showAlert
};