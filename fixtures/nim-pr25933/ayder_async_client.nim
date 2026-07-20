import asyncdispatch, httpclient, json, os

proc main() {.async.} =
  let url = if paramCount() >= 1: paramStr(1) else: "http://127.0.0.1:1109/broker/query"
  let body = if paramCount() >= 2: paramStr(2) else: "{}"
  var client = newAsyncHttpClient()
  client.headers = newHttpHeaders({
    "Content-Type": "application/json",
    "Authorization": "Bearer dev"
  })
  let response = await client.query(url, body)
  let responseBody = await response.body
  let etag = if response.headers.hasKey("ETag"): $response.headers["ETag"] else: ""
  let acceptQuery = if response.headers.hasKey("Accept-Query"): $response.headers["Accept-Query"] else: ""
  echo $(%*{
    "status": response.status,
    "code": $response.code,
    "etag": etag,
    "accept_query": acceptQuery,
    "body_len": responseBody.len
  })

waitFor main()
