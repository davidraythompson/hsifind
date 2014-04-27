host=localhost
port=8888

#queryString="?indent&callback=try"
queryString="?indent"

#curl -g --data "${inputString}" http://${host}:${port}/service/${queryString}
#curl -g --data "${inputString}" http://${host}:${port}/service/echo1${queryString}
#curl -g --data "${inputString}" http://${host}:${port}/service/echo1/${queryString}
#curl -g --data "${inputString}" http://${host}:${port}/service/echo1/a/b/c${queryString}

inputString='{"ordered": [0, 1, 2, 3, 4, 5], "keyed": {}}'
md5sum='acfed9f98eef67ae02b8832c7e712346'
curl -g --data "${inputString}" http://${host}:${port}/service/echo1/${md5sum}${queryString}
#curl -g --data "${inputString}" http://${host}:${port}/service/echo1/${md5sum}/

#inputString='{"ordered": [0, 1, 2, 3, 4, 5], "keyed": {}}1'
#md5sum='a9e27c28868228cb58acf005b0bb4a88'
#curl -g --data "${inputString}" http://${host}:${port}/service/echo1/${md5sum}
