import React from 'react'
import ChatInterface from './components/ChatInterface'
import './App.css'

// 角色配置 - 统一管理角色名字
const CHARACTER_NAME = 'Hitomi'
const APP_TITLE = 'Hitomi-EvoAgent'

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>{APP_TITLE}</h1>
        <span className="slogan">你的反馈让{CHARACTER_NAME}不断进化，变得更好</span>
      </header>
      <main className="app-main">
        <ChatInterface />
      </main>
    </div>
  )
}

export default App
