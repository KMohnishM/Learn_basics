# gRPC Streaming Cheat Sheet

## 1. Architecture & Syntax Comparison

| Mode | Flow | Client Syntax (Go) | Server Syntax (Go) | Primary Use Case |
|---|---|---|---|---|
| **Unary** | Request -> Response | `res, err := client.Do(ctx, req)` | `func Do(ctx, req) (res, err)` | Standard CRUD |
| **Server Stream** | Request -> [Res, Res...] | `stream, _ := client.Sub(ctx, req)`<br>`for { res, err := stream.Recv() }` | `func Sub(req, stream)`<br>`for { stream.Send(res) }` | Subscriptions, large datasets |
| **Client Stream** | [Req, Req...] -> Response | `stream, _ := client.Up(ctx)`<br>`for { stream.Send(req) }`<br>`res, err := stream.CloseAndRecv()` | `func Up(stream)`<br>`for { req, err := stream.Recv() }`<br>`return stream.SendAndClose(res)` | Big file uploads, Telemetry |
| **Bidirectional** | [Req, ...] <-> [Res, ...] | `stream, _ := client.Chat(ctx)`<br>`go read(); go write()` | `func Chat(stream)`<br>`go read(); go write()` | Real-time chat, gaming sync |

---

## 2. Python Streaming Templates

### Server Streaming (Yield)
```python
def GetData(self, request, context):
    for i in range(10):
        if not context.is_active():
            break
        yield pb.DataResponse(item=f"Data {i}")
```

### Client Streaming (Iterator)
```python
def UploadData(self, request_iterator, context):
    count = 0
    for chunk in request_iterator:
        count += len(chunk.data)
    return pb.UploadResponse(bytes_received=count)
```

### Bidirectional Streaming (Generators)
```python
def Chat(self, request_iterator, context):
    for incoming_msg in request_iterator:
        yield pb.ChatResponse(reply=f"Echo: {incoming_msg.text}")
```

---

## 3. Go Streaming Templates

### Bidirectional Server Implementation
```go
func (s *server) Chat(stream pb.ChatService_ChatServer) error {
    errs := make(chan error, 1)
    
    // Sender Goroutine
    go func() {
        for {
            err := stream.Send(&pb.Message{Text: "Ping"})
            if err != nil { errs <- err; return }
            time.Sleep(time.Second)
        }
    }()
    
    // Receiver Goroutine
    go func() {
        for {
            in, err := stream.Recv()
            if err == io.EOF { errs <- nil; return }
            if err != nil { errs <- err; return }
            log.Println(in.Text)
        }
    }()
    
    return <-errs
}
```

---

## 4. Stream Cancellation & Backpressure

### Cancellation (Context)
*   **Trigger:** Client calls `cancel()` on the Context.
*   **Network:** HTTP/2 `RST_STREAM` frame is transmitted.
*   **Go Server:** `ctx.Done()` channel is closed.
*   **Python Server:** `context.is_active()` returns `False`.

### Backpressure (Flow Control)
*   **Mechanism:** HTTP/2 `WINDOW_UPDATE` frames.
*   **Behavior:** If a client reads too slowly, the server's send window drops to 0.
*   **Result:** `stream.Send()` (Go) or `yield` (Python) will physically block until the client reads more data and expands the window. Prevents OOM crashes.

---
## ASCII Diagram: Bidirectional Stream
```text
+--------+       HTTP/2 Single TCP Connection        +--------+
|        | ----------------------------------------> |        |
| Client | <---------------------------------------- | Server |
|        |    [DATA: Stream 1] [DATA: Stream 2]      |        |
|        |    [WINDOW_UPDATE]  [HEADERS: Stream 3]   |        |
+--------+ ----------------------------------------> +--------+
```
