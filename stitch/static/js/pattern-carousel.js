/* Lazy-load images in pattern card carousels.
 * Slides 2-4 use data-src instead of src to avoid loading all thumbnails upfront.
 * When a slide activates, its image src is set from data-src.
 */
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.pattern-carousel').forEach(function (carousel) {
        carousel.addEventListener('slide.bs.carousel', function (e) {
            var img = e.relatedTarget.querySelector('.carousel-lazy');
            if (img && img.dataset.src && !img.src) {
                img.src = img.dataset.src;
            }
        });
    });
});
