import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/page-header';
import { Send, MessageSquare } from 'lucide-react';

interface ChatMessage {
  id: string;
  sender_name: string;
  text: string;
  timestamp: string;
  type: string;
}

interface ChatRoom {
  room_id: string;
  participants: string[];
  message_count: number;
}

export function Chat() {
  const [rooms, setRooms] = useState<ChatRoom[]>([]);
  const [selectedRoom, setSelectedRoom] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch('/chat/rooms')
      .then(r => r.json())
      .then(data => {
        setRooms(data);
        if (data.length > 0 && !selectedRoom) {
          setSelectedRoom(data[0].room_id);
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedRoom) return;

    // Load existing messages
    fetch(`/chat/rooms/${selectedRoom}/messages`)
      .then(r => r.json())
      .then(data => setMessages(data))
      .catch(() => setMessages([]));

    // Connect WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/chat/${selectedRoom}?sender_name=You`);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        setMessages(prev => [...prev, msg]);
      } catch {
        // Ignore non-JSON messages
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [selectedRoom]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = () => {
    if (!newMessage.trim() || !wsRef.current) return;
    wsRef.current.send(JSON.stringify({ text: newMessage.trim(), sender_name: 'You' }));
    setNewMessage('');
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Chat"
        description="Real-time messaging rooms"
      />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 h-[calc(100vh-12rem)]">
        {/* Room List */}
        <Card className="md:col-span-1">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Rooms</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {rooms.length === 0 ? (
              <div className="p-4 text-sm text-muted-foreground text-center">
                No active rooms
              </div>
            ) : (
              rooms.map((room) => (
                <button
                  key={room.room_id}
                  onClick={() => setSelectedRoom(room.room_id)}
                  className={`w-full text-left px-4 py-3 border-b last:border-b-0 hover:bg-muted/50 transition-colors ${
                    selectedRoom === room.room_id ? 'bg-muted' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <MessageSquare className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">{room.room_id}</span>
                    </div>
                    <Badge variant="secondary" className="text-xs">
                      {room.message_count}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {room.participants.length} participants
                  </p>
                </button>
              ))
            )}
          </CardContent>
        </Card>

        {/* Chat Area */}
        <Card className="md:col-span-3 flex flex-col">
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <CardTitle className="text-sm">
              {selectedRoom ? `Room: ${selectedRoom}` : 'Select a room'}
            </CardTitle>
            {selectedRoom && (
              <Badge variant={isConnected ? 'default' : 'destructive'}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </Badge>
            )}
          </CardHeader>
          <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  No messages yet. Start the conversation!
                </div>
              ) : (
                messages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.sender_name === 'You' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[70%] rounded-lg px-3 py-2 ${
                      msg.sender_name === 'You'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}>
                      {msg.sender_name !== 'You' && (
                        <p className="text-xs font-medium mb-1">{msg.sender_name}</p>
                      )}
                      <p className="text-sm">{msg.text}</p>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            {selectedRoom && (
              <div className="border-t p-4 flex gap-2">
                <Input
                  placeholder="Type a message..."
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                  disabled={!isConnected}
                />
                <Button onClick={sendMessage} disabled={!isConnected || !newMessage.trim()}>
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
