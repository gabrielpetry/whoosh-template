var app = new Vue({
  el: '#app',
  data: {
    // input: '#hello',
    fetched: [],
    termm: '',
    correct: false,
    limit: 10
  },
  methods: {
      liveSearch:  function (event) {
            fetch('/search?limit=' + app.limit + '&correct=' + app.correct + '&term=' + app.termm)
                .then(function(response) {
                return response.json();
            }).then(function(data) {
                app.fetched = [];
                app.fetched = data;
            });
      }
  },
})

Vue.config.devtools = true;
