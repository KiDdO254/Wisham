// Custom JavaScript for Django Unfold admin

document.addEventListener('DOMContentLoaded', function() {
    // Add custom functionality for better UX
    
    // Auto-focus first form field
    const firstInput = document.querySelector('.form-row input:not([type="hidden"]), .form-row select, .form-row textarea');
    if (firstInput) {
        firstInput.focus();
    }
    
    // Add confirmation for delete actions
    const deleteLinks = document.querySelectorAll('.deletelink');
    deleteLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });
    
    // Enhance form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let hasErrors = false;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.style.borderColor = '#ef4444';
                    hasErrors = true;
                } else {
                    field.style.borderColor = '#d1d5db';
                }
            });
            
            if (hasErrors) {
                e.preventDefault();
                alert('Please fill in all required fields.');
            }
        });
    });
    
    // Add smooth transitions
    const elements = document.querySelectorAll('input, select, textarea, button');
    elements.forEach(element => {
        element.style.transition = 'all 0.2s ease-in-out';
    });
});