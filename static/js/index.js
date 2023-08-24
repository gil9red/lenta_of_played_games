$(function() {
    // Загрузка остальных годов
    $(".card:has(.not-loaded)").each(function() {
        let $card = $(this);

        let $progress = $card.find(".progress");
        $progress.removeClass('hide');

        let $body = $card.find(".not-loaded");

        let $collapse = $card.find(".collapse.multi-collapse");
        let year = $card.find("[data-year]").data("year");

        $.get(
            '/year/' + year,
            function(data) {
                $body.html(data);
                $body.removeClass('not-loaded');

                // Установка обработчика копирования на игры
                set_copy_handler('.media-body.game', $body);

                // Применение поиска на только что подгруженные игры
                search(true, $collapse.attr('id'));

                $progress.addClass('hide');
            }
        );
    });

    $('#clear_search').click(function() {
        $('#search').val('');
        search();
    });

    let typingTimer = null;       // Timer identifier
    const doneTypingInterval = 300; // Time in ms

    $('#search').on('input', function() {
        clearTimeout(typingTimer);
        typingTimer = setTimeout(search, doneTypingInterval);
    });

    search(true);

    set_copy_handler('.media-body.game');
});

function search(init=false, search_from_id=null) {
    let search_text = $('#search').val().toLowerCase();
    let is_empty = search_text.length == 0;

    // Если функция вызвана при прогрузке страницы и текста в поиске нет,
    // то ничего не делаем -- по умолчанию все элементы и так видимые
    if (init && is_empty) {
        return;
    }

    // При очистке строки поиска, убираем класс у всех не найденных ранее элементов
    if (is_empty) {
        $('.not_found').removeClass('not_found');
    }

    let query = '.media.game';
    if (search_from_id != null) {
        query = `#${search_from_id} ${query}`;
    }

    console.log(`Call search "${search_text}", using "${query}"`);

    let day_by_games = new Map();

    $(query).each(function() {
        let game_el = $(this);
        let day_el = game_el.parent().parent()
        let day_value = day_el.find('.day').text();

        let text = day_value + game_el.text().replace(/\s\s+/g, ' ').trim().toLowerCase();
        let is_visible = text.includes(search_text);
        game_el.toggleClass('not_found', !is_visible);

        // Если хоть одна игра видима, то показываем блок ее карточки
        // Иначе, если уже был поиск и ее карточка была скрыта, то при проверке
        // видимости игры она не будет показана, т.к. ее карточка скрыта
        if (is_visible) {
            day_el.removeClass('not_found');
        }

        let day_el_dom = day_el[0];
        if (!day_by_games.has(day_el_dom)) {
            day_by_games.set(day_el_dom, []);
        }

        day_by_games.get(day_el_dom).push(game_el);
    });

    for (let [day_el_dom, games] of day_by_games) {
        let number_visibles = 0;
        for (let game_el of games) {
            if (!game_el.hasClass("not_found")) {
                number_visibles++;
            }
        }
        $(day_el_dom).toggleClass('not_found', number_visibles == 0);
    }

    $('.collapse[data-year]').each(function() {
        let collapse_el = $(this);
        let is_all_not_found = true;

        collapse_el.find('.card-body > .media').each(function() {
            let day_el = $(this);
            if (!day_el.hasClass('not_found')) {
                is_all_not_found = false;
                return false;
            }
        });

        collapse_el.find('.no_results').toggleClass('hide', !is_all_not_found);
    });
}

function set_copy_handler(css_selector, from_element=null) {
    if (from_element != null) {
        from_element = from_element.find(css_selector);
    } else {
        from_element = $(css_selector);
    }

    // Copy text by double click
    from_element.dblclick(function() {
        let text = $(this).find('.name').text();

        // SOURCE: https://stackoverflow.com/a/48948114/5909792
        $("<textarea/>")
            .appendTo("body")
            .val(text)
            .select()
            .each(() => document.execCommand('copy'))
            .remove();

        noty({
            text: 'Скопировано в буфер обмена',
            type: 'success',
            layout: 'bottomCenter',
            timeout: 2000,
        });
    });
}
