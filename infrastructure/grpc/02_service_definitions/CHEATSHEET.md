# gRPC Service Implementation Cheatsheet

## gRPC Status to HTTP Status Mapping

| gRPC Status Code | ID | HTTP Status | Description / When to use |
|------------------|----|-------------|---------------------------|
| `OK` | 0 | 200 OK | Success |
| `CANCELLED` | 1 | 499 Client Closed | Client cancelled the request. |
| `UNKNOWN` | 2 | 500 Internal | Unknown server error. |
| `INVALID_ARGUMENT` | 3 | 400 Bad Request | Client specified an invalid parameter. |
| `DEADLINE_EXCEEDED`| 4 | 504 Gateway Timeout| Request took longer than timeout. |
| `NOT_FOUND` | 5 | 404 Not Found | Requested resource does not exist. |
| `ALREADY_EXISTS` | 6 | 409 Conflict | Resource already exists. |
| `PERMISSION_DENIED`| 7 | 403 Forbidden | Client lacks necessary roles. |
| `RESOURCE_EXHAUSTED`| 8 | 429 Too Many Req | Rate limit or quota exceeded. |
| `FAILED_PRECONDITION`|9 | 400 Bad Request | System state prevents execution. |
| `ABORTED` | 10 | 409 Conflict | Concurrency conflict (e.g. CAS fail). |
| `OUT_OF_RANGE` | 11 | 400 Bad Request | Value out of valid range. |
| `UNIMPLEMENTED` | 12 | 501 Not Implemented| Server doesn't support this RPC. |
| `INTERNAL` | 13 | 500 Internal Server| Core invariants broken/DB down. |
| `UNAVAILABLE` | 14 | 503 Service Unavail| Service down or restarting. |
| `DATA_LOSS` | 15 | 500 Internal Server| Unrecoverable data corruption. |
| `UNAUTHENTICATED` | 16 | 401 Unauthorized | Missing or invalid auth token. |

---

## Python gRPC Templates

### Python Server Template
```python
import grpc
from concurrent import futures
import service_pb2, service_pb2_grpc

class MyServiceServicer(service_pb2_grpc.MyServiceServicer):
    def MyRPC(self, request, context):
        if not request.id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Missing ID")
        return service_pb2.MyResponse(status="SUCCESS")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_MyServiceServicer_to_server(MyServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()
```

### Python Client Template
```python
import grpc
import service_pb2, service_pb2_grpc

with grpc.insecure_channel('localhost:50051') as channel:
    stub = service_pb2_grpc.MyServiceStub(channel)
    try:
        req = service_pb2.MyRequest(id="123")
        res = stub.MyRPC(req, timeout=3.0)
        print(res)
    except grpc.RpcError as e:
        print(f"Failed: {e.code()} - {e.details()}")
```

---

## Go gRPC Templates

### Go Server Template
```go
package main

import (
	"context"
	"net"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	pb "path/to/generated"
)

type server struct { pb.UnimplementedMyServiceServer }

func (s *server) MyRPC(ctx context.Context, req *pb.MyRequest) (*pb.MyResponse, error) {
	if req.Id == "" {
		return nil, status.Error(codes.InvalidArgument, "Missing ID")
	}
	return &pb.MyResponse{Status: "SUCCESS"}, nil
}

func main() {
	lis, _ := net.Listen("tcp", ":50051")
	s := grpc.NewServer()
	pb.RegisterMyServiceServer(s, &server{})
	s.Serve(lis)
}
```

### Go Client Template
```go
package main

import (
	"context"
	"time"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	pb "path/to/generated"
)

func main() {
	conn, _ := grpc.DialContext(context.Background(), "localhost:50051",
        grpc.WithTransportCredentials(insecure.NewCredentials()), grpc.WithBlock())
	defer conn.Close()

	c := pb.NewMyServiceClient(conn)
	ctx, cancel := context.WithTimeout(context.Background(), time.Second*3)
	defer cancel()

	res, err := c.MyRPC(ctx, &pb.MyRequest{Id: "123"})
	if err != nil {
		panic(err)
	}
	println(res.Status)
}
```

---

## Metadata & Rich Errors Code Snippets

### Python: Read Header, Send Trailer
```python
# Server-side
def MyRPC(self, request, context):
    auth_token = dict(context.invocation_metadata()).get('authorization')
    context.set_trailing_metadata((('rate-limit', '99'),))
    return service_pb2.MyResponse()
```

### Go: Rich Error Generation
```go
import (
	"google.golang.org/grpc/status"
	"google.golang.org/grpc/codes"
	"google.golang.org/genproto/googleapis/rpc/errdetails"
)

// Server-side
st := status.New(codes.InvalidArgument, "Invalid input")
v := &errdetails.BadRequest_FieldViolation{
	Field: "id", Description: "Cannot be empty",
}
br := &errdetails.BadRequest{FieldViolations: []*errdetails.BadRequest_FieldViolation{v}}
st, _ = st.WithDetails(br)
return nil, st.Err()
```