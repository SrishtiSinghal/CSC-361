
# header size is 5 bytes
# 1st byte is method (GET | ACK | SYN | DATA | FIN) 
# 2nd byte is sequence number
# 3rd byte is acknoledgement number
# 4th and 5th bytes contain payload length

def parseMessage(bytes):
    header = parseHeader(bytes[:5])
    payloadLength = header[3]

    payload = bytes[5:5+payloadLength]

    return header, payload.decode()

def encodeMessage(method, seqNo, ackNo, body):
    payload = body.encode()
    payloadLength = len(payload)
    encodedHeader = (encodeHeader(method, seqNo, ackNo, payloadLength))
    return encodedHeader + payload

def byteToMethod(byte):
    return {
        0: "GET",
        1: "SYN",
        2: "ACK",
        3: "DATA",
        4: "FIN"
    }[byte]

def methodToByte(method):
    return {
        "GET": 0,
        "SYN": 1,
        "ACK": 2,
        "DATA": 3,
        "FIN": 4,
    }[method]

def parseHeader(headerBytes):
    payloadLength = headerBytes[3] * 256 + headerBytes[4]
    return [byteToMethod(headerBytes[0]), headerBytes[1], headerBytes[2], payloadLength]

def encodeHeader(method, sequenceNo, ackNo, payloadLength):
    return bytes([
            methodToByte(method),
            sequenceNo,
            ackNo,
            int(payloadLength / 256),
            payloadLength % 256,
    ])


if __name__ == "__main__":
    # test http_util in this block 
    print("------testing header---------")
    header = encodeHeader("GET", 12, 0, 973)
    print(header)
    print(parseHeader(header))

    print("------testing message-------")
    encodedMessage = encodeMessage("GET", 123, 0, "some random message repeated some random message repeated some random message repeated some random message repeated some random message repeated some random message repeated some random message repeated some random message repeated some random message repeated some random message repeated some random message repeated some random message repeated some random message repeated some random message repeated some random message repeated some random message repeated some random message repeated some random message repeated some random message repeated some random message repeated some random message repeated ")
    print(encodedMessage)
    print(parseMessage(encodedMessage))
    
    

