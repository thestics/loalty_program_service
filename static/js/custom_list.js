function getListCount(el) {
    $.ajax({
        url: "ajax/count/" + window.location.search,
        beforeSend: function() {
            el.text = 'Loading...';
        },
        timeout: 30 * 1000
    })
    .done(function( data ) {
        el.text = 'Refresh ( ' + data + ' )';
    })
    .fail(function() {
        el.text = 'Refresh ( ERROR )';
    });
}
