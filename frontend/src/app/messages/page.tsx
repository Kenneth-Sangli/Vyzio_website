'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Header, Footer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuthStore } from '@/stores/auth-store';
import { messagesAPI, type Conversation, type Message } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import {
  Send,
  Search,
  MoreVertical,
  Phone,
  Video,
  Image,
  Paperclip,
  Smile,
  Check,
  CheckCheck,
  ArrowLeft,
} from 'lucide-react';

export default function MessagesPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/connexion?redirect=/messages');
      return;
    }
    fetchConversations();
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (selectedConversation) {
      fetchMessages(selectedConversation.id);
    }
  }, [selectedConversation]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchConversations = async () => {
    try {
      const response = await messagesAPI.getConversations();
      setConversations(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching conversations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchMessages = async (conversationId: string) => {
    try {
      // Utiliser getConversation qui retourne les messages via ConversationDetailSerializer
      const response = await messagesAPI.getConversation(conversationId);
      const conversationData = response.data as any;
      setMessages(conversationData.messages || []);
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedConversation) return;

    setIsSending(true);
    try {
      await messagesAPI.sendMessage(selectedConversation.id, newMessage);
      setNewMessage('');
      fetchMessages(selectedConversation.id);
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsSending(false);
    }
  };

  const getOtherUser = (conversation: Conversation) => {
    return conversation.buyer.id === user?.id ? conversation.seller : conversation.buyer;
  };

  const filteredConversations = conversations.filter((conv) => {
    const otherUser = getOtherUser(conv);
    const listingTitle = conv.listing_info?.title || '';
    return (
      otherUser.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      listingTitle.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  if (!user) return null;

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />

      <main className="flex-1">
        <div className="container mx-auto px-4 py-6">
          <div className="bg-white rounded-xl shadow-sm overflow-hidden h-[calc(100vh-200px)] flex">
            {/* Conversations List */}
            <div className={`w-full md:w-96 border-r flex flex-col ${selectedConversation ? 'hidden md:flex' : ''}`}>
              {/* Search */}
              <div className="p-4 border-b">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <Input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Rechercher une conversation..."
                    className="pl-10"
                  />
                </div>
              </div>

              {/* Conversations */}
              <div className="flex-1 overflow-y-auto">
                {isLoading ? (
                  <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                  </div>
                ) : filteredConversations.length === 0 ? (
                  <div className="text-center py-12 px-4">
                    <p className="text-gray-500">Aucune conversation</p>
                  </div>
                ) : (
                  filteredConversations.map((conversation) => {
                    const otherUser = getOtherUser(conversation);
                    return (
                      <button
                        key={conversation.id}
                        onClick={() => setSelectedConversation(conversation)}
                        className={`w-full flex items-start gap-3 p-4 hover:bg-gray-50 transition-colors text-left ${
                          selectedConversation?.id === conversation.id ? 'bg-primary-50' : ''
                        }`}
                      >
                        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary-600 to-purple-600 flex items-center justify-center text-white font-bold shrink-0">
                          {otherUser.avatar ? (
                            <img
                              src={otherUser.avatar}
                              alt={otherUser.username}
                              className="w-full h-full rounded-full object-cover"
                            />
                          ) : (
                            otherUser.username.charAt(0).toUpperCase()
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <h3 className="font-medium text-gray-900 truncate">
                              {otherUser.username}
                            </h3>
                            <span className="text-xs text-gray-500">
                              {conversation.last_message_date
                                ? formatDistanceToNow(
                                    new Date(conversation.last_message_date),
                                    { addSuffix: true, locale: fr }
                                  )
                                : ''}
                            </span>
                          </div>
                          {conversation.listing_info && (
                            <p className="text-sm text-gray-600 truncate">
                              {conversation.listing_info.title}
                            </p>
                          )}
                          {conversation.last_message && (
                            <p className="text-sm text-gray-500 truncate mt-1">
                              {conversation.last_message.content}
                            </p>
                          )}
                        </div>
                        {conversation.unread_count > 0 && (
                          <span className="w-5 h-5 bg-primary-600 text-white text-xs rounded-full flex items-center justify-center">
                            {conversation.unread_count}
                          </span>
                        )}
                      </button>
                    );
                  })
                )}
              </div>
            </div>

            {/* Messages */}
            <div className={`flex-1 flex flex-col ${!selectedConversation ? 'hidden md:flex' : ''}`}>
              {selectedConversation ? (
                <>
                  {/* Header */}
                  <div className="flex items-center gap-4 p-4 border-b">
                    <button
                      onClick={() => setSelectedConversation(null)}
                      className="md:hidden text-gray-600 hover:text-gray-900"
                    >
                      <ArrowLeft className="w-6 h-6" />
                    </button>
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-600 to-purple-600 flex items-center justify-center text-white font-bold">
                      {getOtherUser(selectedConversation).username.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">
                        {getOtherUser(selectedConversation).username}
                      </h3>
                      {selectedConversation.listing_info && (
                        <p className="text-sm text-gray-500">
                          {selectedConversation.listing_info.title}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-full">
                        <Phone className="w-5 h-5" />
                      </button>
                      <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-full">
                        <Video className="w-5 h-5" />
                      </button>
                      <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-full">
                        <MoreVertical className="w-5 h-5" />
                      </button>
                    </div>
                  </div>

                  {/* Messages List */}
                  <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.map((message) => {
                      const isOwn = message.sender.id === user.id;
                      return (
                        <div
                          key={message.id}
                          className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}
                        >
                          <div
                            className={`max-w-[70%] rounded-2xl px-4 py-2 ${
                              isOwn
                                ? 'bg-primary-600 text-white rounded-br-md'
                                : 'bg-gray-100 text-gray-900 rounded-bl-md'
                            }`}
                          >
                            <p>{message.content}</p>
                            <div className={`flex items-center justify-end gap-1 mt-1 ${
                              isOwn ? 'text-white/70' : 'text-gray-500'
                            }`}>
                              <span className="text-xs">
                                {new Date(message.created_at).toLocaleTimeString('fr-FR', {
                                  hour: '2-digit',
                                  minute: '2-digit',
                                })}
                              </span>
                              {isOwn && (
                                message.is_read ? (
                                  <CheckCheck className="w-4 h-4" />
                                ) : (
                                  <Check className="w-4 h-4" />
                                )
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                    <div ref={messagesEndRef} />
                  </div>

                  {/* Input */}
                  <form onSubmit={handleSendMessage} className="p-4 border-t">
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        className="p-2 text-gray-600 hover:bg-gray-100 rounded-full"
                      >
                        <Paperclip className="w-5 h-5" />
                      </button>
                      <button
                        type="button"
                        className="p-2 text-gray-600 hover:bg-gray-100 rounded-full"
                      >
                        <Image className="w-5 h-5" />
                      </button>
                      <Input
                        value={newMessage}
                        onChange={(e) => setNewMessage(e.target.value)}
                        placeholder="Écrivez votre message..."
                        className="flex-1"
                      />
                      <button
                        type="button"
                        className="p-2 text-gray-600 hover:bg-gray-100 rounded-full"
                      >
                        <Smile className="w-5 h-5" />
                      </button>
                      <Button
                        type="submit"
                        variant="gradient"
                        size="icon"
                        disabled={!newMessage.trim() || isSending}
                      >
                        <Send className="w-5 h-5" />
                      </Button>
                    </div>
                  </form>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center">
                  <div className="text-center">
                    <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Send className="w-12 h-12 text-gray-400" />
                    </div>
                    <h3 className="text-xl font-medium text-gray-900 mb-2">
                      Vos messages
                    </h3>
                    <p className="text-gray-500">
                      Sélectionnez une conversation pour commencer
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
