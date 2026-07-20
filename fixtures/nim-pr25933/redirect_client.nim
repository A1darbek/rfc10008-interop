import httpclient, json, os

let base = if paramCount() >= 1: paramStr(1) else: "http://127.0.0.1:18133"
let body = """{"probe":"redirect"}"""

var results = newJArray()

for code in ["301", "302", "303", "307", "308"]:
  var client = newHttpClient(maxRedirects = 5)
  client.headers = newHttpHeaders({"Content-Type": "application/json"})
  let response = client.query(base & "/redirect/" & code, body)
  let responseBody = response.body
  var parsed = parseJson(responseBody)
  parsed["redirect_code"] = %code
  parsed["final_status"] = %response.status
  results.add(parsed)

echo $results
