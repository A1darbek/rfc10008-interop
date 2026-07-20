import asynchttpserver, asyncdispatch, httpcore, json, strutils

const PortNumber = 18133

proc headerValue(headers: HttpHeaders, key: string): string =
  if headers.hasKey(key):
    result = headers[key]
  else:
    result = ""

proc jsonResponse(request: Request): string =
  let contentType = request.headers.headerValue("Content-Type")
  let contentLength = request.headers.headerValue("Content-Length")
  result = $(%*{
    "method": $request.reqMethod,
    "path": request.url.path,
    "body": request.body,
    "content_type": contentType,
    "content_length": contentLength
  })

proc statusFor(path: string): HttpCode =
  case path
  of "/redirect/301": Http301
  of "/redirect/302": Http302
  of "/redirect/303": Http303
  of "/redirect/307": Http307
  of "/redirect/308": Http308
  else: Http404

proc handler(request: Request) {.async.} =
  case request.url.path
  of "/query", "/echo":
    let headers = newHttpHeaders({"Content-Type": "application/json"})
    await request.respond(Http200, request.jsonResponse(), headers)
  of "/redirect/301", "/redirect/302", "/redirect/303", "/redirect/307", "/redirect/308":
    let headers = newHttpHeaders({"Location": "/echo"})
    await request.respond(statusFor(request.url.path), "", headers)
  else:
    await request.respond(Http404, "not found")

let server = newAsyncHttpServer()
echo "nim QUERY server listening on 127.0.0.1:" & $PortNumber
waitFor server.serve(Port(PortNumber), handler, address = "127.0.0.1")
