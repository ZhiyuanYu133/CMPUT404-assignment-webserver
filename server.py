#  coding: utf-8
from curses.ascii import CR
from genericpath import exists
import os
import socketserver

# Copyright 2013 Abram Hindle, Eddie Antonio Santos
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/

# Reference
# https://www.w3.org/Protocols/rfc2616/rfc2616-sec5.html
# ============================================================
# Request
# ============================================================
# A request message from a client to a server includes, within
# the first line of that message, the method to be applied to
# the resource, the identifier of the resource, and the protocol
# version in use.
#
# Request = Request-Line    ; Section 5.1
#           *(( general-header
#            |  request-header
#            |  entity-header ) CRLF)
#           CRLF
#           [ message-body ]


CRLF = "\r\n"
SP = " "
COLON = ":"
HTTP_VERSION = "HTTP/1.1"
UTF_8 = "utf-8"


class MyWebServer(socketserver.BaseRequestHandler):

    def handle(self):
        self.headers = {}
        self.data = self.request.recv(1024).strip().decode(UTF_8)
        self.parse()
        self.write_response()

    def write_response(self):
        """
        Write response back to the client.
        """
        if self.method.upper() != "GET":
            self.request.sendall(bytearray(HTTP_VERSION + SP + "405" + SP + "Method Not Allowed" + CRLF + CRLF, UTF_8))
            return

        filepath = os.path.join(os.getcwd(), "www") + self.request_uri

        # 404 error
        if not os.path.exists(filepath):
            self.request.sendall(bytearray(HTTP_VERSION + SP + "404" + SP + "Not Found" + CRLF + CRLF, UTF_8))
            return

        status_line = HTTP_VERSION + SP + "200" + SP + "OK" + CRLF

        # check if it's a directory
        if os.path.isdir(filepath):
            if self.request_uri == "/deep":
                self.request.sendall(bytearray(HTTP_VERSION + SP + "301 Moved Permanently" +
                                     CRLF + "Location: /deep/" + CRLF + CRLF, UTF_8))
                return

            self.request.sendall(bytearray(status_line + CRLF, UTF_8))
            return

        # read the file
        fp = open(filepath, mode="r")
        content = fp.read()
        fp.close()

        headers = ["Content-Type: " + self.get_mime_type(), "Content-Length: " + str(len(content))]
        self.request.sendall(bytearray(status_line + CRLF.join(headers) + CRLF + CRLF + content, UTF_8))

    def get_mime_type(self):
        """
        Get mime type from the request uri.
        """
        if self.request_uri.endswith("htm") or self.request_uri.endswith("html"):
            return "text/html"

        if self.request_uri.endswith("css"):
            return "text/css"

        return "text/plain"

    def parse(self):
        """
        Parse HTTP request.
        """
        lines = self.data.split(CRLF)
        self.parse_request_line(lines[0])

        for line in lines[1:]:
            if line == CRLF:
                break

            self.parse_header(line)

    def parse_request_line(self, request_line):
        """
        Parse the request line. The Request-Line begins with a method token,
        followed by the Request-URI and the protocol version, and ending with
        CRLF. The elements are separated by SP characters.

        @param request_line: `Method SP Request-URI SP HTTP-Version CRLF`
        """
        self.method, self.request_uri, self.http_version = request_line.split(SP)

        # set relative path to absolute path if exists
        if "/.." in self.request_uri:
            self.request_uri = os.path.abspath(self.request_uri)

        if self.request_uri[-1] == "/":
            self.request_uri += "index.html"

    def parse_header(self, line):
        """
        Parse the header field.

        There are a few header fields which have general applicability for
        both request and response messages, but which do not apply to the
        entity being transferred.

        general-header = Cache-Control
                       | Connection
                       | Date
                       | Pragma
                       | Trailer
                       | Transfer-Encoding
                       | Upgrade
                       | Via
                       | Warning

        The request-header fields allow the client to pass additional
        information about the request, and about the client itself, to
        the server.

        request-header = Accept
                       | Accept-Charset
                       | Accept-Encoding
                       | Accept-Language
                       | Authorization
                       | Expect
                       | From
                       | Host
                       | If-Match

                       | If-Modified-Since
                       | If-None-Match
                       | If-Range
                       | If-Unmodified-Since
                       | Max-Forwards
                       | Proxy-Authorization
                       | Range
                       | Referer
                       | TE
                       | User-Agent

        Entity-header fields define metainformation about the entity-body or,
        if no body is present, about the resource identified by the request.

        entity-header = Allow
                      | Content-Encoding
                      | Content-Language
                      | Content-Length
                      | Content-Location
                      | Content-MD5
                      | Content-Range
                      | Content-Type
                      | Expires
                      | Last-Modified
                      | extension-header

        @param line: colon separated key value pair
        """
        index = line.find(COLON)
        if index == -1:
            return

        key = line[:index].strip()
        value = line[index + 1:].strip()
        self.headers[key] = value


if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer(
        (HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
