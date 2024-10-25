import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    print(f"Notification: {data['message']}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws):
    print("WebSocket connection closed")

def on_open(ws):
    print("WebSocket connection established")

if __name__ == "__main__":
    websocket_url = "ws://localhost:8000/ws/notifications/"
    ws = websocket.WebSocketApp(websocket_url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    ws.run_forever()
