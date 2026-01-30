import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import FeedbackModal from './FeedbackModal'
import SpriteDisplay from './SpriteDisplay'
import './ChatInterface.css'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface SessionInfo {
  id: string
  title: string
  created_at: number
  updated_at: number
  message_count: number
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [ws, setWs] = useState<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [currentResponse, setCurrentResponse] = useState('')
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false)
  const [selectedMessage, setSelectedMessage] = useState<{task: string, response: string} | null>(null)
  const [currentEmotion, setCurrentEmotion] = useState<string | null>(null)
  const [currentSpritePath, setCurrentSpritePath] = useState<string | null>('/img_src/Hitomi/neutral.png')

  const [sessions, setSessions] = useState<SessionInfo[]>([])
  const [isSessionLoading, setIsSessionLoading] = useState(false)
  const [sessionMenuOpenId, setSessionMenuOpenId] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false) // 移动端sidebar控制
  const [isMobile, setIsMobile] = useState(false) // 是否移动端

  // 检测移动端
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth <= 768
      setIsMobile(mobile)
      // 移动端默认隐藏sidebar，PC端默认显示
      setSidebarOpen(!mobile)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  useEffect(() => {
    const onDocClick = () => setSessionMenuOpenId(null)
    document.addEventListener('click', onDocClick)
    return () => document.removeEventListener('click', onDocClick)
  }, [])

  const loadSessionList = async () => {
    const resp = await axios.get('/api/session/list')
    const list = resp.data?.sessions || []
    setSessions(list)
    return list as SessionInfo[]
  }

  const loadSessionMessages = async (sid: string) => {
    const resp = await axios.get(`/api/session/${sid}/messages`)
    const msgs = resp.data?.messages || []
    const uiMsgs: Message[] = msgs.map((m: any) => ({
      role: m.role,
      content: m.content,
      timestamp: new Date((m.ts || Date.now() / 1000) * 1000),
    }))
    setMessages(uiMsgs)
  }

  const createNewSession = async () => {
    const resp = await axios.post('/api/session/new')
    const sid = resp.data.session_id as string
    setSessionId(sid)
    setMessages([])
    await loadSessionList()
    return sid
  }

  // 初始化：加载 session 列表，恢复最近一个 session（没有则创建）
  useEffect(() => {
    const init = async () => {
      try {
        setIsSessionLoading(true)
        const list = await loadSessionList()
        if (list.length > 0) {
          const sid = list[0].id
          setSessionId(sid)
          await loadSessionMessages(sid)
        } else {
          await createNewSession()
        }
      } catch (error: any) {
        console.error('创建会话失败:', error)
        const errorMessage = error?.response?.data?.detail || error?.message || '未知错误'
        alert(`无法连接到后端: ${errorMessage}\n请确保后端服务正在运行 (http://localhost:8000)`)
      } finally {
        setIsSessionLoading(false)
      }
    }
    init()
  }, [])

  // 滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, currentResponse])

  // 发送消息
  const sendMessage = async () => {
    if (!input.trim() || !sessionId) {
      console.log('无法发送: input=', input.trim(), 'sessionId=', sessionId)
      return
    }

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    const messageToSend = input
    setInput('')
    setIsLoading(true)
    setCurrentResponse('')

    try {
      // 先尝试使用REST API作为fallback
      console.log('尝试发送消息，sessionId:', sessionId)
      
      // 使用WebSocket流式接收
      // 开发环境直接连接后端，因为Vite的WebSocket代理可能有问题
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      // 开发环境：用当前页面的 hostname（即你电脑的局域网 IP/域名）连接后端 8000
      // 这样手机访问 http://<电脑IP>:3000 时，也会连到 ws://<电脑IP>:8000
      const wsHost = import.meta.env.DEV
        ? `${window.location.hostname}:8000`
        : window.location.host
      const wsUrl = `${wsProtocol}//${wsHost}/api/chat/stream`
      console.log('WebSocket URL:', wsUrl)
      
      const websocket = new WebSocket(wsUrl)
      
      websocket.onopen = () => {
        console.log('WebSocket连接已建立')
        websocket.send(JSON.stringify({
          message: messageToSend,
          session_id: sessionId
        }))
        console.log('消息已发送:', messageToSend)
      }

      let accumulatedResponse = ''
      
      websocket.onmessage = (event) => {
        console.log('收到WebSocket消息:', event.data)
        try {
          const data = JSON.parse(event.data)
          console.log('解析后的数据:', data)
          
          if (data.type === 'chunk') {
            accumulatedResponse += data.content
            setCurrentResponse(accumulatedResponse)
          } else if (data.type === 'done') {
            // 完成，添加到消息列表
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: accumulatedResponse,
              timestamp: new Date()
            }])
            setCurrentResponse('')
            setIsLoading(false)
            // 更新情绪和sprites
            if (data.emotion) {
              setCurrentEmotion(data.emotion)
            }
            if (data.sprite_path) {
              setCurrentSpritePath(data.sprite_path)
            }
            websocket.close()
            // 更新 session 列表（更新时间、message_count 等）
            loadSessionList()
          } else if (data.type === 'error') {
            console.error('WebSocket错误:', data.error)
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: `错误: ${data.error}`,
              timestamp: new Date()
            }])
            setCurrentResponse('')
            setIsLoading(false)
            websocket.close()
          } else if (data.type === 'start') {
            console.log('开始接收响应')
          }
        } catch (e) {
          console.error('解析消息失败:', e, event.data)
        }
      }

      websocket.onerror = (error) => {
        console.error('WebSocket连接错误:', error)
        setIsLoading(false)
        // 如果WebSocket失败，尝试使用REST API
        setTimeout(() => {
          fallbackToRestAPI(messageToSend, sessionId)
        }, 100)
      }

      websocket.onclose = (event) => {
        console.log('WebSocket连接关闭:', event.code, event.reason)
        if (event.code !== 1000 && isLoading) {
          // 非正常关闭且还在加载中，尝试REST API
          setIsLoading(false)
          setTimeout(() => {
            fallbackToRestAPI(messageToSend, sessionId)
          }, 100)
        }
      }
      
      // 设置超时，如果5秒内没有响应，使用REST API
      const timeout = setTimeout(() => {
        if (isLoading && websocket.readyState === WebSocket.OPEN) {
          console.log('WebSocket超时，切换到REST API')
          websocket.close()
          fallbackToRestAPI(messageToSend, sessionId)
        }
      }, 5000)
      
      // 清理超时
      websocket.addEventListener('message', () => {
        clearTimeout(timeout)
      })

      setWs(websocket)
    } catch (error) {
      console.error('发送消息失败:', error)
      // 尝试使用REST API作为fallback
      fallbackToRestAPI(messageToSend, sessionId)
    }
  }

  // REST API fallback
  const fallbackToRestAPI = async (message: string, sid: string | null) => {
    try {
      console.log('使用REST API发送消息')
      const response = await axios.post('/api/chat', {
        message: message,
        session_id: sid
      })
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date()
      }])
      if (response.data.session_id && response.data.session_id !== sessionId) {
        setSessionId(response.data.session_id)
      }
      // 更新情绪和sprites
      if (response.data.emotion) {
        setCurrentEmotion(response.data.emotion)
      }
      if (response.data.sprite_path) {
        setCurrentSpritePath(response.data.sprite_path)
      }
      setIsLoading(false)
    } catch (error: any) {
      console.error('REST API也失败:', error)
      const errorMessage = error?.response?.data?.detail || error?.message || '未知错误'
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `发送失败: ${errorMessage}`,
        timestamp: new Date()
      }])
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="chat-shell">
      <SpriteDisplay emotion={currentEmotion} spritePath={currentSpritePath} />
      {/* 移动端遮罩层 */}
      {isMobile && sidebarOpen && (
        <div 
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <aside className={`session-sidebar ${sidebarOpen ? 'open' : ''} ${isMobile ? 'mobile' : ''}`}>
        <div className="session-top">
          <button
            className="session-new-icon"
            onClick={async () => {
              await createNewSession()
              // 移动端创建新会话后自动关闭sidebar
              if (isMobile) {
                setSidebarOpen(false)
              }
            }}
            disabled={isSessionLoading}
            title="New chat"
          >
            <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M19 11h-6V5h-2v6H5v2h6v6h2v-6h6z"/>
            </svg>
          </button>
        </div>

        <div className="session-section-title">Chats</div>
        <div className="session-list">
          {sessions.map((s) => (
            <div
              key={s.id}
              className={`session-item ${sessionId === s.id ? 'active' : ''}`}
              onClick={async () => {
                if (isLoading) return
                setSessionId(s.id)
                await loadSessionMessages(s.id)
                // 移动端选择会话后自动关闭sidebar
                if (isMobile) {
                  setSidebarOpen(false)
                }
              }}
              title={s.title}
            >
              <div className="session-item-title">{s.title || '新对话'}</div>
              <button
                className="session-item-menu-btn"
                title="Menu"
                onClick={(e) => {
                  e.stopPropagation()
                  setSessionMenuOpenId((cur) => (cur === s.id ? null : s.id))
                }}
              >
                <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
                  <path fill="currentColor" d="M12 7a2 2 0 1 0-2-2 2 2 0 0 0 2 2Zm0 2a2 2 0 1 0 2 2 2 2 0 0 0-2-2Zm0 8a2 2 0 1 0 2 2 2 2 0 0 0-2-2Z"/>
                </svg>
              </button>

              {sessionMenuOpenId === s.id && (
                <div
                  className="session-item-menu"
                  onClick={(e) => e.stopPropagation()}
                >
                  <button
                    className="session-item-menu-item"
                    onClick={async () => {
                      const newTitle = prompt('Rename', s.title || '新对话')
                      if (!newTitle) return
                      await axios.put(`/api/session/${s.id}/rename`, { title: newTitle })
                      await loadSessionList()
                      setSessionMenuOpenId(null)
                    }}
                  >
                    Rename
                  </button>
                  <button
                    className="session-item-menu-item danger"
                    onClick={async () => {
                      if (!confirm('Delete this chat?')) return
                      await axios.delete(`/api/session/${s.id}`)
                      const list = await loadSessionList()
                      if (sessionId === s.id) {
                        if (list.length > 0) {
                          setSessionId(list[0].id)
                          await loadSessionMessages(list[0].id)
                        } else {
                          await createNewSession()
                        }
                      }
                      setSessionMenuOpenId(null)
                    }}
                  >
                    Delete
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </aside>

      <div className="chat-interface">
        {/* 移动端菜单按钮 */}
        {isMobile && (
          <button
            className="mobile-menu-btn"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            title="菜单"
          >
            <svg className="icon" width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>
            </svg>
          </button>
        )}
        <div className="chat-messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-content">
                {msg.role === 'assistant' ? (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.content}
                  </ReactMarkdown>
                ) : (
                  msg.content
                )}
              </div>
              <div className="message-footer">
                <div className="message-time">
                  {msg.timestamp.toLocaleTimeString()}
                </div>
                {msg.role === 'assistant' && (
                  <button
                    className="feedback-button"
                    onClick={() => {
                      const userMsg = messages[idx - 1]?.role === 'user' ? messages[idx - 1] : null
                      setSelectedMessage({
                        task: userMsg?.content || '未知任务',
                        response: msg.content
                      })
                      setFeedbackModalOpen(true)
                    }}
                    title="反馈本次回复并触发进化"
                  >
                    反馈&进化
                  </button>
                )}
              </div>
            </div>
          ))}
          {isLoading && currentResponse && (
            <div className="message assistant">
              <div className="message-content">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {currentResponse}
                </ReactMarkdown>
                <span className="cursor">|</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        <FeedbackModal
          isOpen={feedbackModalOpen}
          onClose={() => {
            setFeedbackModalOpen(false)
            setSelectedMessage(null)
          }}
          task={selectedMessage?.task || ''}
          response={selectedMessage?.response || ''}
          sessionId={sessionId}
          onFeedbackSubmitted={() => {
            loadSessionList()
          }}
        />
        
        <div className="chat-input-container">
          <textarea
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入消息... (Enter发送, Shift+Enter换行)"
            rows={3}
            disabled={isLoading}
          />
          <button
            className="send-button"
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
          >
            {isLoading ? '角色正在输入...' : '发送'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ChatInterface
