var keywordsKeydown = function(e) {
    if (!this.columns) {
        var cols = [
            {
                root: $('#keyword-side'),
                up: function() {
                    keywordsEvent(['nav', 'key', 'prev']);
                    $('#nav-prev').click();
                },
                down: function() {
                    keywordsEvent(['nav', 'key', 'next']);
                    $('#nav-next').click();
                }
            },
            [$('#info-news'),$('#info-bing'),$('#info-wiki')],
            [$('#info-blogs'),$('#info-twitter')]
        ];

        this.columns = [];
        for (c in cols) {
            if ($.isArray(cols[c])) {
                this.columns.push({
                    rows: cols[c],
                    row: 0,
                    up: function() {
                        if(this.row==0) this.rows[0].trigger('keyfocus');
                        else this.rows[--this.row].trigger('keyfocus');
                    },
                    down: function() {
                        if(this.row==this.rows.length-1) this.rows[this.row].trigger('keyfocus');
                        else this.rows[++this.row].trigger('keyfocus');
                    },
                    focus: function() {
                        this.row = 0;
                        this.rows[this.row].trigger('keyfocus');
                    },
                    custom: function(keycode) {
                        this.rows[this.row].trigger('keycustom', [keycode]);
                    }
                });
            } else if (cols[c].root) {
                var col = cols[c];
                col.focus = function() {
                    this.root.trigger('keyfocus');
                };
                this.columns.push(col);
            } else {
                this.columns.push(cols[c]);
            }
        }
    }

    if (!this.col) this.col = 0;

    var oldcol = this.col;
    var keycode = (e.keyCode ? e.keyCode : e.which);
    switch (keycode) {
        case 37: //left
            keywordsEvent(['keypress', 'left', null, this.col]);
            this.col = Math.max(0, this.col-1);
            if (this.col != oldcol)
                this.columns[this.col].focus();
            break;
        case 39: // right
            keywordsEvent(['keypress', 'right', null, this.col]);
            this.col = Math.min(this.columns.length-1, this.col+1);
            if (this.col != oldcol)
                this.columns[this.col].focus();
            break;
        case 38: // up
            keywordsEvent(['keypress', 'up', null, this.col]);
            this.columns[this.col].up();
            break;
        case 40: // down
            keywordsEvent(['keypress', 'down', null, this.col]);
            this.columns[this.col].down();
            break;

        default:
            if (typeof this.columns[this.col].custom == 'function') this.columns[this.col].custom(keycode);
            return true;
    }
    e.preventDefault();
    return false;
}
