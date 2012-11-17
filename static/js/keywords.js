var Keywords = {
  config: {
    minLength: 3,
    maxResults: 5,
    debug: true
  },

  Fetcher: {
    bing: function(keyword) {
      var target = this;

//      var bing_url='http://api.search.live.net/json.aspx?JsonType=callback&JsonCallback=?&Appid='+Keywords.config.BING_KEY+'&query='+encodeURIComponent(keyword)+'&sources=web';
      var bing_url='/api/bing/'+encodeURIComponent(keyword);

      $.ajax({
        type: "GET",
        url: bing_url,
        dataType: "json", 
        success: function(resp) {
          target.data('loaded', keyword);

          var results = [];
          if (resp.SearchResponse.Web) {
            if (resp.SearchResponse.Web.Results) {
                $.each(resp.SearchResponse.Web.Results, function(i,data) {
                  results.push({
                    title: data.Title,
                    info: data.DisplayUrl + ', ' + data.DateTime,
                    text: data.Description,
                    link: data.Url
                  });
                });
                Keywords.out.results.apply(target, [results]);
            } else {
              Keywords.out.error.noResults.apply(target);
            }

          } else {
            Keywords.out.error.queryError.apply(target, [(resp.SearchResponse.Errors.length ? resp.SearchResponse.Errors[0].Message : 'null')]);
          }
        }
      });
    },

    news: function(keyword) {
      var target = this;

//      var bing_url='http://api.search.live.net/json.aspx?JsonType=callback&JsonCallback=?&Appid='+Keywords.config.BING_KEY+'&query='+encodeURIComponent(keyword)+'&sources=news';
      var bing_url='/api/news/'+encodeURIComponent(keyword);

      $.ajax({
        type: "GET",
        url: bing_url,
        dataType: "json", 
        success: function(resp) {
          target.data('loaded', keyword);

          var results = [];
          if (resp.SearchResponse.News) {
            $.each(resp.SearchResponse.News.Results, function(i,data) {
              results.push({
                title: data.Title,
                info: data.Source + ', ' + data.Date,
                text: data.Snippet,
                link: data.Url
              });
            });

            Keywords.out.results.apply(target, [results]);
          } else if (resp.SearchResponse.Errors) {
            Keywords.out.error.queryError.apply(target, [resp.SearchResponse.Errors]);
          } else {
            Keywords.out.error.noResults.apply(target);
          }
        }
      });
    },

    wiki: function(keyword) {
      var target = this;

//          var wiki_url='http://en.wikipedia.org/w/api.php?action=opensearch&search='+encodeURIComponent(keyword)+'&limit=10&namespace=0&format=xml';
      var wiki_url='api/wiki/'+encodeURIComponent(keyword);

      $.ajax({
        type: "GET",
        url: wiki_url,
        dataType: "xml",
        success: function(resp) {
          target.data('loaded', keyword);

          var results = [];
          if ($(resp).find('Section > Item').length) {
            $(resp).find('Section > Item').each(function(i,data) {
              var article = {
                title: $(this).children('text').text(),
                text: $(this).children('description').text(),
                link: $(this).children('url').text()
              };
              results.push(article);
            });

            Keywords.out.results.apply(target, [results]);
          } else {
            Keywords.out.error.noResults.apply(target);
          }
        }
      });
    },

    blogs: function(keyword) {
      var target = this;

      // var blogs_url='https://ajax.googleapis.com/ajax/services/search/blogs?v=1.0&q='+encodeURIComponent(keyword)+'&userip='+$('#userip').val();
      var blogs_url = '/api/blogs/'+encodeURIComponent(keyword);

      $.ajax({
        type: "GET",
        url: blogs_url,
        dataType: "json",
        success: function(resp) {
          target.data('loaded', keyword);

          var results = [];
          if (resp.responseData && resp.responseData.results) {
            $.each(resp.responseData.results, function(i,data) {
              var article = {
                title: data.title,
                info: "<a href=\"" + data.blogUrl + "\">" + data.author + "</a>, " + data.publishedDate,
                text: data.content,
                link: data.postUrl
              };
              results.push(article);
            });

            Keywords.out.results.apply(target, [results]);
          } else {
            Keywords.out.error.queryError.apply(target, [null]);
          }
        }
      });
    },

    twitter: function(keyword) {
      this.find('div.progress').remove();
      this.twitterSearch(keyword);
    }

  },

  out: {
    error: {
      unknownPlugin: function() {
        this.html('<div class="error">Unknown search plugin.</div>');
      },
      queryError: function(data) {
        if (Keywords.config.debug) console.log('queryError', data);
        this.html('<div class="error">Query error ('+data+')</div>');
      },
      tooShort: function() {
        this.html('<div class="error">Missing keyword.</div>');
      },
      noResults: function() {
        this.html('<div class="error">No relevant items were found.</div>');
      }
    },

    results: function(data) {
      var target = this;
      if (data.length) {
        target.html('');
        $.each(data, function(i, result) {
          if (i >= Keywords.config.maxResults) return;
          target.append(
              $('#tpl-result').html()
                .replace(/{title}/g, result.title)
                .replace(/{info}/g, result.info ? result.info : '')
                .replace(/{text}/g, result.text)
                .replace(/{link}/g, result.link)
          );
        });
      } else {
        Keywords.out.error.noResults.apply(target);
      }
    },

    progress: function() {
      this.html('<div class="progress"><img src="img/progress.gif"></div>');
    }
  },

  fetch: function(target, keyword) {
    if (target.data('plugin') in Keywords.Fetcher) {
      if (keyword.length >= Keywords.config.minLength) {
        Keywords.out.progress.apply(target);
        Keywords.Fetcher[target.data('plugin')].apply(target, [keyword]);
      } else {
        Keywords.out.error.tooShort.apply(target);
      }
    } else {
      Keywords.out.error.unknownPlugin.apply(target);
    }
  },

  day: function(target, day, ordering, callback) {
    $.getJSON('/trends/daily/'+day+'?o='+ordering, function(data) {
      if (!data.success) return;

      target.html('');
      if (data.keywords.length) {
          $.each(data.keywords, function(i, keyword) {
            target.append(
                $('#tpl-keyword').html()
                  .replace(/{hotKeyword}/g, keyword)
            );
          });
          target.find('li:first').click();   
      }

      if (typeof callback == 'function') callback.apply(target, [data]);
    });
  }
}

