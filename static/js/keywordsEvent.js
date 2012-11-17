var keywordsEvent = function(ev) {
  if (_gaq) {
    _gaq.push(['_trackEvent'].concat(ev))
  }
  $.getJSON('/event/'+ev.join('/'), function(data) {
    if (!data.success && data.error && !data.redirect) {
      $('#messages').notify('create', 'messages-error', {
        title: 'Event error',
        text: data.error
      });
      return;
    }

    if (data.badges) $.each(data.badges, function() {
      $('#messages').notify('create', 'messages-badge', {
        name: this.name,
        icon: this.icon
      });
    });
  });
}
