host=localhost
port=8888

#queryString="?indent&callback=try"
queryString="?indent"

#curl http://${host}:${port}/service/${queryString}
#curl http://${host}:${port}/service/echo1${queryString}
#curl http://${host}:${port}/service/echo1/${queryString}
curl http://${host}:${port}/service/echo1/a/1/c/3/e/5${queryString}
#curl http://${host}:${port}/service/echo/fd/er/eer/e/ee/reg/re/erg${queryString}
#curl http://${host}:${port}/service/cg/f/d/d/d/d/d${queryString}
