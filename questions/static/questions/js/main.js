$(document).ready(function() {
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    $(document).on('click', '.like-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const btn = $(this);
        const questionId = btn.data('question-id');
        const likesCountSpan = btn.find('.likes-count');
        
        if (!questionId) return;

        btn.prop('disabled', true);

        $.ajax({
            url: '/question/' + questionId + '/like/',
            type: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            success: function(response) {
                if (response.status === 'success') {
                    likesCountSpan.text(response.likes_count);
                    
                    if (response.action === 'liked') {
                        btn.addClass('active-like');
                    } else {
                        btn.removeClass('active-like');
                    }
                    btn.prop('disabled', false); 
                } else {
                    alert(response.message || 'Ошибка');
                    btn.prop('disabled', false);
                }
            },
            error: function(xhr) {
                if (xhr.status === 401 || xhr.status === 403) {
                    const currentUrl = window.location.pathname + window.location.search;
                    const loginUrl = '/login?next=' + encodeURIComponent(currentUrl);
                    window.location.href = loginUrl;
                } else {
                    btn.prop('disabled', false);
                }
            }
        });
        return false;
    });

    $(document).on('click', '.answer-like-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const btn = $(this);
        const answerId = btn.data('answer-id');
        const likesCountSpan = btn.find('.answer-likes-count');
        
        if (!answerId) return;
    
        btn.prop('disabled', true);
    
        $.ajax({
            url: '/answer/' + answerId + '/like/',
            type: 'POST',
            headers: { 'X-CSRFToken': csrftoken },
            success: function(response) {
                if (response.status === 'success') {
                    likesCountSpan.text(response.likes_count);
                    
                    if (response.action === 'liked') {
                        btn.addClass('active-like');
                    } else {
                        btn.removeClass('active-like');
                    }
                    btn.prop('disabled', false);
                } else {
                    btn.prop('disabled', false);
                }
            },
            error: function(xhr) {
                if (xhr.status === 401 || xhr.status === 403) {
                    const currentUrl = window.location.pathname + window.location.search;
                    const loginUrl = '/login?next=' + encodeURIComponent(currentUrl);
                    window.location.href = loginUrl;
                } else {
                    btn.prop('disabled', false);
                }
            }
        });
        return false;
    });

    $(document).on('click', '.mark-best-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const btn = $(this);
        const answerId = btn.data('answer-id');
        
        btn.prop('disabled', true);

        $.ajax({
            url: '/answer/' + answerId + '/mark-best/',
            type: 'POST',
            headers: { 'X-CSRFToken': csrftoken },
            success: function(response) {
                if (response.status === 'success') {
                    $('.mark-best-btn').each(function() {
                        const currentBtn = $(this);
                        const currentCard = currentBtn.closest('article.card');
                        currentBtn.removeClass('btn-success disabled').addClass('btn-outline-success');
                        currentBtn.text('Сделать правильным');
                        currentBtn.prop('disabled', false);
                        currentCard.removeClass('border-success border-2');
                        currentCard.find('.badge.bg-success').remove();
                    });


                    const selectedBtn = $(`.mark-best-btn[data-answer-id="${response.answer_id}"]`);
                    const selectedCard = selectedBtn.closest('article.card');
                    selectedBtn.removeClass('btn-outline-success').addClass('btn-success disabled');
                    selectedBtn.text('✓ Правильный');
                    selectedBtn.prop('disabled', true);
                    selectedCard.addClass('border-success border-2');

                    const headerContainer = selectedCard.find('.d-flex.justify-content-between.align-items-center.mb-2');
                    if (headerContainer.length > 0) {
                        headerContainer.append('<span class="badge bg-success">✓ Правильный ответ</span>');
                    }
                } else {
                    alert(response.message || 'Ошибка при выборе ответа');
                    btn.prop('disabled', false);
                }
            },
            error: function(xhr) {
                if (xhr.status === 403) {
                    alert('Только автор вопроса может выбрать лучший ответ!');
                } else {
                    alert('Произошла ошибка сервера');
                }
                btn.prop('disabled', false);
            }
        });
    });
});
