APP_VERSION="5.23.4"
PACKAGE_VERSION="0.1"

# This regex parses websocket sends. It was pain to create :(
# ^(\d+) - Id of the message
# (?: ... ) - variants of the payload
## \[([^,]+)\] - list with single element: 43149[null]
## (\{.*\}) - JSON data: 40{"sid":"ZTBT5U5U9VbKPIHYASsQ"}
## \[[^,]+,[^,]+,[^,]+\] - array with three elements: 43150[null,"2024-12-09T22:34:24.329Z",[]]
## \[(?:\"([^,]+)\"|(null)),(?:(true)|(false)|(\{.+\})|(\[.+\])))\] - full variant with json, array or bool payload:
## 42["open-onetime-image",{"messageId":"35f0c221-c334-4669-babf-07c61bc0e054","dialogId":"67576856b7a77b4d7b7fa77e","viewedAt":"2024-12-09T22:00:23.480Z"}]
msg_regex = r"^(\d+)(?:(?:\[([^\n,]+)\])|(\{.*\})|(?:\[(?:\"([^\n,]+)\"|(null)),(?:(true|false)|(\{.+\})|(\[.+\])))\]|(\[[^,\n]+,[^,\n]+,[^\n,]+\]))$"
