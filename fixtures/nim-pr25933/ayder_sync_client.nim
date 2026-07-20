import httpclient, json, os

let url = if paramCount() >= 1: paramStr(1) else: "http://127.0.0.1:1109/broker/query"
let body = if paramCount() >= 2: paramStr(2) else: "{}"

var client = newHttpClient()
client.headers = newHttpHeaders({
  "Content-Type": "application/json",
  "Authorization": "Bearer dev"
})
let response = client.query(url, body)
let responseBody = response.body
let etag = if response.headers.hasKey("ETag"): $response.headers["ETag"] else: ""
let acceptQuery = if response.headers.hasKey("Accept-Query"): $response.headers["Accept-Query"] else: ""

var conditionalStatus = ""
var conditionalCode = ""
var conditionalBodyLen = -1
var conditionalError = ""
if etag.len > 0:
  try:
    client.headers = newHttpHeaders({
      "Content-Type": "application/json",
      "Authorization": "Bearer dev",
      "If-None-Match": etag
    })
    let conditional = client.query(url, body)
    let conditionalBody = conditional.body
    conditionalStatus = conditional.status
    conditionalCode = $conditional.code
    conditionalBodyLen = conditionalBody.len
  except CatchableError as e:
    conditionalError = e.msg

echo $(%*{
  "status": response.status,
  "code": $response.code,
  "etag": etag,
  "accept_query": acceptQuery,
  "body_len": responseBody.len,
  "conditional_status": conditionalStatus,
  "conditional_code": conditionalCode,
  "conditional_body_len": conditionalBodyLen,
  "conditional_error": conditionalError
})
