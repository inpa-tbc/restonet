document.addEventListener('DOMContentLoaded', function() {
    console.log('Restaurant menu website loaded successfully');

    // Initialize AOS (Animate on Scroll)
    AOS.init({
        duration: 1000,
        once: true
    });

    // Dark Mode Toggle
    const darkModeToggle = document.querySelector('.dark-mode-toggle');
    const body = document.body;

    // Only initialize dark mode if the toggle exists
    if (darkModeToggle) {
        // Check for saved dark mode preference
        if (localStorage.getItem('darkMode') === 'enabled') {
            body.classList.add('dark-mode');
        }

        function toggleDarkMode() {
            body.classList.toggle('dark-mode');
            
            // Save preference
            if (body.classList.contains('dark-mode')) {
                localStorage.setItem('darkMode', 'enabled');
            } else {
                localStorage.removeItem('darkMode');
            }
        }

        // Attach event listener to dark mode toggle
        darkModeToggle.addEventListener('click', toggleDarkMode);
    }

    // Category Card Click Handler
    const viewCategoryButtons = document.querySelectorAll('.view-category-btn');
    const menuItemsModal = new bootstrap.Modal(document.getElementById('menuItemsModal'));
    const menuItemsModalBody = document.getElementById('menuItemsModalBody');

    viewCategoryButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const categoryId = this.closest('.category-card').getAttribute('data-category-id');
            fetchMenuItems(categoryId);
        });
    });

    function fetchMenuItems(categoryId) {
        fetch(`/get_menu_items/${categoryId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(menuItems => {
                displayMenuItems(menuItems);
                menuItemsModal.show();
            })
            .catch(error => {
                console.error('Error fetching menu items:', error);
                alert('حدث خطأ أثناء تحميل القائمة. يرجى المحاولة مرة أخرى.');
            });
    }

    function displayMenuItems(menuItems) {
        // Clear previous items
        menuItemsModalBody.innerHTML = '';

        // Create row for menu items
        const row = document.createElement('div');
        row.className = 'row g-4';

        // Populate menu items
        menuItems.forEach(item => {
            const col = document.createElement('div');
            col.className = 'col-md-4 col-sm-6';
            
            const card = document.createElement('div');
            card.className = 'card h-100 menu-item-card';
            
            const imagePath = item.image ? item.image : '/static/img/default-dish.png';
            
            card.innerHTML = `
                <img src="${imagePath}" class="card-img-top menu-item-image" alt="${item.name}">
                <div class="card-body">
                    <h5 class="card-title">${item.name}</h5>
                    <p class="card-text">${item.description || ''}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="price">${item.price} ريال</span>
                    </div>
                </div>
            `;

            col.appendChild(card);
            row.appendChild(col);
        });

        menuItemsModalBody.appendChild(row);
    }

    // Smooth Scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
});
